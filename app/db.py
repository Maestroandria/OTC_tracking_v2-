import os
import sqlite3
from datetime import datetime, timezone

from flask import current_app, g

_DATABASE_URL = os.getenv("DATABASE_URL")
_USE_PG = bool(_DATABASE_URL)

if _USE_PG:
    import psycopg2
    import psycopg2.extras


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _q(sql: str) -> str:
    """Convertit les placeholders ? en %s pour PostgreSQL."""
    return sql.replace("?", "%s") if _USE_PG else sql


def get_db():
    if "db" not in g:
        if _USE_PG:
            g.db = psycopg2.connect(
                _DATABASE_URL,
                cursor_factory=psycopg2.extras.RealDictCursor,
            )
        else:
            g.db = sqlite3.connect(current_app.config["DATABASE"])
            g.db.row_factory = sqlite3.Row
            g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exception=None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def _write(query: str, params: tuple = ()) -> None:
    """Exécute une requête d'écriture et commit."""
    db = get_db()
    if _USE_PG:
        cur = db.cursor()
        cur.execute(_q(query), params)
        cur.close()
        db.commit()
    else:
        db.execute(query, params)
        db.commit()


def query_one(query: str, params: tuple = ()):
    db = get_db()
    if _USE_PG:
        cur = db.cursor()
        cur.execute(_q(query), params)
        row = cur.fetchone()
        cur.close()
        return row
    return db.execute(query, params).fetchone()


def query_all(query: str, params: tuple = ()):
    db = get_db()
    if _USE_PG:
        cur = db.cursor()
        cur.execute(_q(query), params)
        rows = cur.fetchall()
        cur.close()
        return rows
    return db.execute(query, params).fetchall()


def _run_ddl(db, statements: list) -> None:
    """Exécute une liste d'instructions DDL."""
    if _USE_PG:
        cur = db.cursor()
        for stmt in statements:
            if stmt.strip():
                cur.execute(stmt)
        cur.close()
        db.commit()
    else:
        for stmt in statements:
            if stmt.strip():
                db.execute(stmt)
        db.commit()


def init_db() -> None:
    db = get_db()
    _drop_obsolete_tables(db)

    _pk = "SERIAL PRIMARY KEY" if _USE_PG else "INTEGER PRIMARY KEY"
    _ts = "TIMESTAMPTZ NOT NULL DEFAULT NOW()" if _USE_PG else "TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP"

    ddl = [
        f"""CREATE TABLE IF NOT EXISTS users (
            id {_pk},
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            nom TEXT NOT NULL,
            prenom TEXT NOT NULL,
            fonction TEXT NOT NULL,
            date_inscription TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin'))
        )""",
        f"""CREATE TABLE IF NOT EXISTS client (
            id {_pk},
            code_client TEXT NOT NULL UNIQUE,
            raison_sociale TEXT NOT NULL,
            adresse TEXT NOT NULL,
            nif TEXT NOT NULL,
            stat TEXT NOT NULL,
            rib TEXT NOT NULL,
            user_email TEXT,
            created_at {_ts},
            FOREIGN KEY (user_email) REFERENCES users(email) ON UPDATE CASCADE ON DELETE SET NULL
        )""",
        f"""CREATE TABLE IF NOT EXISTS colis (
            id {_pk},
            tracking_number TEXT NOT NULL UNIQUE,
            date TEXT,
            client TEXT,
            poids REAL,
            colis INTEGER,
            envoi TEXT,
            frais REAL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            delivered_at TEXT,
            status_current_code TEXT,
            status_current_label TEXT
        )""",
        f"""CREATE TABLE IF NOT EXISTS historique (
            id {_pk},
            colis_id INTEGER NOT NULL,
            code TEXT NOT NULL,
            label TEXT NOT NULL,
            location TEXT,
            details TEXT,
            event_time TEXT NOT NULL,
            created_at TEXT NOT NULL,
            user_email TEXT,
            FOREIGN KEY (colis_id) REFERENCES colis(id) ON DELETE CASCADE,
            FOREIGN KEY (user_email) REFERENCES users(email) ON UPDATE CASCADE ON DELETE SET NULL
        )""",
        f"""CREATE TABLE IF NOT EXISTS facture (
            id {_pk},
            num_facture TEXT UNIQUE NOT NULL,
            date_facture TEXT,
            code_client TEXT,
            reference TEXT,
            type_facture TEXT,
            mode_reglement TEXT,
            total REAL,
            devise TEXT,
            commentaire TEXT,
            created_at {_ts},
            FOREIGN KEY (code_client) REFERENCES client(code_client) ON UPDATE CASCADE ON DELETE SET NULL
        )""",
        f"""CREATE TABLE IF NOT EXISTS ligne_facture (
            id {_pk},
            num_facture TEXT NOT NULL,
            code_article TEXT,
            designation TEXT,
            prix_unitaire REAL,
            quantite REAL,
            montant REAL,
            devise TEXT,
            FOREIGN KEY (num_facture) REFERENCES facture(num_facture) ON UPDATE CASCADE ON DELETE CASCADE
        )""",
        f"""CREATE TABLE IF NOT EXISTS facture_colis (
            id {_pk},
            num_facture TEXT NOT NULL,
            colis_id INTEGER NOT NULL,
            created_at {_ts},
            UNIQUE (num_facture, colis_id),
            FOREIGN KEY (num_facture) REFERENCES facture(num_facture) ON UPDATE CASCADE ON DELETE CASCADE,
            FOREIGN KEY (colis_id) REFERENCES colis(id) ON UPDATE CASCADE ON DELETE CASCADE
        )""",
        "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
        "CREATE INDEX IF NOT EXISTS idx_client_code ON client(code_client)",
        "CREATE INDEX IF NOT EXISTS idx_colis_tracking ON colis(tracking_number)",
        "CREATE INDEX IF NOT EXISTS idx_historique_colis_time ON historique(colis_id, event_time DESC)",
        "CREATE INDEX IF NOT EXISTS idx_facture_num ON facture(num_facture)",
        "CREATE INDEX IF NOT EXISTS idx_ligne_facture_num ON ligne_facture(num_facture)",
        "CREATE INDEX IF NOT EXISTS idx_facture_colis_num ON facture_colis(num_facture)",
    ]

    _run_ddl(db, ddl)
    _ensure_colis_columns(db)


def _drop_obsolete_tables(db) -> None:
    obsolete = ["shipment_events", "shipments", "tracking", "article"]
    if _USE_PG:
        cur = db.cursor()
        for t in obsolete:
            cur.execute(f"DROP TABLE IF EXISTS {t} CASCADE")
        cur.close()
        db.commit()
    else:
        for t in obsolete:
            db.execute(f"DROP TABLE IF EXISTS {t}")


def _ensure_colis_columns(db) -> None:
    required = {
        "date": "TEXT",
        "client": "TEXT",
        "poids": "REAL",
        "colis": "INTEGER",
        "envoi": "TEXT",
        "frais": "REAL",
    }
    if _USE_PG:
        cur = db.cursor()
        cur.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'colis' AND table_schema = 'public'"
        )
        existing = {row["column_name"] for row in cur.fetchall()}
        for col, typ in required.items():
            if col not in existing:
                cur.execute(f"ALTER TABLE colis ADD COLUMN {col} {typ}")
        cur.close()
        db.commit()
    else:
        existing = {
            row["name"]
            for row in db.execute("PRAGMA table_info(colis)").fetchall()
        }
        for col, typ in required.items():
            if col not in existing:
                db.execute(f"ALTER TABLE colis ADD COLUMN {col} {typ}")
        db.commit()


def init_app(app) -> None:
    @app.cli.command("init-db")
    def init_db_command():
        init_db()
        print("Base initialisée")


def create_shipment(payload: dict):
    ts = now_iso()
    _write(
        """
        INSERT INTO colis (
            tracking_number, date, client, poids, colis, envoi, frais,
            created_at, updated_at, status_current_code, status_current_label
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            payload["tracking_number"],
            payload.get("date"),
            payload.get("client"),
            payload.get("poids"),
            payload.get("colis"),
            payload.get("envoi"),
            payload.get("frais"),
            ts,
            ts,
            payload.get("status_current_code", "CREATED"),
            payload.get("status_current_label", "Créé"),
        ),
    )
    return get_shipment_by_tracking(payload["tracking_number"])


def get_shipment_by_tracking(tracking_number: str):
    normalized_tracking = tracking_number
    if isinstance(normalized_tracking, float) and normalized_tracking.is_integer():
        normalized_tracking = str(int(normalized_tracking))
    else:
        normalized_tracking = str(normalized_tracking).strip()

    return query_one(
        "SELECT * FROM colis WHERE tracking_number = ?",
        (normalized_tracking,),
    )


def _build_shipments_filter_clause(filters: dict | None = None) -> tuple[str, tuple]:
    filters = filters or {}
    clauses: list[str] = []
    params: list = []

    tracking_search = (filters.get("q") or "").strip()
    client_search = (filters.get("client") or "").strip()
    status_filter = (filters.get("status") or "").strip()
    envoi_filter = (filters.get("envoi") or "").strip()

    if tracking_search:
        clauses.append("tracking_number LIKE ?")
        params.append(f"%{tracking_search}%")

    if client_search:
        clauses.append("LOWER(COALESCE(client, '')) LIKE LOWER(?)")
        params.append(f"%{client_search}%")

    if status_filter:
        clauses.append("status_current_label = ?")
        params.append(status_filter)

    if envoi_filter:
        clauses.append("envoi = ?")
        params.append(envoi_filter)

    where_clause = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    return where_clause, tuple(params)


def count_shipments(filters: dict | None = None) -> int:
    where_clause, params = _build_shipments_filter_clause(filters)
    row = query_one(f"SELECT COUNT(*) AS total FROM colis{where_clause}", params)

    if not row:
        return 0

    return int(row["total"] if isinstance(row, dict) else row[0])


def list_shipments(filters: dict | None = None, limit: int = 25, offset: int = 0):
    where_clause, params = _build_shipments_filter_clause(filters)
    return query_all(
        f"""
        SELECT * FROM colis
        {where_clause}
        ORDER BY updated_at DESC
        LIMIT ?
        OFFSET ?
        """,
        (*params, limit, offset),
    )


def export_shipments(filters: dict | None = None):
    where_clause, params = _build_shipments_filter_clause(filters)
    return query_all(
        f"""
        SELECT date, tracking_number, client, status_current_label, poids, colis, envoi, frais, created_at, updated_at
        FROM colis
        {where_clause}
        ORDER BY updated_at DESC
        """,
        params,
    )


def create_event(shipment_id: int, payload: dict):
    ts = now_iso()
    _write(
        """
        INSERT INTO historique (colis_id, code, label, location, details, event_time, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            shipment_id,
            payload["code"],
            payload["label"],
            payload.get("location"),
            payload.get("details"),
            payload["event_time"],
            ts,
        ),
    )


def list_events(shipment_id: int):
    return query_all(
        """
        SELECT id, code, label, location, details, event_time, created_at
        FROM historique
        WHERE colis_id = ?
        ORDER BY event_time DESC
        """,
        (shipment_id,),
    )


def update_shipment_status(shipment_id: int, code: str, label: str, event_time: str):
    delivered_at = event_time if code == "DELIVERED" else None
    _write(
        """
        UPDATE colis
        SET status_current_code = ?,
            status_current_label = ?,
            updated_at = ?,
            delivered_at = COALESCE(?, delivered_at)
        WHERE id = ?
        """,
        (code, label, now_iso(), delivered_at, shipment_id),
    )
