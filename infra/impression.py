import os
import sys
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def imprimer_facture(facture_data, lignes, pdf_path=None):
    """
    Génère un PDF de facture à partir des données fournies et l'ouvre pour impression.
    facture_data : dict (num_facture, date, client, devise, type, mode_reglement, total, commentaire)
    lignes : liste de dicts (code_article, designation, prix_unitaire, quantite, montant, devise)
    pdf_path : chemin du PDF à générer (optionnel)
    """
    from io import BytesIO
    if not pdf_path:
        num = facture_data.get('num_facture') or 'SANS_NUM'
        pdf_path = f"Facture_{num}.pdf"
    # Si pdf_path est un objet BytesIO, on génère en mémoire
    if isinstance(pdf_path, BytesIO):
        c = canvas.Canvas(pdf_path, pagesize=A4)
        in_memory = True
    else:
        c = canvas.Canvas(pdf_path, pagesize=A4)
        in_memory = False
    width, height = A4


    # --- Logo en-tête (en haut à gauche, un peu plus haut) ---
    logo_path = os.path.join(os.path.dirname(__file__), "Otherfiles", "logo.png")
    if os.path.exists(logo_path):
        c.drawImage(logo_path, 40, height - 100, width=90, height=80, mask='auto')

    # --- En-tête société (aligné à gauche) ---
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, height - 115, "Oriental Sourcing Logistics")
    c.setFont("Helvetica", 10)
    c.drawString(40, height - 130, "LOT IVX 92 ANKAZOMANGA SUD ANKAZOMANGA ATSIMO ")
    c.drawString(40, height - 145, "101 ANTANANARIVO")
    c.drawString(40, height - 160, " +261343289483 / orientalsourcinglogistics@gmail.com")
    c.drawString(40, height - 175, "NIF : 3019350524")
    c.drawString(40, height - 190, "STAT : 46101 11 2025 0 06370")

    # --- Bloc F A C T U R E ---
    c.setFillColorRGB(0.7, 0.82, 0.93)
    c.roundRect(370, height - 85, 170, 40, 8, fill=1, stroke=0)
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 22)
    # Utilise le champ "type" de facture_data pour le titre du bloc
    titre_facture = facture_data.get('type', 'F A C T U R E')
    c.drawCentredString(455, height - 65, titre_facture)


    # --- Bloc Info facture (gauche sous l'en-tête) ---
    bloc_x = 40
    bloc_y = height - 265
    bloc_w = 220
    bloc_h = 60
    c.setFillColorRGB(0.7, 0.82, 0.93)
    c.roundRect(bloc_x, bloc_y, bloc_w, bloc_h, 8, fill=1, stroke=0)
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(bloc_x + 10, bloc_y + bloc_h - 18, f"Date : {facture_data.get('date','')}")
    c.drawString(bloc_x + 10, bloc_y + bloc_h - 34, f"N° Facture : {facture_data.get('num_facture','')}")
    c.drawString(bloc_x + 10, bloc_y + bloc_h - 50, f"Code client : {facture_data.get('code_client','')}")



    # --- Bloc client (à droite sous le bloc 'Facture') ---
    client_nom = facture_data.get('client', '')
    if client_nom:
        # Positionner juste sous le bloc "Facture" (titre), sans fond
        bloc_client_w = 220
        bloc_client_h = 50
        bloc_client_x = width - bloc_client_w - 40
        bloc_client_y = height - 255
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(bloc_client_x + 10, bloc_client_y + bloc_client_h - 18, "Client :")
        c.setFont("Helvetica", 10)
        c.drawString(bloc_client_x + 65, bloc_client_y + bloc_client_h - 18, client_nom)
        c.drawString(bloc_client_x + 10, bloc_client_y + bloc_client_h - 32, str(facture_data.get('adresse', '')))
        c.drawString(bloc_client_x + 10, bloc_client_y + bloc_client_h - 46, f"NIF: {facture_data.get('nif', '')}")
        c.drawString(bloc_client_x + 10, bloc_client_y + bloc_client_h - 60, f"STAT: {facture_data.get('stat', '')}")

    # --- Intitulé ---
    c.setFont("Helvetica", 10)
    c.drawString(40, height - 280, f"Intitulé: {facture_data.get('commentaire', '')}")

    # --- Tableau des articles (décalé de 20px vers le bas) ---
    y = height - 315
    c.setFont("Helvetica-Bold", 10)
    c.setFillColorRGB(0.7, 0.82, 0.93)
    c.rect(40, y, 500, 20, fill=1, stroke=0)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(50, y + 6, "Quantité")
    c.drawString(120, y + 6, "Désignation")
    c.drawString(370, y + 6, "Prix unit HT")
    c.drawString(460, y + 6, "Prix total HT")
    y -= 20

    c.setFont("Helvetica", 10)
    total_ht = 0
    for ligne in lignes:
        pu = ligne.get('prix_unitaire', 0)
        prix_total_ht = ligne.get('quantite', 0) * pu
        c.drawString(50, y + 6, str(ligne.get('quantite', '')))
        c.drawString(120, y + 6, ligne.get('designation', ''))
        c.drawRightString(420, y + 6, f"{pu:.2f}")
        c.drawRightString(530, y + 6, f"{prix_total_ht:.2f}")
        total_ht += prix_total_ht
        y -= 18
        if y < 120:
            c.showPage()
            y = height - 80

    # --- Totaux (sans TVA) ---
    total_ttc = total_ht
    y -= 10
    c.setFont("Helvetica", 10)
    c.drawRightString(480, y, "Total Hors Taxe")
    c.drawRightString(530, y, f"{total_ht:.2f}")
    y -= 15
    c.setFont("Helvetica-Bold", 11)
    devise = facture_data.get('devise', 'euros')
    c.drawRightString(480, y, f"Total TTC en {devise}")
    c.drawRightString(530, y, f"{total_ttc:.2f}")

    # --- Bas de page : mentions légales ---
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0, 0, 0)
    mode_reglement = facture_data.get('mode_reglement', '')
    c.drawString(40, 100, f"Mode de règlement : {mode_reglement}")
    c.drawString(40, 90, "En votre aimable règlement,")
    c.drawString(40, 80, "Cordialement,")
    c.setFont("Helvetica", 7)
    c.drawString(40, 60, "Conditions de paiement : paiement à réception de facture")
    c.drawString(40, 52, "Aucun escompte consenti pour règlement anticipé")
    c.drawString(40, 44, "Tout incident de paiement est passible d'intérêt de retard. Le montant des pénalités résulte de l'application aux")
    c.drawString(40, 36, "sommes restant dues d'un taux d'intérêt légal en vigueur au moment de l'incident.")
    c.drawString(40, 28, "Indemnité forfaitaire pour frais de recouvrement due au créancier en cas de retard de paiement: 40€")
    c.setFont("Helvetica", 7)
    c.drawCentredString(width / 2, 15, "NIF: 3019350524 STAT: 46101 11 2025 0 06370")

    c.save()
    # Si génération en mémoire (BytesIO), ne rien faire de plus
    if in_memory:
        pdf_path.seek(0)
        return
    # Sinon, ouvrir le PDF automatiquement (Windows/Linux)
    if sys.platform.startswith('win'):
        try:
            os.startfile(pdf_path)
        except Exception as e:
            try:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.critical(None, "Erreur ouverture PDF", f"Impossible d'ouvrir le PDF : {e}\nOuvrez le fichier manuellement.")
            except ImportError:
                print(f"Erreur ouverture PDF : {e}")
    else:
        os.system(f'xdg-open "{pdf_path}"')
