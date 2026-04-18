import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QSizePolicy
)
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import Qt
from article_widget import ArticleWidget
from client_widget import ClientWidget
from facture_widget import FactureWidget
from database import init_db

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        from PyQt6.QtGui import QIcon
        import os
        logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
        if os.path.exists(logo_path):
            self.setWindowIcon(QIcon(logo_path))
        self.setWindowTitle("Oriental sourcing Logistics")
        self.setGeometry(100, 100, 1000, 650)

        # Thèmes
        self.dark_stylesheet = """
            QMainWindow {
                background-color: #23272e;
            }
            QLabel {
                color: #e0e0e0;
                font-size: 14px;
                font-weight: bold;
                font-family: 'Segoe UI', 'San Francisco', 'Ubuntu', Arial, sans-serif;
            }
            QPushButton {
                background-color: #313742;
                color: #e0e0e0;
                border: none;
                border-radius: 8px;
                padding: 12px 0px;
                font-size: 14px;
                margin: 8px 0px;
            }
            QPushButton:hover {
                background-color: #3e4451;
            }
        """
        self.light_stylesheet = """
            QMainWindow {
                background-color: #f5f5f5;
            }
            QLabel {
                color: #23272e;
                font-size: 14px;
                font-weight: bold;
                font-family: 'Segoe UI', 'San Francisco', 'Ubuntu', Arial, sans-serif;
            }
            QPushButton {
                background-color: #e0e0e0;
                color: #23272e;
                border: none;
                border-radius: 8px;
                padding: 12px 0px;
                font-size: 14px;
                margin: 8px 0px;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
        """
        self.is_dark = True
        self.setStyleSheet(self.dark_stylesheet)

        # Widgets cachés par défaut
        self.article_widget = ArticleWidget()
        self.article_widget.hide()
        self.client_widget = ClientWidget()
        self.client_widget.hide()
        self.facture_widget = FactureWidget()
        self.facture_widget.hide()
        # Forcer le dark mode sur les widgets enfants si possible
        self.article_widget.setStyleSheet("")
        self.client_widget.setStyleSheet("")
        self.facture_widget.setStyleSheet("")

        # Layout principal vertical (barre du haut + contenu)
        main_widget = QWidget()
        main_vlayout = QVBoxLayout()
        main_vlayout.setContentsMargins(0, 0, 0, 0)
        main_vlayout.setSpacing(0)

        # Barre supérieure (top bar)
        top_bar = QWidget()
        top_bar_layout = QHBoxLayout()
        top_bar_layout.setContentsMargins(0, 0, 10, 0)
        top_bar_layout.setSpacing(0)
        top_bar.setFixedHeight(50)
        top_bar.setStyleSheet("background: transparent;")

        # Espace à droite
        top_bar_layout.addStretch()
        self.theme_btn = QPushButton("☀️")
        self.theme_btn.setToolTip("Changer de thème sombre/clair")
        self.theme_btn.setFixedSize(40, 40)
        self.theme_btn.setStyleSheet("font-size: 20px; border-radius: 20px;")
        self.theme_btn.clicked.connect(self.toggle_theme)
        top_bar_layout.addWidget(self.theme_btn)
        top_bar.setLayout(top_bar_layout)

        # Layout principal horizontal (sidebar + contenu)
        content_widget = QWidget()
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Panneau latéral gauche
        sidebar = QWidget()
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setContentsMargins(10, 30, 10, 10)
        sidebar_layout.setSpacing(15)

        # Ajout du logo en haut du panneau latéral
        logo_label = QLabel()
        logo_path = os.path.join(os.path.dirname(__file__), "Otherfiles", "logo.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            pixmap = pixmap.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(pixmap)
            self.setWindowIcon(QIcon(logo_path))
        else:
            logo_label.setText("[Logo non trouvé]")
            logo_label.setStyleSheet("color: #e57373; font-size: 16px;")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(logo_label)

        # Boutons de navigation
        logo_color = "#1e88e5"
        self.btn_article = QPushButton("Article")
        self.btn_client = QPushButton("Client")
        self.btn_facture = QPushButton("Facture")
        for btn in (self.btn_article, self.btn_client, self.btn_facture):
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {logo_color};
                    color: #fff;
                    border: none;
                    border-radius: 8px;
                    padding: 12px 0px;
                    font-size: 18px;
                    margin: 8px 0px;
                }}
                QPushButton:hover {{
                    background-color: #1565c0;
                }}
            """)
        sidebar_layout.addWidget(self.btn_article)
        sidebar_layout.addWidget(self.btn_client)
        sidebar_layout.addWidget(self.btn_facture)
        sidebar_layout.addStretch()
        sidebar.setLayout(sidebar_layout)
        sidebar.setFixedWidth(180)

        # Zone centrale
        self.central_widget = QWidget()
        self.central_layout = QVBoxLayout()
        self.label_accueil = QLabel("Bienvenue sur OSL Invoice Maker !")
        self.label_accueil.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.central_layout.addWidget(self.label_accueil)
        self.central_widget.setLayout(self.central_layout)

        # Ajout au layout horizontal (sidebar + central)
        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.central_widget)
        content_widget.setLayout(main_layout)

        # Ajout barre du haut + contenu au layout vertical principal
        main_vlayout.addWidget(top_bar)
        main_vlayout.addWidget(content_widget)
        main_widget.setLayout(main_vlayout)
        self.setCentralWidget(main_widget)

        # Connexion des boutons (doit être à la fin de __init__)
        self.btn_article.clicked.connect(self.afficher_article)
        self.btn_client.clicked.connect(self.afficher_client)
        self.btn_facture.clicked.connect(self.afficher_facture)

    def afficher_facture(self):
        # Nettoie la zone centrale et affiche le widget Facture
        for i in reversed(range(self.central_layout.count())):
            widget = self.central_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        self.central_layout.addWidget(self.facture_widget)
        self.facture_widget.show()

    def afficher_client(self):
        # Nettoie la zone centrale et affiche le widget Client
        for i in reversed(range(self.central_layout.count())):
            widget = self.central_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        self.central_layout.addWidget(self.client_widget)
        self.client_widget.show()

    def toggle_theme(self):
        self.is_dark = not self.is_dark
        if self.is_dark:
            self.setStyleSheet(self.dark_stylesheet)
            self.theme_btn.setText("🌙")
            self.article_widget.setStyleSheet("")
            self.client_widget.setStyleSheet("")
            self.facture_widget.setStyleSheet("")
        else:
            self.setStyleSheet(self.light_stylesheet)
            self.theme_btn.setText("☀️")
            # Optionnel : appliquer un style clair si besoin

    def afficher_article(self):
        # Nettoie la zone centrale et affiche le widget Article
        for i in reversed(range(self.central_layout.count())):
            widget = self.central_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        self.central_layout.addWidget(self.article_widget)
        self.article_widget.show()

# Bloc de lancement principal (doit être hors classe !)
if __name__ == "__main__":
    init_db()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
