from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def imprimer_facture(facture_data, lignes, pdf_path=None):
    if not pdf_path:
        num = facture_data.get("num_facture") or "SANS_NUM"
        pdf_path = f"Facture_{num}.pdf"

    in_memory = isinstance(pdf_path, BytesIO)
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, height - 60, "Oriental Sourcing Logistics")
    c.setFont("Helvetica", 10)
    c.drawString(40, height - 75, "LOT IVX 92 ANKAZOMANGA SUD - ANTANANARIVO")
    c.drawString(40, height - 90, "+261343289483 / orientalsourcinglogistics@gmail.com")

    c.setFont("Helvetica-Bold", 20)
    c.drawRightString(width - 40, height - 60, facture_data.get("type", "FACTURE"))

    c.setFont("Helvetica", 10)
    c.drawString(40, height - 120, f"Date : {facture_data.get('date', '')}")
    c.drawString(40, height - 135, f"N° Facture : {facture_data.get('num_facture', '')}")
    c.drawString(40, height - 150, f"Code client : {facture_data.get('code_client', '')}")
    c.drawString(40, height - 165, f"Client : {facture_data.get('client', '')}")

    y = height - 210
    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, y, "Quantité")
    c.drawString(120, y, "Désignation")
    c.drawString(360, y, "Prix unit HT")
    c.drawString(460, y, "Prix total HT")

    total_ht = 0.0
    c.setFont("Helvetica", 10)
    y -= 16
    for ligne in lignes:
        pu = float(ligne.get("prix_unitaire", 0.0) or 0.0)
        qty = float(ligne.get("quantite", 0.0) or 0.0)
        montant = qty * pu
        total_ht += montant

        c.drawString(40, y, str(qty))
        c.drawString(120, y, str(ligne.get("designation", "")))
        c.drawRightString(430, y, f"{pu:.2f}")
        c.drawRightString(540, y, f"{montant:.2f}")
        y -= 14

        if y < 100:
            c.showPage()
            y = height - 80

    y -= 20
    c.setFont("Helvetica-Bold", 11)
    devise = facture_data.get("devise", "Ar")
    c.drawRightString(470, y, f"Total TTC en {devise}")
    c.drawRightString(540, y, f"{total_ht:.2f}")

    c.setFont("Helvetica", 8)
    c.drawString(40, 60, f"Mode de règlement : {facture_data.get('mode_reglement', '')}")
    c.drawString(40, 45, "Conditions de paiement : paiement à réception de facture")

    c.save()

    if in_memory:
        pdf_path.seek(0)
