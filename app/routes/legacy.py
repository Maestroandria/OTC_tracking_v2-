from datetime import datetime
from io import BytesIO

from flask import Blueprint, flash, jsonify, redirect, render_template, request, send_file, session, url_for

from app.legacy_db import get_legacy_db
from app.services.legacy_impression import imprimer_facture

bp = Blueprint("legacy", __name__)


@bp.get("/legacy")
def legacy_home():
	return render_template("front_user/index.html")


@bp.get("/about")
def about_page():
	return redirect(url_for("web.index") + "#mission")


@bp.route("/register", methods=["GET", "POST"])
def register():
	db = get_legacy_db()
	if request.method == "POST":
		username = request.form.get("username", "").strip()
		email = request.form.get("email", "").strip()
		nom = request.form.get("nom", "").strip()
		prenom = request.form.get("prenom", "").strip()
		fonction = request.form.get("fonction", "").strip()
		password = request.form.get("password", "").strip()

		if not all([username, email, nom, prenom, fonction, password]):
			flash("Tous les champs sont obligatoires.")
			return render_template("front_user/register.html")

		success, error = db.add_user(username, email, password, nom, prenom, fonction)
		if success:
			flash("Inscription réussie. Connectez-vous.")
			return redirect(url_for("legacy.login"))

		if error and "username" in error:
			flash("Nom d'utilisateur déjà utilisé.")
		elif error and "email" in error:
			flash("E-mail déjà utilisé.")
		else:
			flash("Erreur lors de l'inscription.")

	return render_template("front_user/register.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
	db = get_legacy_db()
	if request.method == "POST":
		identifier = request.form.get("username", "").strip()
		password = request.form.get("password", "").strip()
		user = db.get_user_by_email_or_username(identifier)

		if user and db.verify_password(user[3], password):
			session["user"] = user[1]
			session["email"] = user[2]
			session["nom"] = user[4]
			session["prenom"] = user[5]
			session["fonction"] = user[6]
			session["role"] = user[8] if len(user) > 8 else "user"
			return redirect(url_for("legacy.dashboard"))

		flash("Identifiants invalides")

	return render_template("front_user/login.html")


@bp.get("/logout")
def logout():
	for key in ["user", "email", "nom", "prenom", "fonction", "role"]:
		session.pop(key, None)
	return redirect(url_for("legacy.login"))


def _require_session():
	return session.get("user") is not None


@bp.get("/dashboard")
def dashboard():
	if not _require_session():
		return redirect(url_for("legacy.login"))
	if session.get("role") == "admin":
		return redirect(url_for("web.admin"))
	return render_template("front_user/dashboard_user.html")


@bp.route("/tracking", methods=["GET", "POST"])
def tracking_page():
	if not _require_session():
		return redirect(url_for("legacy.login"))
	if session.get("role") == "admin":
		return redirect(url_for("web.admin"))

	if request.method == "POST":
		tracking_number = request.form.get("tracking_number", "").strip()
		if tracking_number:
			return redirect(url_for("web.tracking_page", tracking_number=tracking_number))
		flash("Veuillez saisir un numéro de suivi.")

	return redirect(url_for("web.tracking_page"))


@bp.route("/facture", methods=["GET", "POST"])
def create_facture():
	if not _require_session():
		return redirect(url_for("legacy.login"))

	db = get_legacy_db()
	clients = db.list_clients()
	factures = db.list_factures(limit=120)
	if request.method == "POST":
		type_facture = request.form.get("type_facture") or "Facture"
		type_map = {"Facture": "FA", "Devis": "DV", "Proforma": "PRF"}
		prefix = type_map.get(type_facture, "FA")
		year = datetime.now().strftime("%y")

		last = db.fetchone(
			"SELECT num_facture FROM facture WHERE num_facture LIKE ? ORDER BY num_facture DESC LIMIT 1",
			(f"{prefix}{year}%",),
		)
		if last:
			last_num = int(last[0][4:])
			next_num = last_num + 1
		else:
			next_num = 1

		num_facture = f"{prefix}{year}{next_num:03d}"
		date_facture = datetime.now().strftime("%Y-%m-%d")
		code_client = request.form.get("client_code") or ""
		client_raison_sociale = request.form.get("client_raison_sociale") or ""
		client_adresse = request.form.get("client_adresse") or ""
		client_nif = request.form.get("client_nif") or ""
		client_stat = request.form.get("client_stat") or ""
		client_rib = request.form.get("client_rib") or ""
		devise = request.form.get("devise") or "Ar"
		mode_reglement = request.form.get("mode_reglement") or "Espèces"
		commentaire = request.form.get("commentaire") or ""

		ok_client, client_error = db.upsert_client(
			code_client,
			client_raison_sociale,
			client_adresse,
			client_nif,
			client_stat,
			client_rib,
		)
		if not ok_client:
			flash(client_error or "Impossible d'enregistrer le client.")
			return redirect(url_for("legacy.create_facture"))

		items = request.form.getlist("item")
		quantities = request.form.getlist("quantity")
		unit_prices = request.form.getlist("unit_price")

		lignes = []
		total = 0.0
		for item, qty, price in zip(items, quantities, unit_prices):
			try:
				qty_value = float(qty)
				price_value = float(price)
			except Exception:
				qty_value = 0.0
				price_value = 0.0
			montant = qty_value * price_value
			total += montant
			lignes.append(
				{
					"code_article": "",
					"designation": item,
					"prix_unitaire": price_value,
					"quantite": qty_value,
					"montant": montant,
					"devise": devise,
				}
			)

		ok, error = db.insert_facture(
			num_facture,
			date_facture,
			code_client,
			devise,
			type_facture,
			mode_reglement,
			total,
			commentaire,
			lignes,
		)
		if not ok:
			flash(error or "Erreur lors de la création de la facture.")
			return redirect(url_for("legacy.create_facture"))

		try:
			buffer = BytesIO()
			client_row = db.get_client_by_code(code_client)
			client_nom = client_row[2] if client_row else ""
			adresse = client_row[3] if client_row else ""
			nif = client_row[4] if client_row else ""
			stat = client_row[5] if client_row else ""

			facture_data = {
				"num_facture": num_facture,
				"date": date_facture,
				"code_client": code_client,
				"client": client_nom,
				"adresse": adresse,
				"nif": nif,
				"stat": stat,
				"devise": devise,
				"type": type_facture,
				"mode_reglement": mode_reglement,
				"total": total,
				"commentaire": commentaire,
			}

			imprimer_facture(facture_data, lignes, pdf_path=buffer)
			buffer.seek(0)
			return send_file(
				buffer,
				as_attachment=True,
				download_name=f"Facture_{num_facture}.pdf",
				mimetype="application/pdf",
			)
		except Exception as exc:
			flash(f"Facture créée, mais erreur lors de la génération du PDF : {exc}")
			return redirect(url_for("legacy.create_facture"))

	return render_template(
		"front_admin/facture_form.html",
		date_facture=datetime.now().strftime("%Y-%m-%d"),
		clients=[dict(row) for row in clients],
		factures=[dict(row) for row in factures],
	)


@bp.post("/legacy/api/track")
def api_track_legacy():
	data = request.get_json(silent=True) or {}
	tracking_number = data.get("tracking_number", "").strip()
	if not tracking_number:
		return jsonify({"error": "Numéro de suivi manquant"}), 400

	fake_response = {
		"status": "En transit",
		"last_update": "2025-07-21 08:45",
		"location": "Antananarivo - Entrepôt central",
		"history": [
			{"date": "2025-07-20 15:00", "status": "Colis expédié"},
			{"date": "2025-07-21 08:45", "status": "Arrivé à l'entrepôt"},
		],
	}
	return jsonify(fake_response)
