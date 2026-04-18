import sqlite3
import os

class Database:
    def get_tracking_history_by_number(self, tracking_number):
        return self.fetchall('SELECT * FROM tracking WHERE tracking_number = ? ORDER BY last_update ASC', (tracking_number,))
    # --- Tracking ---
    def init_tracking_table(self):
        self.execute('''
            CREATE TABLE IF NOT EXISTS tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tracking_number TEXT NOT NULL,
                statut TEXT NOT NULL,
                last_update TEXT NOT NULL,
                location TEXT NOT NULL,
                commentaire TEXT
            )
        ''')

    def add_tracking(self, tracking_number, statut, last_update, location, commentaire=None):
        self.execute('''
            INSERT INTO tracking (tracking_number, statut, last_update, location, commentaire)
            VALUES (?, ?, ?, ?, ?)
        ''', (tracking_number, statut, last_update, location, commentaire))

    def get_tracking_by_number(self, tracking_number):
        return self.fetchone('SELECT * FROM tracking WHERE tracking_number = ? ORDER BY last_update DESC', (tracking_number,))
    def add_article(self, code_article, designation, prix_unitaire):
        self.execute('''
            CREATE TABLE IF NOT EXISTS article (
                code_article TEXT PRIMARY KEY,
                designation TEXT NOT NULL,
                prix_unitaire REAL NOT NULL
            )
        ''')
        self.execute('INSERT INTO article (code_article, designation, prix_unitaire) VALUES (?, ?, ?)', (code_article, designation, prix_unitaire))
    # --- Utilisateurs ---
    def init_users_db(self):
        self.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                nom TEXT NOT NULL,
                prenom TEXT NOT NULL,
                fonction TEXT NOT NULL,
                date_inscription TEXT NOT NULL
            )
        ''')

    def add_user(self, username, email, password, nom, prenom, fonction):
        from werkzeug.security import generate_password_hash
        from datetime import datetime
        password_hash = generate_password_hash(password)
        date_inscription = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            self.execute('''INSERT INTO users (username, email, password_hash, nom, prenom, fonction, date_inscription)
                         VALUES (?, ?, ?, ?, ?, ?, ?)''',
                      (username, email, password_hash, nom, prenom, fonction, date_inscription))
            return True, None
        except Exception as e:
            return False, str(e)

    def get_user_by_email_or_username(self, identifier):
        return self.fetchone('SELECT * FROM users WHERE email=? OR username=?', (identifier, identifier))

    def verify_password(self, stored_hash, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(stored_hash, password)

    # --- Factures ---
    def insert_facture(self, num_facture, date_facture, code_client, devise, type_facture, mode_reglement, total, commentaire, lignes):
        # Vérifier unicité du numéro de facture
        if self.fetchone('SELECT 1 FROM facture WHERE num_facture = ?', (num_facture,)):
            return False, "Numéro de facture déjà existant."
        # Vérifier existence client
        if not self.fetchone('SELECT 1 FROM client WHERE code_client = ?', (code_client,)):
            return False, "Code client inexistant."
        # Insertion entête facture
        self.execute('''
            INSERT INTO facture (num_facture, date_facture, code_client, reference, type_facture, mode_reglement, total, devise, commentaire)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (num_facture, date_facture, code_client, devise, type_facture, mode_reglement, total, devise, commentaire))
        # S'assurer que la table ligne_facture existe
        self.execute('''
            CREATE TABLE IF NOT EXISTS ligne_facture (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                num_facture TEXT NOT NULL,
                code_article TEXT,
                designation TEXT,
                prix_unitaire REAL,
                quantite REAL,
                montant REAL,
                devise TEXT
            )
        ''')
        # Insertion lignes
        for ligne in lignes:
            self.execute('''
                INSERT INTO ligne_facture (num_facture, code_article, designation, prix_unitaire, quantite, montant, devise)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                num_facture,
                ligne.get('code_article', ''),
                ligne.get('designation', ''),
                ligne.get('prix_unitaire', 0.0),
                ligne.get('quantite', 0.0),
                ligne.get('montant', 0.0),
                ligne.get('devise', devise)
            ))
        return True, None

    # Ajoute ici d'autres méthodes métier (get_factures, etc.)
    def __init__(self, db_path):
        self.db_path = db_path

    def connect(self):
        return sqlite3.connect(self.db_path)

    # --- Génériques ---
    def execute(self, query, params=None):
        params = params or ()
        with self.connect() as conn:
            cur = conn.cursor()
            cur.execute(query, params)
            conn.commit()
            return cur

    def fetchone(self, query, params=None):
        params = params or ()
        with self.connect() as conn:
            cur = conn.cursor()
            cur.execute(query, params)
            return cur.fetchone()

    def fetchall(self, query, params=None):
        params = params or ()
        with self.connect() as conn:
            cur = conn.cursor()
            cur.execute(query, params)
            return cur.fetchall()

    # --- Méthodes métier miniERP ---
    def add_client(self, code_client, raison_sociale, adresse, nif, stat, rib):
        self.execute('''
            CREATE TABLE IF NOT EXISTS client (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code_client TEXT NOT NULL,
                raison_sociale TEXT NOT NULL,
                adresse TEXT NOT NULL,
                nif TEXT NOT NULL,
                stat TEXT NOT NULL,
                rib TEXT NOT NULL
            )
        ''')
        self.execute('''
            INSERT INTO client (code_client, raison_sociale, adresse, nif, stat, rib)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (code_client, raison_sociale, adresse, nif, stat, rib))

    def get_clients(self):
        self.execute('''
            CREATE TABLE IF NOT EXISTS client (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code_client TEXT NOT NULL,
                raison_sociale TEXT NOT NULL,
                adresse TEXT NOT NULL,
                nif TEXT NOT NULL,
                stat TEXT NOT NULL,
                rib TEXT NOT NULL
            )
        ''')
        return self.fetchall('SELECT * FROM client')

    def get_client_by_code(self, code_client):
        return self.fetchone('SELECT * FROM client WHERE code_client = ?', (code_client,))

    # Ajoute ici d'autres méthodes métier (add_facture, get_factures, etc.)

# Exemple d'instanciation pour le miniERP :
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'db', 'osl_invoice.db')
db = Database(DB_PATH)
