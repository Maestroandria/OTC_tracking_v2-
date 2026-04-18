from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
import sqlite3

class ArticleWidget(QWidget):
    def __init__(self):
        super().__init__()
        border_color = "#444"
        text_color = "#f1f1f1"
        bg_color = "#23272e"
        input_bg = "#2c313a"

        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(25)

        self.setStyleSheet(f"""
            QWidget {{ background-color: {bg_color}; }}
            QLabel {{ color: {text_color}; font-size: 16px; font-weight: 500; }}
            QLineEdit {{ font-size: 14px; padding: 6px; border-radius: 6px; background: {input_bg}; color: {text_color}; border: 2px solid {border_color}; selection-background-color: #90caf9; selection-color: {text_color}; }}
            QPushButton {{ background-color: #1e88e5; color: #fff; font-size: 14px; border-radius: 8px; padding: 10px 0; margin-top: 16px; }}
            QPushButton:hover {{ background-color: #1565c0; }}
        """)

        label_code = QLabel("Code Article :")
        self.input_code = QLineEdit()
        layout.addWidget(label_code)
        layout.addWidget(self.input_code)

        label_designation = QLabel("Désignation :")
        self.input_designation = QLineEdit()
        layout.addWidget(label_designation)
        layout.addWidget(self.input_designation)

        label_prix = QLabel("Prix unitaire :")
        self.input_prix = QLineEdit()
        self.input_prix.setPlaceholderText("Ex: 100.00")
        layout.addWidget(label_prix)
        layout.addWidget(self.input_prix)

        self.btn_create = QPushButton("Créer l'article")
        self.btn_create.clicked.connect(self.create_article)
        layout.addWidget(self.btn_create)

        layout.addStretch()
        self.setLayout(layout)

    def create_article(self):
        code_article = self.input_code.text().strip()
        designation = self.input_designation.text().strip()
        prix = self.input_prix.text().strip()
        if not code_article or not designation or not prix:
            QMessageBox.warning(self, "Champs manquants", "Veuillez remplir tous les champs.")
            return
        try:
            prix_float = float(prix)
        except ValueError:
            QMessageBox.warning(self, "Prix invalide", "Le prix doit être un nombre valide.")
            return
        try:
            import os
            # Recherche du chemin absolu du dossier du projet
            base_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.abspath(os.path.join(base_dir, "..", "osl_invoice.db"))
            if not os.path.exists(db_path):
                db_path = os.path.abspath(os.path.join(base_dir, "osl_invoice.db"))
            if not os.path.exists(db_path):
                QMessageBox.critical(self, "Erreur", f"Base de données introuvable : {db_path}")
                return
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS article (
                    code_article TEXT PRIMARY KEY,
                    designation TEXT NOT NULL,
                    prix_unitaire REAL NOT NULL
                )
            """)
            cur.execute("INSERT INTO article (code_article, designation, prix_unitaire) VALUES (?, ?, ?)", (code_article, designation, prix_float))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Succès", "Article créé avec succès !")
            self.input_code.clear()
            self.input_designation.clear()
            self.input_prix.clear()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'insertion : {e}")
