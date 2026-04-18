
import os
import sqlite3
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, QDateEdit, QMessageBox, QTextEdit, QDialog, QListWidget
)
from PyQt6.QtCore import Qt, QDate



class FactureWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumWidth(700)
        layout = QVBoxLayout(self)

        self.setStyleSheet("""
            QWidget {
                background-color: #23272e;
                color: #f1f1f1;
            }
            QLabel, QLineEdit, QComboBox, QTableWidget, QPushButton, QTextEdit {
                font-size: 12px;
                color: #f1f1f1;
            }
            QLineEdit, QComboBox, QTextEdit {
                background-color: #2c313a;
                border: 1px solid #444;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #1e88e5;
                color: white;
                border-radius: 8px;
            }
            QTableWidget {
                background-color: #23272e;
                alternate-background-color: #2c313a;
                gridline-color: #444;
            }
        """)

        # --- Bloc 1 : Entête facture ---
        entete_layout = QVBoxLayout()
        entete_label = QLabel("Entête de la facture")
        entete_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        entete_layout.addWidget(entete_label)

        entete_labels = QHBoxLayout()
        entete_labels.addWidget(QLabel("N° Facture:"))
        entete_labels.addWidget(QLabel("Date:"))
        entete_labels.addWidget(QLabel("Code client:"))
        entete_labels.addWidget(QLabel(" "))
        entete_labels.addWidget(QLabel("Devise:"))
        entete_labels.addWidget(QLabel("Type:"))
        entete_layout.addLayout(entete_labels)

        entete_form = QHBoxLayout()
        self.num_facture = QLineEdit()
        self.num_facture.setPlaceholderText("Numéro facture")
        self.num_facture.setFixedWidth(120)
        self.date_facture = QDateEdit(QDate.currentDate())
        self.date_facture.setCalendarPopup(True)
        self.date_facture.setFixedWidth(110)
        self.code_client = QLineEdit()
        self.code_client.setPlaceholderText("Code client")
        self.code_client.setFixedWidth(120)
        self.btn_search_client = QPushButton("Rechercher")
        self.btn_search_client.setFixedWidth(90)
        self.btn_search_client.clicked.connect(self.rechercher_client)
        self.devise = QLineEdit()
        self.devise.setPlaceholderText("Devise")
        self.devise.setFixedWidth(100)
        self.type_facture = QComboBox()
        self.type_facture.addItems(["Facture", "Devis", "Proforma"])
        self.type_facture.setFixedWidth(110)
        entete_form.addWidget(self.num_facture)
        entete_form.addWidget(self.date_facture)
        entete_form.addWidget(self.code_client)
        entete_form.addWidget(self.btn_search_client)
        entete_form.addWidget(self.devise)
        entete_form.addWidget(self.type_facture)
        entete_layout.addLayout(entete_form)
        layout.addLayout(entete_layout)

        # --- Bloc 2 : Lignes de facture (tableau) ---
        lignes_label = QLabel("Lignes de facture")
        lignes_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(lignes_label)
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels([
            "Code Article", "Désignation", "Prix Unitaire", "Quantité", "Montant Ligne", "Référence", "Supprimer", "Rechercher"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        # --- Ajout ligne ---
        self.btn_ajouter_ligne = QPushButton("Ajouter une ligne")
        self.btn_ajouter_ligne.clicked.connect(self.ajouter_ligne)
        layout.addWidget(self.btn_ajouter_ligne)

        # Masquer la colonne 'Rechercher' (colonne 7)
        self.table.setColumnHidden(7, True)

        # --- Bloc 3 : Footer et mode de règlement ---
        footer_layout = QHBoxLayout()
        self.total_label = QLabel("Total : 0.00")
        self.mode_reglement = QComboBox()
        self.mode_reglement.addItems(["Espèces", "Chèque", "Virement", "Carte bancaire"])
        footer_layout.addWidget(self.total_label)
        footer_layout.addStretch()
        footer_layout.addWidget(QLabel("Mode de règlement :"))
        footer_layout.addWidget(self.mode_reglement)
        layout.addLayout(footer_layout)

        # --- Commentaire ---
        commentaire_layout = QVBoxLayout()
        commentaire_label = QLabel("Commentaire :")
        commentaire_layout.addWidget(commentaire_label)
        self.commentaire_edit = QTextEdit()
        self.commentaire_edit.setFixedHeight(40)
        commentaire_layout.addWidget(self.commentaire_edit)
        layout.addLayout(commentaire_layout)

        self.articles = self.get_articles()

        # --- Bouton de création de la facture ---
        self.btn_creer_facture = QPushButton("Créer la facture")
        self.btn_creer_facture.setStyleSheet("font-weight: bold; background: #1e88e5; color: white; padding: 10px 20px; border-radius: 8px; font-size: 12px;")
        self.btn_creer_facture.clicked.connect(self.creer_facture)
        layout.addWidget(self.btn_creer_facture)

        # --- Bouton d'impression ---
        self.btn_imprimer = QPushButton("Imprimer la facture")
        self.btn_imprimer.setStyleSheet("font-weight: bold; background: #43a047; color: white; padding: 10px 20px; border-radius: 8px; font-size: 12px;")
        self.btn_imprimer.clicked.connect(self.imprimer_facture)
        layout.addWidget(self.btn_imprimer)

    # (Suppression de la première définition incomplète de ajouter_ligne)

    def remplir_article(self, row):
        code_cb = self.table.cellWidget(row, 0)
        code = code_cb.currentText()
        for art in self.articles:
            if art[0] == code:
                # Met à jour uniquement la désignation (col 1) et le prix (col 2), NE PAS toucher à la quantité (col 3)
                item_designation = self.table.item(row, 1)
                if item_designation:
                    item_designation.setText(art[1])
                else:
                    self.table.setItem(row, 1, QTableWidgetItem(art[1]))
                prix_item = QTableWidgetItem(str(art[2]))
                prix_item.setFlags(prix_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, 2, prix_item)
                self.calculer_montant_ligne(row)
                break

    def selectionner_article(self, row, listw, articles, dialog):
        idx = listw.currentRow()
        if idx >= 0:
            code, designation, prix = articles[idx]
            code_cb = self.table.cellWidget(row, 0)
            code_cb.setCurrentText(code)
            # Met à jour uniquement la désignation (col 1) et le prix (col 2), NE PAS toucher à la quantité (col 3)
            item_designation = self.table.item(row, 1)
            if item_designation:
                item_designation.setText(designation)
            else:
                self.table.setItem(row, 1, QTableWidgetItem(designation))
            prix_item = QTableWidgetItem(str(prix))
            prix_item.setFlags(prix_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 2, prix_item)
            self.calculer_montant_ligne(row)
            dialog.accept()

    def rechercher_article(self, row):
        db_path = os.path.join(os.path.dirname(__file__), "osl_invoice.db")
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT code_article, designation, prix_unitaire FROM article")
        articles = cur.fetchall()
        conn.close()
        dialog = QDialog(self)
        dialog.setWindowTitle("Liste des articles")
        dialog.setMinimumWidth(350)
        vlayout = QVBoxLayout(dialog)
        listw = QListWidget()
        for code, designation, prix in articles:
            listw.addItem(f"{code} - {designation} - {prix}")
        vlayout.addWidget(listw)
        btn_ok = QPushButton("Sélectionner")
        btn_cancel = QPushButton("Annuler")
        btn_ok.clicked.connect(lambda: self.selectionner_article(row, listw, articles, dialog))
        btn_cancel.clicked.connect(dialog.reject)
        btns = QHBoxLayout()
        btns.addWidget(btn_ok)
        btns.addWidget(btn_cancel)
        vlayout.addLayout(btns)
        dialog.exec()

    def calculer_montant_ligne(self, row):
        try:
            prix = float(self.table.item(row, 2).text())
            qty_widget = self.table.cellWidget(row, 3)
            qty_text = qty_widget.text() if qty_widget and qty_widget.text() else "0"
            # Remplacer la virgule par un point pour le calcul float
            qty_text = qty_text.replace(',', '.')
            if qty_text in ('', '.', ','):
                qty = 0.0
            else:
                qty = float(qty_text)
            montant = prix * qty
            self.table.setItem(row, 4, QTableWidgetItem(f"{montant:.2f}"))
        except Exception:
            self.table.setItem(row, 4, QTableWidgetItem("0.00"))
        self.calculer_total()
    def rafraichir_articles(self):
        """Recharge la liste des articles depuis la base et met à jour les ComboBox existants."""
        self.articles = self.get_articles()
        for row in range(self.table.rowCount()):
            code_cb = self.table.cellWidget(row, 0)
            if isinstance(code_cb, QComboBox):
                current = code_cb.currentText()
                code_cb.clear()
                for art in self.articles:
                    code_cb.addItem(art[0])
                if current:
                    idx = code_cb.findText(current)
                    if idx >= 0:
                        code_cb.setCurrentIndex(idx)

    def calculer_total(self):
        total = 0.0
        for row in range(self.table.rowCount()):
            try:
                montant = float(self.table.item(row, 4).text())
                total += montant
            except Exception:
                pass
        self.total_label.setText(f"Total : {total:.2f}")

    def supprimer_ligne(self, row):
        self.table.removeRow(row)
        self.calculer_total()

    def rechercher_client(self):
        db_path = os.path.join(os.path.dirname(__file__), "osl_invoice.db")
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT code_client, raison_sociale FROM client")
        clients = cur.fetchall()
        conn.close()
        dialog = QDialog(self)
        dialog.setWindowTitle("Liste des clients")
        dialog.setMinimumWidth(350)
        vlayout = QVBoxLayout(dialog)
        listw = QListWidget()
        for code, raison in clients:
            listw.addItem(f"{code} - {raison}")
        vlayout.addWidget(listw)
        btn_ok = QPushButton("Sélectionner")
        btn_cancel = QPushButton("Annuler")
        btn_ok.clicked.connect(lambda: self.selectionner_client(listw, clients, dialog))
        btn_cancel.clicked.connect(dialog.reject)
        btns = QHBoxLayout()
        btns.addWidget(btn_ok)
        btns.addWidget(btn_cancel)
        vlayout.addLayout(btns)
        dialog.exec()

    def selectionner_client(self, listw, clients, dialog):
        idx = listw.currentRow()
        if idx >= 0:
            code = clients[idx][0]
            self.code_client.setText(code)
            dialog.accept()

    def check_client(self):
        code = self.code_client.text().strip()
        if not code:
            QMessageBox.warning(self, "Erreur", "Veuillez saisir un code client.")
            return
        db_path = os.path.join(os.path.dirname(__file__), "osl_invoice.db")
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT raison_sociale FROM client WHERE code_client = ?", (code,))
        row = cur.fetchone()
        conn.close()
        if row:
            QMessageBox.information(self, "Client trouvé", f"Client : {row[0]}")
        else:
            QMessageBox.warning(self, "Erreur", "Client non trouvé dans la base de données.")

    def get_articles(self):
        db_path = os.path.join(os.path.dirname(__file__), "osl_invoice.db")
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT code_article, designation, prix_unitaire FROM article")
        articles = cur.fetchall()
        conn.close()
        return articles

    def creer_facture(self):
        num_facture = self.num_facture.text().strip()
        date_facture = self.date_facture.date().toString("yyyy-MM-dd")
        code_client = self.code_client.text().strip()
        devise = self.devise.text().strip()
        type_facture = self.type_facture.currentText()
        mode_reglement = self.mode_reglement.currentText()
        total = self.total_label.text().replace("Total : ", "").replace(",", ".")
        try:
            total = float(total)
        except Exception:
            total = 0.0

        if not num_facture or not code_client:
            QMessageBox.warning(self, "Erreur", "Numéro de facture et code client obligatoires.")
            return

        db_path = os.path.join(os.path.dirname(__file__), "osl_invoice.db")
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        # Vérifier unicité du numéro de facture
        cur.execute("SELECT 1 FROM facture WHERE num_facture = ?", (num_facture,))
        if cur.fetchone():
            QMessageBox.warning(self, "Erreur", "Numéro de facture déjà existant.")
            conn.close()
            return
        # Vérifier existence client
        cur.execute("SELECT 1 FROM client WHERE code_client = ?", (code_client,))
        if not cur.fetchone():
            QMessageBox.warning(self, "Erreur", "Code client inexistant.")
            conn.close()
            return
        # Insertion entête facture
        commentaire = self.commentaire_edit.toPlainText().strip()
        cur.execute("""
            INSERT INTO facture (num_facture, date_facture, code_client, reference, type_facture, mode_reglement, total, commentaire)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (num_facture, date_facture, code_client, devise, type_facture, mode_reglement, total, commentaire))

        # Insertion lignes
        for row in range(self.table.rowCount()):
            code_article = self.table.cellWidget(row, 0).currentText()
            designation = self.table.item(row, 1).text() if self.table.item(row, 1) else ""
            try:
                prix_unitaire = float(self.table.item(row, 2).text())
            except Exception:
                prix_unitaire = 0.0
            try:
                quantite = float(self.table.cellWidget(row, 3).text().replace(',', '.') or 0)
            except Exception:
                quantite = 0.0
            try:
                montant = float(self.table.item(row, 4).text())
            except Exception:
                montant = 0.0
            devise_ligne = self.table.item(row, 5).text() if self.table.item(row, 5) else devise
            cur.execute("""
                INSERT INTO ligne_facture (num_facture, code_article, designation, prix_unitaire, quantite, montant, devise)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (num_facture, code_article, designation, prix_unitaire, quantite, montant, devise_ligne))

        conn.commit()
        conn.close()
        QMessageBox.information(self, "Succès", "Facture créée avec succès !")
        self.reset_form()

    def reset_form(self):
        self.num_facture.clear()
        self.code_client.clear()
        self.devise.clear()
        self.type_facture.setCurrentIndex(0)
        self.mode_reglement.setCurrentIndex(0)
        self.table.setRowCount(0)
        self.total_label.setText("Total : 0.00")
        self.commentaire_edit.clear()

    def imprimer_facture(self):
        from impression import imprimer_facture
        num_facture = self.num_facture.text().strip()
        date_facture = self.date_facture.date().toString("yyyy-MM-dd")
        code_client = self.code_client.text().strip()
        devise = self.devise.text().strip()
        type_facture = self.type_facture.currentText()
        mode_reglement = self.mode_reglement.currentText()
        total = self.total_label.text().replace("Total : ", "").replace(",", ".")
        commentaire = self.commentaire_edit.toPlainText().strip()
        client_nom = ""
        Adresse = ""
        nif = ""
        stat = ""
        if code_client:
            db_path = os.path.join(os.path.dirname(__file__), "osl_invoice.db")
            try:
                conn = sqlite3.connect(db_path)
                cur = conn.cursor()
                cur.execute("SELECT raison_sociale, adresse, nif, stat FROM client WHERE code_client = ?", (code_client,))
                row = cur.fetchone()
                if row:
                    client_nom = row[0] or ""
                    Adresse = row[1] or ""
                    nif = row[2] or ""
                    stat = row[3] or ""
                conn.close()
            except Exception:
                pass
        try:
            total = float(total)
        except Exception:
            total = 0.0

        facture_data = {
            'num_facture': num_facture,
            'date': date_facture,
            'code_client': code_client,
            'client': client_nom,
            'adresse': Adresse,
            'nif': nif,
            'stat': stat,
            'devise': devise,
            'type': type_facture,
            'mode_reglement': mode_reglement,
            'total': total,
            'commentaire': commentaire
        }
        lignes = []
        for row in range(self.table.rowCount()):
            code_article = self.table.cellWidget(row, 0).currentText()
            designation = self.table.item(row, 1).text() if self.table.item(row, 1) else ""
            try:
                prix_unitaire = float(self.table.item(row, 2).text())
            except Exception:
                prix_unitaire = 0.0
            try:
                quantite = float(self.table.cellWidget(row, 3).text().replace(',', '.') or 0)
            except Exception:
                quantite = 0.0
            try:
                montant = float(self.table.item(row, 4).text())
            except Exception:
                montant = 0.0
            devise_ligne = self.table.item(row, 5).text() if self.table.item(row, 5) else devise
            lignes.append({
                'code_article': code_article,
                'designation': designation,
                'prix_unitaire': prix_unitaire,
                'quantite': quantite,
                'montant': montant,
                'devise': devise_ligne
            })
        imprimer_facture(facture_data, lignes)


    # Toutes les méthodes doivent être définies ici, sans code flottant ni dupliqué en dehors des méthodes.

    def ajouter_ligne(self):
        row = self.table.rowCount()
        self.table.insertRow(row)
        # Code Article (ComboBox)
        code_cb = QComboBox()
        for art in self.articles:
            code_cb.addItem(art[0])
        code_cb.currentIndexChanged.connect(lambda idx, r=row: self.remplir_article(r))
        self.table.setCellWidget(row, 0, code_cb)

        # Désignation (éditable)
        self.table.setItem(row, 1, QTableWidgetItem(""))

        # Prix unitaire (non éditable)
        prix_item = QTableWidgetItem("")
        prix_item.setFlags(prix_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 2, prix_item)

        # Quantité (QLineEdit éditable, vide par défaut)
        qty_edit = QLineEdit()
        qty_edit.setPlaceholderText("Quantité")
        qty_edit.setText("")
        qty_edit.setReadOnly(False)
        qty_edit.setEnabled(True)
        qty_edit.setStyleSheet("background-color: #fff; color: #23272e;")
        qty_edit.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        # Calcul dynamique du montant ligne
        qty_edit.textChanged.connect(lambda val, r=row: self.calculer_montant_ligne(r))
        self.table.setCellWidget(row, 3, qty_edit)

        # Montant ligne (non éditable)
        montant_item = QTableWidgetItem("0.00")
        montant_item.setFlags(montant_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 4, montant_item)

        # Devise (par défaut celle de l'entête)
        self.table.setItem(row, 5, QTableWidgetItem(self.devise.text()))

        # Bouton supprimer (dans la ligne)
        btn_suppr = QPushButton("Supprimer")
        btn_suppr.clicked.connect(lambda _, r=row: self.supprimer_ligne(r))
        self.table.setCellWidget(row, 6, btn_suppr)

        # Bouton rechercher article (dans la ligne)
        btn_search_article = QPushButton("Rechercher")
        btn_search_article.clicked.connect(lambda _, r=row: self.rechercher_article(r))
        self.table.setCellWidget(row, 7, btn_search_article)

        # Calcul initial (quantité vide = montant 0)
        self.calculer_montant_ligne(row)

    def rechercher_article(self, row):
        db_path = os.path.join(os.path.dirname(__file__), "osl_invoice.db")
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT code_article, designation, prix_unitaire FROM article")
        articles = cur.fetchall()
        conn.close()
        dialog = QDialog(self)
        dialog.setWindowTitle("Liste des articles")
        dialog.setMinimumWidth(350)
        vlayout = QVBoxLayout(dialog)
        listw = QListWidget()
        for code, designation, prix in articles:
            listw.addItem(f"{code} - {designation} - {prix}")
        vlayout.addWidget(listw)
        btn_ok = QPushButton("Sélectionner")
        btn_cancel = QPushButton("Annuler")
        btn_ok.clicked.connect(lambda: self.selectionner_article(row, listw, articles, dialog))
        btn_cancel.clicked.connect(dialog.reject)
        btns = QHBoxLayout()
        btns.addWidget(btn_ok)
        btns.addWidget(btn_cancel)
        vlayout.addLayout(btns)
        dialog.exec()

    def selectionner_article(self, row, listw, articles, dialog):
        idx = listw.currentRow()
        if idx >= 0:
            code, designation, prix = articles[idx]
            code_cb = self.table.cellWidget(row, 0)
            code_cb.setCurrentText(code)
            # Désignation éditable
            designation_item = QTableWidgetItem(designation)
            self.table.setItem(row, 1, designation_item)
            # Prix unitaire non éditable
            prix_item = QTableWidgetItem(str(prix))
            prix_item.setFlags(prix_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 2, prix_item)
            self.calculer_montant_ligne(row)
            dialog.accept()

    def remplir_article(self, row):
        code_cb = self.table.cellWidget(row, 0)
        code = code_cb.currentText()
        for art in self.articles:
            if art[0] == code:
                # Désignation éditable
                designation_item = QTableWidgetItem(art[1])
                self.table.setItem(row, 1, designation_item)
                # Prix unitaire non éditable
                prix_item = QTableWidgetItem(str(art[2]))
                prix_item.setFlags(prix_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, 2, prix_item)
                self.calculer_montant_ligne(row)
                break

    def calculer_montant_ligne(self, row):
        try:
            prix = float(self.table.item(row, 2).text())
            qty_widget = self.table.cellWidget(row, 3)
            qty_text = qty_widget.text().replace(',', '.') if qty_widget and qty_widget.text() else "0"
            qty = float(qty_text)
            montant = prix * qty
            self.table.setItem(row, 4, QTableWidgetItem(f"{montant:.2f}"))
        except Exception:
            self.table.setItem(row, 4, QTableWidgetItem("0.00"))
        self.calculer_total()

    def calculer_total(self):
        total = 0.0
        for row in range(self.table.rowCount()):
            try:
                montant = float(self.table.item(row, 4).text())
                total += montant
            except Exception:
                pass
        self.total_label.setText(f"Total : {total:.2f}")

    def supprimer_ligne(self, row):
        self.table.removeRow(row)
        self.calculer_total()

    def rechercher_client(self):
        db_path = os.path.join(os.path.dirname(__file__), "osl_invoice.db")
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT code_client, raison_sociale FROM client")
        clients = cur.fetchall()
        conn.close()
        dialog = QDialog(self)
        dialog.setWindowTitle("Liste des clients")
        dialog.setMinimumWidth(350)
        vlayout = QVBoxLayout(dialog)
        listw = QListWidget()
        for code, raison in clients:
            listw.addItem(f"{code} - {raison}")
        vlayout.addWidget(listw)
        btn_ok = QPushButton("Sélectionner")
        btn_cancel = QPushButton("Annuler")
        btn_ok.clicked.connect(lambda: self.selectionner_client(listw, clients, dialog))
        btn_cancel.clicked.connect(dialog.reject)
        btns = QHBoxLayout()
        btns.addWidget(btn_ok)
        btns.addWidget(btn_cancel)
        vlayout.addLayout(btns)
        dialog.exec()

    def selectionner_client(self, listw, clients, dialog):
        idx = listw.currentRow()
        if idx >= 0:
            code = clients[idx][0]
            self.code_client.setText(code)
            dialog.accept()

    def check_client(self):
        code = self.code_client.text().strip()
        if not code:
            QMessageBox.warning(self, "Erreur", "Veuillez saisir un code client.")
            return
        db_path = os.path.join(os.path.dirname(__file__), "osl_invoice.db")
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT raison_sociale FROM client WHERE code_client = ?", (code,))
        row = cur.fetchone()
        conn.close()
        if row:
            QMessageBox.information(self, "Client trouvé", f"Client : {row[0]}")
        else:
            QMessageBox.warning(self, "Erreur", "Client non trouvé dans la base de données.")

    def get_articles(self):
        db_path = os.path.join(os.path.dirname(__file__), "osl_invoice.db")
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT code_article, designation, prix_unitaire FROM article")
        articles = cur.fetchall()
        conn.close()
        return articles

    def creer_facture(self):
        num_facture = self.num_facture.text().strip()
        date_facture = self.date_facture.date().toString("yyyy-MM-dd")
        code_client = self.code_client.text().strip()
        devise = self.devise.text().strip()
        type_facture = self.type_facture.currentText()
        mode_reglement = self.mode_reglement.currentText()
        total = self.total_label.text().replace("Total : ", "").replace(",", ".")
        try:
            total = float(total)
        except Exception:
            total = 0.0

        if not num_facture or not code_client:
            QMessageBox.warning(self, "Erreur", "Numéro de facture et code client obligatoires.")
            return

        db_path = os.path.join(os.path.dirname(__file__), "osl_invoice.db")
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        # Vérifier unicité du numéro de facture
        cur.execute("SELECT 1 FROM facture WHERE num_facture = ?", (num_facture,))
        if cur.fetchone():
            QMessageBox.warning(self, "Erreur", "Numéro de facture déjà existant.")
            conn.close()
            return
        # Vérifier existence client
        cur.execute("SELECT 1 FROM client WHERE code_client = ?", (code_client,))
        if not cur.fetchone():
            QMessageBox.warning(self, "Erreur", "Code client inexistant.")
            conn.close()
            return
        # Insertion entête facture
        commentaire = self.commentaire_edit.toPlainText().strip()
        cur.execute("""
            INSERT INTO facture (num_facture, date_facture, code_client, reference, type_facture, mode_reglement, total, commentaire)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (num_facture, date_facture, code_client, devise, type_facture, mode_reglement, total, commentaire))

        # Insertion lignes
        for row in range(self.table.rowCount()):
            code_article = self.table.cellWidget(row, 0).currentText()
            designation = self.table.item(row, 1).text() if self.table.item(row, 1) else ""
            try:
                prix_unitaire = float(self.table.item(row, 2).text())
            except Exception:
                prix_unitaire = 0.0
            try:
                quantite = float(self.table.cellWidget(row, 3).text().replace(',', '.') or 0)
            except Exception:
                quantite = 0.0
            try:
                montant = float(self.table.item(row, 4).text())
            except Exception:
                montant = 0.0
            devise_ligne = self.table.item(row, 5).text() if self.table.item(row, 5) else devise
            cur.execute("""
                INSERT INTO ligne_facture (num_facture, code_article, designation, prix_unitaire, quantite, montant, devise)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (num_facture, code_article, designation, prix_unitaire, quantite, montant, devise_ligne))

        conn.commit()
        conn.close()
        QMessageBox.information(self, "Succès", "Facture créée avec succès !")
        self.reset_form()

    def reset_form(self):
        self.num_facture.clear()
        self.code_client.clear()
        self.devise.clear()
        self.type_facture.setCurrentIndex(0)
        self.mode_reglement.setCurrentIndex(0)
        self.table.setRowCount(0)
        self.total_label.setText("Total : 0.00")
        self.commentaire_edit.clear()

    def imprimer_facture(self):
        from impression import imprimer_facture
        num_facture = self.num_facture.text().strip()
        date_facture = self.date_facture.date().toString("yyyy-MM-dd")
        code_client = self.code_client.text().strip()
        devise = self.devise.text().strip()
        type_facture = self.type_facture.currentText()
        mode_reglement = self.mode_reglement.currentText()
        total = self.total_label.text().replace("Total : ", "").replace(",", ".")
        commentaire = self.commentaire_edit.toPlainText().strip()
        client_nom = ""
        Adresse = ""
        nif = ""
        stat = ""
        if code_client:
            import sqlite3, os
            db_path = os.path.join(os.path.dirname(__file__), "osl_invoice.db")
            try:
                conn = sqlite3.connect(db_path)
                cur = conn.cursor()
                cur.execute("SELECT raison_sociale, adresse, nif, stat FROM client WHERE code_client = ?", (code_client,))
                row = cur.fetchone()
                if row:
                    client_nom = row[0] or ""
                    Adresse = row[1] or ""
                    nif = row[2] or ""
                    stat = row[3] or ""
                conn.close()
            except Exception:
                pass
        try:
            total = float(total)
        except Exception:
            total = 0.0

        facture_data = {
            'num_facture': num_facture,
            'date': date_facture,
            'code_client': code_client,
            'client': client_nom,
            'adresse': Adresse,
            'nif': nif,
            'stat': stat,
            'devise': devise,
            'type': type_facture,
            'mode_reglement': mode_reglement,
            'total': total,
            'commentaire': commentaire
        }
        lignes = []
        for row in range(self.table.rowCount()):
            code_article = self.table.cellWidget(row, 0).currentText()
            designation = self.table.item(row, 1).text() if self.table.item(row, 1) else ""
            try:
                prix_unitaire = float(self.table.item(row, 2).text())
            except Exception:
                prix_unitaire = 0.0
            try:
                quantite = float(self.table.cellWidget(row, 3).text().replace(',', '.') or 0)
            except Exception:
                quantite = 0.0
            try:
                montant = float(self.table.item(row, 4).text())
            except Exception:
                montant = 0.0
            devise_ligne = self.table.item(row, 5).text() if self.table.item(row, 5) else devise
            lignes.append({
                'code_article': code_article,
                'designation': designation,
                'prix_unitaire': prix_unitaire,
                'quantite': quantite,
                'montant': montant,
                'devise': devise_ligne
            })
        imprimer_facture(facture_data, lignes)

    def creer_facture(self):
        num_facture = self.num_facture.text().strip()
        date_facture = self.date_facture.date().toString("yyyy-MM-dd")
        code_client = self.code_client.text().strip()
        devise = self.devise.text().strip()
        type_facture = self.type_facture.currentText()
        mode_reglement = self.mode_reglement.currentText()
        total = self.total_label.text().replace("Total : ", "").replace(",", ".")
        try:
            total = float(total)
        except Exception:
            total = 0.0

        if not num_facture or not code_client:
            QMessageBox.warning(self, "Erreur", "Numéro de facture et code client obligatoires.")
            return

        db_path = os.path.join(os.path.dirname(__file__), "osl_invoice.db")
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        # Vérifier unicité du numéro de facture
        cur.execute("SELECT 1 FROM facture WHERE num_facture = ?", (num_facture,))
        if cur.fetchone():
            QMessageBox.warning(self, "Erreur", "Numéro de facture déjà existant.")
            conn.close()
            return
        # Vérifier existence client
        cur.execute("SELECT 1 FROM client WHERE code_client = ?", (code_client,))
        if not cur.fetchone():
            QMessageBox.warning(self, "Erreur", "Code client inexistant.")
            conn.close()
            return
        # Insertion entête facture
        commentaire = self.commentaire_edit.toPlainText().strip()
        cur.execute("""
            INSERT INTO facture (num_facture, date_facture, code_client, reference, type_facture, mode_reglement, total, devise, commentaire)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (num_facture, date_facture, code_client, devise, type_facture, mode_reglement, total, devise, commentaire))

        # Insertion lignes
        for row in range(self.table.rowCount()):
            code_article = self.table.cellWidget(row, 0).currentText()
            designation = self.table.item(row, 1).text() if self.table.item(row, 1) else ""
            try:
                prix_unitaire = float(self.table.item(row, 2).text())
            except Exception:
                prix_unitaire = 0.0
            try:
                quantite = float(self.table.cellWidget(row, 3).text().replace(',', '.') or 0)
            except Exception:
                quantite = 0.0
            try:
                montant = float(self.table.item(row, 4).text())
            except Exception:
                montant = 0.0
            devise_ligne = self.table.item(row, 5).text() if self.table.item(row, 5) else devise
            cur.execute("""
                INSERT INTO ligne_facture (num_facture, code_article, designation, prix_unitaire, quantite, montant, devise)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (num_facture, code_article, designation, prix_unitaire, quantite, montant, devise_ligne))

        conn.commit()
        conn.close()
        QMessageBox.information(self, "Succès", "Facture créée avec succès !")
        self.reset_form()

    def reset_form(self):
        self.num_facture.clear()
        self.code_client.clear()
        self.devise.clear()
        self.type_facture.setCurrentIndex(0)
        self.mode_reglement.setCurrentIndex(0)
        self.table.setRowCount(0)
        self.total_label.setText("Total : 0.00")
        self.commentaire_edit.clear()

    def check_client(self):
        code = self.code_client.text().strip()
        if not code:
            QMessageBox.warning(self, "Erreur", "Veuillez saisir un code client.")
            return
        db_path = os.path.join(os.path.dirname(__file__), "osl_invoice.db")
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT raison_sociale FROM client WHERE code_client = ?", (code,))
        row = cur.fetchone()
        conn.close()
        if row:
            QMessageBox.information(self, "Client trouvé", f"Client : {row[0]}")
        else:
            QMessageBox.warning(self, "Erreur", "Client non trouvé dans la base de données.")

    def get_articles(self):
        db_path = os.path.join(os.path.dirname(__file__), "osl_invoice.db")
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT code_article, designation, prix_unitaire FROM article")
        articles = cur.fetchall()
        conn.close()
        return articles

    # (Suppression de la redéfinition de ajouter_ligne avec QSpinBox)

    def remplir_article(self, row):
        code_cb = self.table.cellWidget(row, 0)
        code = code_cb.currentText()
        for art in self.articles:
            if art[0] == code:
                self.table.setItem(row, 1, QTableWidgetItem(art[1]))
                self.table.setItem(row, 2, QTableWidgetItem(str(art[2])))
                self.calculer_montant_ligne(row)
                break

    def calculer_montant_ligne(self, row):
        try:
            prix = float(self.table.item(row, 2).text())
            qty_widget = self.table.cellWidget(row, 3)
            qty_text = qty_widget.text().replace(',', '.') if qty_widget and qty_widget.text() else "0"
            qty = float(qty_text)
            montant = prix * qty
            self.table.setItem(row, 4, QTableWidgetItem(f"{montant:.2f}"))
        except Exception:
            self.table.setItem(row, 4, QTableWidgetItem("0.00"))
        self.calculer_total()

    def calculer_total(self):
        total = 0.0
        for row in range(self.table.rowCount()):
            try:
                montant = float(self.table.item(row, 4).text())
                total += montant
            except Exception:
                pass
        self.total_label.setText(f"Total : {total:.2f}")

    def supprimer_ligne(self, row):
        self.table.removeRow(row)
        self.calculer_total()


# Permettre l'exécution autonome du widget pour test
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    w = FactureWidget()
    w.show()
    sys.exit(app.exec())
