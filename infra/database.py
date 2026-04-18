def add_devise_column_to_ligne_facture():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(ligne_facture)")
    columns = [row[1] for row in cur.fetchall()]
    if 'devise' not in columns:
        cur.execute("ALTER TABLE ligne_facture ADD COLUMN devise TEXT")
        conn.commit()
    conn.close()
def add_commentaire_column_to_facture():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(facture)")
    columns = [row[1] for row in cur.fetchall()]
    if 'commentaire' not in columns:
        cur.execute("ALTER TABLE facture ADD COLUMN commentaire TEXT")
        conn.commit()
    conn.close()
def add_devise_column_to_facture():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    # Vérifie si la colonne existe déjà
    cur.execute("PRAGMA table_info(facture)")
    columns = [row[1] for row in cur.fetchall()]
    if 'devise' not in columns:
        cur.execute("ALTER TABLE facture ADD COLUMN devise TEXT")
        conn.commit()
    conn.close()
import os
import sqlite3

def get_db_path():
    return os.path.join(os.path.dirname(__file__), "osl_invoice.db")

def init_db():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    # Table Article
    cur.execute('''
        CREATE TABLE IF NOT EXISTS article (
            code_article TEXT PRIMARY KEY,
            designation TEXT NOT NULL,
            prix_unitaire REAL NOT NULL
        )
    ''')
    # Table Client
    cur.execute('''
        CREATE TABLE IF NOT EXISTS client (
            code_client TEXT PRIMARY KEY,
            raison_sociale TEXT NOT NULL,
            adresse TEXT,
            nif TEXT,
            stat TEXT,
            rib TEXT
        )
    ''')
    # Table Facture (entête)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS facture (
            num_facture TEXT PRIMARY KEY,
            date_facture TEXT NOT NULL,
            code_client TEXT NOT NULL,
            reference TEXT,
            type_facture TEXT,
            mode_reglement TEXT,
            total REAL,
            FOREIGN KEY(code_client) REFERENCES client(code_client)
        )
    ''')
    # Table LigneFacture
    cur.execute('''
        CREATE TABLE IF NOT EXISTS ligne_facture (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            num_facture TEXT NOT NULL,
            code_article TEXT NOT NULL,
            designation TEXT,
            prix_unitaire REAL,
            quantite INTEGER,
            montant REAL,
            FOREIGN KEY(num_facture) REFERENCES facture(num_facture),
            FOREIGN KEY(code_article) REFERENCES article(code_article)
        )
    ''')
    conn.commit()
    conn.close()

    # Ajout automatique des colonnes 'devise' et 'commentaire' si besoin
    add_devise_column_to_facture()
    add_commentaire_column_to_facture()
    add_devise_column_to_ligne_facture()
