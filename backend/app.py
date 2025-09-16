


# =====================
# IMPORTS ET CONFIG
# =====================
import os
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, session, flash
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from datetime import datetime
from database import db

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(
    __name__,
    static_folder=os.path.join(BASE_DIR, "..", "frontend", "static"),
    template_folder=os.path.join(BASE_DIR, "..", "frontend", "templates")
)
app.secret_key = 'change_this_secret_key_for_security'
# Initialisation de la base utilisateurs
db.init_users_db()

# =====================
# ROUTE ARTICLE
# =====================
@app.route('/article', methods=['GET', 'POST'])
def create_article():
    if not session.get('user'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        code_article = request.form.get('code_article', '').strip()
        designation = request.form.get('designation', '').strip()
        prix_unitaire = request.form.get('prix_unitaire', '').strip()
        if not all([code_article, designation, prix_unitaire]):
            flash('Veuillez remplir tous les champs.')
            return render_template('article_form.html')
        try:
            prix_float = float(prix_unitaire)
        except ValueError:
            flash('Le prix doit être un nombre valide.')
            return render_template('article_form.html')
        try:
            db.add_article(code_article, designation, prix_float)
            flash("Article créé avec succès !")
            return redirect(url_for('create_article'))
        except Exception as e:
            flash(f"Erreur lors de l'insertion : {e}")
    return render_template('article_form.html')


# =====================
# ROUTES PUBLIQUES
# =====================
@app.route('/')
def home():
    # Si l'utilisateur n'est pas connecté, il voit la vraie page d'accueil (index.html)
    if not session.get('user'):
        return render_template('index.html')
    # Sinon, il est redirigé vers le dashboard selon son rôle
    return redirect(url_for('dashboard'))


# =====================
# ROUTE TRACKING (admin = saisie, user = consultation)
# =====================
@app.route('/tracking', methods=['GET', 'POST'])
def tracking_page():
    if not session.get('user'):
        return redirect(url_for('login'))
    db.init_tracking_table()
    is_admin = session.get('user') == 'admin'
    if is_admin:
        # Formulaire d'ajout de tracking
        if request.method == 'POST':
            tracking_number = request.form.get('tracking_number', '').strip()
            statut = request.form.get('statut', '').strip()
            last_update = datetime.now().strftime('%Y-%m-%d %H:%M')
            location = request.form.get('location', '').strip()
            commentaire = request.form.get('commentaire', '').strip()
            if not all([tracking_number, statut, location]):
                flash('Veuillez remplir tous les champs obligatoires.')
            else:
                try:
                    db.add_tracking(tracking_number, statut, last_update, location, commentaire)
                    flash('Tracking ajouté avec succès !')
                except Exception as e:
                    flash(f'Erreur lors de l\'ajout : {e}')
        return render_template('tracking_admin.html')
    else:
        # Formulaire de consultation
        tracking_history = None
        if request.method == 'POST':
            tracking_number = request.form.get('tracking_number', '').strip()
            if not tracking_number:
                flash('Veuillez saisir un numéro de suivi.')
            else:
                tracking_history = db.get_tracking_history_by_number(tracking_number)
                if not tracking_history:
                    flash('Aucun statut trouvé pour ce numéro.')
        return render_template('tracking.html', tracking_history=tracking_history)

@app.route('/about')
def about_page():
    return render_template('about.html')

@app.route('/api/track', methods=['POST'])
def api_track():
    data = request.json
    tracking_number = data.get('tracking_number', '').strip()
    if not tracking_number:
        return jsonify({'error': 'Numéro de suivi manquant'}), 400
    fake_response = {
        "status": "En transit",
        "last_update": "2025-07-21 08:45",
        "location": "Antananarivo - Entrepôt central",
        "history": [
            {"date": "2025-07-20 15:00", "status": "Colis expédié"},
            {"date": "2025-07-21 08:45", "status": "Arrivé à l'entrepôt"},
        ]
    }
    return jsonify(fake_response)

# =====================
# AUTHENTIFICATION
# =====================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        nom = request.form['nom']
        prenom = request.form['prenom']
        fonction = request.form['fonction']
        password = request.form['password']
        if not all([username, email, nom, prenom, fonction, password]):
            flash('Tous les champs sont obligatoires.')
            return render_template('register.html')
        success, error = db.add_user(username, email, password, nom, prenom, fonction)
        if success:
            flash('Inscription réussie. Connectez-vous.')
            return redirect(url_for('login'))
        else:
            if error and 'username' in error:
                flash("Nom d'utilisateur déjà utilisé.")
            elif error and 'email' in error:
                flash("E-mail déjà utilisé.")
            else:
                flash("Erreur lors de l'inscription.")
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form['username']
        password = request.form['password']
        user = db.get_user_by_email_or_username(identifier)
        if user and db.verify_password(user[3], password):
            session['user'] = user[1]  # username
            session['email'] = user[2]
            session['nom'] = user[4]
            session['prenom'] = user[5]
            session['fonction'] = user[6]
            return redirect(url_for('dashboard'))
        else:
            flash('Identifiants invalides')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if not session.get('user'):
        return redirect(url_for('login'))
    if session.get('user') == 'admin':
        return render_template('dashboard_admin.html')
    else:
        return render_template('dashboard_user.html')

# =====================
# ROUTE CLIENT
# =====================
@app.route('/client', methods=['GET', 'POST'])
def create_client():
    if not session.get('user'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        code_client = request.form.get('code_client', '').strip()
        raison_sociale = request.form.get('raison_sociale', '').strip()
        adresse = request.form.get('adresse', '').strip()
        nif = request.form.get('nif', '').strip()
        stat = request.form.get('stat', '').strip()
        rib = request.form.get('rib', '').strip()
        if not all([code_client, raison_sociale, adresse, nif, stat, rib]):
            flash('Veuillez remplir tous les champs.')
            return render_template('client_form.html')
        try:
            db.add_client(code_client, raison_sociale, adresse, nif, stat, rib)
            flash('Client créé avec succès !')
            return redirect(url_for('create_client'))
        except Exception as e:
            flash(f"Erreur lors de l'insertion : {e}")
    return render_template('client_form.html')

# =====================
# ROUTE FACTURE
# =====================
@app.route('/facture', methods=['GET', 'POST'])
def create_facture():
    if not session.get('user'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        type_facture = request.form.get('type_facture') or 'Facture'
        type_map = {'Facture': 'FA', 'Devis': 'DV', 'Proforma': 'PRF'}
        prefix = type_map.get(type_facture, 'FA')
        year = datetime.now().strftime('%y')
        # Compteur auto : chercher le dernier numéro pour ce type et année
        from database import db as db_instance
        db_instance.execute('''CREATE TABLE IF NOT EXISTS facture (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            num_facture TEXT UNIQUE,
            date_facture TEXT,
            code_client TEXT,
            reference TEXT,
            type_facture TEXT,
            mode_reglement TEXT,
            total REAL,
            devise TEXT,
            commentaire TEXT
        )''')
        last = db_instance.fetchone("SELECT num_facture FROM facture WHERE num_facture LIKE ? ORDER BY num_facture DESC LIMIT 1", (f"{prefix}{year}%",))
        if last:
            last_num = int(last[0][4:])
            next_num = last_num + 1
        else:
            next_num = 1
        num_facture = f"{prefix}{year}{next_num:03d}"
        date_facture = datetime.now().strftime('%Y-%m-%d')
        code_client = request.form.get('client_code') or ''
        devise = request.form.get('devise') or 'Ar'
        mode_reglement = request.form.get('mode_reglement') or 'Espèces'
        commentaire = request.form.get('commentaire') or ''
        items = request.form.getlist('item')
        quantities = request.form.getlist('quantity')
        unit_prices = request.form.getlist('unit_price')
        lignes = []
        total = 0.0
        for item, qty, price in zip(items, quantities, unit_prices):
            try:
                qty = float(qty)
                price = float(price)
            except Exception:
                qty = 0.0
                price = 0.0
            montant = qty * price
            total += montant
            lignes.append({
                'code_article': '',
                'designation': item,
                'prix_unitaire': price,
                'quantite': qty,
                'montant': montant,
                'devise': devise
            })
        # Insertion en base
        ok, error = db.insert_facture(num_facture, date_facture, code_client, devise, type_facture, mode_reglement, total, commentaire, lignes)
        if not ok:
            flash(error or "Erreur lors de la création de la facture.")
            return redirect(url_for('create_facture'))
        # Génération PDF en mémoire et téléchargement direct
        try:
            from impression import imprimer_facture
            from io import BytesIO
            buffer = BytesIO()
            # Récupérer les détails du client
            client_row = db.get_client_by_code(code_client)
            client_nom = client_row[2] if client_row else ''
            adresse = client_row[3] if client_row else ''
            nif = client_row[4] if client_row else ''
            stat = client_row[5] if client_row else ''
            facture_data = {
                'num_facture': num_facture,
                'date': date_facture,
                'code_client': code_client,
                'client': client_nom,
                'adresse': adresse,
                'nif': nif,
                'stat': stat,
                'devise': devise,
                'type': type_facture,
                'mode_reglement': mode_reglement,
                'total': total,
                'commentaire': commentaire
            }
            imprimer_facture(facture_data, lignes, pdf_path=buffer)
            buffer.seek(0)
            return send_file(buffer, as_attachment=True, download_name=f"Facture_{num_facture}.pdf", mimetype='application/pdf')
        except Exception as e:
            flash(f"Facture créée, mais erreur lors de la génération du PDF : {e}")
            return redirect(url_for('create_facture'))
    return render_template('facture_form.html', date_facture=datetime.now().strftime('%Y-%m-%d'))

if __name__ == '__main__':
    app.run()
