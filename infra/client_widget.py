from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
import sqlite3
import os

class ClientWidget(QWidget):
    def __init__(self):
        super().__init__()
        border_color = "#444"
        text_color = "#f1f1f1"
        bg_color = "#23272e"
        input_bg = "#2c313a"

        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        self.setStyleSheet(f"""
            QWidget {{ background-color: {bg_color}; }}
            QLabel {{ color: {text_color}; font-size: 16px; font-weight: 500; }}
            QLineEdit {{ font-size: 14px; padding: 6px; border-radius: 6px; background: {input_bg}; color: {text_color}; border: 2px solid {border_color}; selection-background-color: #90caf9; selection-color: {text_color}; }}
            QPushButton {{ background-color: #1e88e5; color: #fff; font-size: 14px; border-radius: 8px; padding: 10px 0; margin-top: 16px; }}
            QPushButton:hover {{ background-color: #1565c0; }}
        """)

        self.inputs = {}
        fields = [
            ("Code Client", "code_client"),
            ("Raison Sociale", "raison_sociale"),
            ("Adresse", "adresse"),
            ("NIF", "nif"),
            ("STAT", "stat"),
            ("RIB", "rib"),
        ]
        for label_txt, key in fields:
            label = QLabel(label_txt + " :")
            input_field = QLineEdit()
            layout.addWidget(label)
            layout.addWidget(input_field)
            self.inputs[key] = input_field

        self.btn_create = QPushButton("Créer le client")
        self.btn_create.clicked.connect(self.create_client)
        layout.addWidget(self.btn_create)

        layout.addStretch()
        self.setLayout(layout)

    def create_client(self):
        values = {k: v.text().strip() for k, v in self.inputs.items()}
        if not all(values.values()):
            QMessageBox.warning(self, "Champs manquants", "Veuillez remplir tous les champs.")
            return
        try:
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
                CREATE TABLE IF NOT EXISTS client (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code_client TEXT NOT NULL,
                    raison_sociale TEXT NOT NULL,
                    adresse TEXT NOT NULL,
                    nif TEXT NOT NULL,
                    stat TEXT NOT NULL,
                    rib TEXT NOT NULL
                )
            """)
            cur.execute(
                "INSERT INTO client (code_client, raison_sociale, adresse, nif, stat, rib) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    values["code_client"],
                    values["raison_sociale"],
                    values["adresse"],
                    values["nif"],
                    values["stat"],
                    values["rib"]
                )
            )
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Succès", "Client créé avec succès !")
            for v in self.inputs.values():
                v.clear()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'insertion : {e}")
