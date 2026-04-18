import sqlite3
from datetime import datetime, timezone

from flask import current_app, g


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exception=None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    db = get_db()
    _drop_obsolete_tables(db)
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            nom TEXT NOT NULL,
            prenom TEXT NOT NULL,
            fonction TEXT NOT NULL,
            date_inscription TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin'))
        );

        CREATE TABLE IF NOT EXISTS client (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code_client TEXT NOT NULL UNIQUE,
            raison_sociale TEXT NOT NULL,
            adresse TEXT NOT NULL,
            nif TEXT NOT NULL,
            stat TEXT NOT NULL,
            rib TEXT NOT NULL,
            user_email TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_email) REFERENCES users(email) ON UPDATE CASCADE ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS colis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        );

        CREATE TABLE IF NOT EXISTS historique (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        );

        CREATE TABLE IF NOT EXISTS facture (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            num_facture TEXT UNIQUE NOT NULL,
            date_facture TEXT,
            code_client TEXT,
            reference TEXT,
            type_facture TEXT,
            mode_reglement TEXT,
            total REAL,
            devise TEXT,
            commentaire TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (code_client) REFERENCES client(code_client) ON UPDATE CASCADE ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS ligne_facture (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            num_facture TEXT NOT NULL,
            code_article TEXT,
            designation TEXT,
            prix_unitaire REAL,
            quantite REAL,
            montant REAL,
            devise TEXT,
            FOREIGN KEY (num_facture) REFERENCES facture(num_facture) ON UPDATE CASCADE ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS facture_colis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            num_facture TEXT NOT NULL,
            colis_id INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (num_facture, colis_id),
            FOREIGN KEY (num_facture) REFERENCES facture(num_facture) ON UPDATE CASCADE ON DELETE CASCADE,
            FOREIGN KEY (colis_id) REFERENCES colis(id) ON UPDATE CASCADE ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        CREATE INDEX IF NOT EXISTS idx_client_code ON client(code_client);
        CREATE INDEX IF NOT EXISTS idx_colis_tracking ON colis(tracking_number);
        CREATE INDEX IF NOT EXISTS idx_historique_colis_time ON historique(colis_id, event_time DESC);
        CREATE INDEX IF NOT EXISTS idx_facture_num ON facture(num_facture);
        CREATE INDEX IF NOT EXISTS idx_ligne_facture_num ON ligne_facture(num_facture);
        CREATE INDEX IF NOT EXISTS idx_facture_colis_num ON facture_colis(num_facture);
        """
    )
    _ensure_colis_columns(db)
    db.commit()


def _drop_obsolete_tables(db: sqlite3.Connection) -> None:
    # Nettoyage schema: on retire les anciennes tables de l'ancienne architecture.
    obsolete_tables = [
        "shipment_events",
        "shipments",
        "tracking",
        "article",
    ]
    for table_name in obsolete_tables:
        db.execute(f"DROP TABLE IF EXISTS {table_name}")


def _ensure_colis_columns(db: sqlite3.Connection) -> None:
    existing_columns = {
        row["name"]
        for row in db.execute("PRAGMA table_info(colis)").fetchall()
    }
    required_columns = {
        "date": "TEXT",
        "client": "TEXT",
        "poids": "REAL",
        "colis": "INTEGER",
        "envoi": "TEXT",
        "frais": "REAL",
    }

    for column_name, column_type in required_columns.items():
        if column_name not in existing_columns:
            db.execute(f"ALTER TABLE colis ADD COLUMN {column_name} {column_type}")


def init_app(app) -> None:
    @app.cli.command("init-db")
    def init_db_command():
        init_db()
        print("Base initialisée")


def query_one(query: str, params: tuple = ()):
    return get_db().execute(query, params).fetchone()


def query_all(query: str, params: tuple = ()):
    return get_db().execute(query, params).fetchall()


def create_shipment(payload: dict):
    db = get_db()
    ts = now_iso()
    db.execute(
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
    db.commit()
    return get_shipment_by_tracking(payload["tracking_number"])


def get_shipment_by_tracking(tracking_number: str):
    return query_one(
        "SELECT * FROM colis WHERE tracking_number = ?",
        (tracking_number,),
    )


def list_shipments(search: str | None = None, limit: int = 50):
    if search:
        return query_all(
            """
            SELECT * FROM colis
            WHERE tracking_number LIKE ?
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (f"%{search}%", limit),
        )

    return query_all(
        "SELECT * FROM colis ORDER BY updated_at DESC LIMIT ?",
        (limit,),
    )


def create_event(shipment_id: int, payload: dict):
    db = get_db()
    ts = now_iso()
    db.execute(
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
    db.commit()


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
    db = get_db()
    delivered_at = event_time if code == "DELIVERED" else None
    db.execute(
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
    db.commit()
