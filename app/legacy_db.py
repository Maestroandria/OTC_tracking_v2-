from datetime import datetime

from app import db as unified_db
from werkzeug.security import check_password_hash, generate_password_hash


class LegacyDatabase:
    def connect(self):
        return unified_db.get_db()

    def execute(self, query: str, params=None):
        params = params or ()
        conn = self.connect()
        cur = conn.cursor()
        cur.execute(query, params)
        conn.commit()
        return cur

    def fetchone(self, query: str, params=None):
        params = params or ()
        conn = self.connect()
        cur = conn.cursor()
        cur.execute(query, params)
        return cur.fetchone()

    def fetchall(self, query: str, params=None):
        params = params or ()
        conn = self.connect()
        cur = conn.cursor()
        cur.execute(query, params)
        return cur.fetchall()

    def init_all(self):
        unified_db.init_db()

    def init_users_db(self):
        unified_db.init_db()

    def init_tracking_table(self):
        unified_db.init_db()

    def add_tracking(self, tracking_number: str, statut: str, last_update: str, location: str, commentaire=None):
        self.execute(
            """
            INSERT INTO historique (colis_id, code, label, location, details, event_time, created_at)
            SELECT id, ?, ?, ?, ?, ?, ?
            FROM colis
            """,
            (statut, statut, location, commentaire, last_update, datetime.now().isoformat(), tracking_number),
        )

    def get_tracking_history_by_number(self, tracking_number: str):
        return self.fetchall(
            """
            SELECT h.*
            FROM historique h
            INNER JOIN colis c ON c.id = h.colis_id
            WHERE c.tracking_number = ?
            ORDER BY h.event_time ASC
            """,
            (tracking_number,),
        )

    def add_user(
        self,
        username: str,
        email: str,
        password: str,
        nom: str,
        prenom: str,
        fonction: str,
        role: str = "user",
    ):
        password_hash = generate_password_hash(password)
        date_inscription = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            self.execute(
                """
                INSERT INTO users (username, email, password_hash, nom, prenom, fonction, date_inscription, role)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (username, email, password_hash, nom, prenom, fonction, date_inscription, role),
            )
            return True, None
        except Exception as exc:
            return False, str(exc)

    def get_user_by_email_or_username(self, identifier: str):
        return self.fetchone("SELECT * FROM users WHERE email=? OR username=?", (identifier, identifier))

    def verify_password(self, stored_hash: str, password: str):
        return check_password_hash(stored_hash, password)

    def get_client_by_code(self, code_client: str):
        return self.fetchone("SELECT * FROM client WHERE code_client = ?", (code_client,))

    def list_clients(self):
        return self.fetchall(
            """
            SELECT code_client, raison_sociale, adresse, nif, stat, rib
            FROM client
            ORDER BY code_client ASC
            """
        )

    def list_factures(self, limit: int = 100):
        safe_limit = max(1, min(int(limit), 500))
        return self.fetchall(
            f"""
            SELECT
                f.num_facture,
                f.date_facture,
                f.code_client,
                COALESCE(c.raison_sociale, '') AS raison_sociale,
                f.type_facture,
                f.mode_reglement,
                f.total,
                f.devise,
                f.created_at
            FROM facture f
            LEFT JOIN client c ON c.code_client = f.code_client
            ORDER BY f.created_at DESC, f.id DESC
            LIMIT {safe_limit}
            """
        )

    def upsert_client(
        self,
        code_client: str,
        raison_sociale: str,
        adresse: str,
        nif: str,
        stat: str,
        rib: str,
    ):
        code_client = (code_client or "").strip()
        if not code_client:
            return False, "Code client requis."

        existing = self.get_client_by_code(code_client)
        if existing:
            merged_raison_sociale = (raison_sociale or existing[2] or "").strip()
            merged_adresse = (adresse or existing[3] or "").strip()
            merged_nif = (nif or existing[4] or "").strip()
            merged_stat = (stat or existing[5] or "").strip()
            merged_rib = (rib or existing[6] or "").strip()

            if not all([merged_raison_sociale, merged_adresse, merged_nif, merged_stat, merged_rib]):
                return False, "Fiche client incomplète. Complète les informations client avant de facturer."

            self.execute(
                """
                UPDATE client
                SET raison_sociale = ?, adresse = ?, nif = ?, stat = ?, rib = ?
                WHERE code_client = ?
                """,
                (
                    merged_raison_sociale,
                    merged_adresse,
                    merged_nif,
                    merged_stat,
                    merged_rib,
                    code_client,
                ),
            )
            return True, None

        required_fields = {
            "Raison sociale": (raison_sociale or "").strip(),
            "Adresse": (adresse or "").strip(),
            "NIF": (nif or "").strip(),
            "STAT": (stat or "").strip(),
            "RIB": (rib or "").strip(),
        }
        missing_fields = [label for label, value in required_fields.items() if not value]
        if missing_fields:
            return False, f"Nouveau client: renseigne {', '.join(missing_fields)}."

        self.execute(
            """
            INSERT INTO client (code_client, raison_sociale, adresse, nif, stat, rib)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                code_client,
                required_fields["Raison sociale"],
                required_fields["Adresse"],
                required_fields["NIF"],
                required_fields["STAT"],
                required_fields["RIB"],
            ),
        )
        return True, None

    def insert_facture(
        self,
        num_facture: str,
        date_facture: str,
        code_client: str,
        devise: str,
        type_facture: str,
        mode_reglement: str,
        total: float,
        commentaire: str,
        lignes: list[dict],
    ):
        if self.fetchone("SELECT 1 FROM facture WHERE num_facture = ?", (num_facture,)):
            return False, "Numéro de facture déjà existant."
        if not self.fetchone("SELECT 1 FROM client WHERE code_client = ?", (code_client,)):
            return False, "Code client inexistant. Renseigne la fiche client puis réessaie."

        self.execute(
            """
            INSERT INTO facture (num_facture, date_facture, code_client, reference, type_facture, mode_reglement, total, devise, commentaire)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (num_facture, date_facture, code_client, devise, type_facture, mode_reglement, total, devise, commentaire),
        )

        for ligne in lignes:
            self.execute(
                """
                INSERT INTO ligne_facture (num_facture, code_article, designation, prix_unitaire, quantite, montant, devise)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    num_facture,
                    ligne.get("code_article", ""),
                    ligne.get("designation", ""),
                    ligne.get("prix_unitaire", 0.0),
                    ligne.get("quantite", 0.0),
                    ligne.get("montant", 0.0),
                    ligne.get("devise", devise),
                ),
            )
        return True, None

    def ensure_default_users(self):
        defaults = [
            # OSL staff admins
            ("harena.jonah", "harena.jonah@osl-track.com", "Hj@9mXqL2fRv", "Jonah", "Harena", "Administrateur", "admin"),
            ("admin.osl", "admin@osl-track.com", "Mh$4kNpW7dBz", "Harisanjy", "Mahery", "Administrateur", "admin"),
            ("oriental", "oriental@osl-track.com", "On#3yTsE8cGx", "Nokaliana", "Oscars", "Administrateur", "admin"),
            ("tsitohaina.fandresena", "tsitohaina.fandresena@osl-track.com", "Tf!6wQvA5nJu", "Fandresena", "Tsitohaina", "Administrateur", "admin"),
        ]
        for username, email, password, nom, prenom, fonction, role in defaults:
            existing = self.get_user_by_email_or_username(username) or self.get_user_by_email_or_username(email)
            if existing:
                continue
            self.add_user(username, email, password, nom, prenom, fonction, role=role)


def get_legacy_db() -> LegacyDatabase:
    legacy_db = LegacyDatabase()
    legacy_db.init_all()
    return legacy_db
