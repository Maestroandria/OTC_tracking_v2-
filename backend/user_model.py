from database import db

def init_db():
    db.init_users_db()

def add_user(username, email, password, nom, prenom, fonction):
    return db.add_user(username, email, password, nom, prenom, fonction)

def get_user_by_email_or_username(identifier):
    return db.get_user_by_email_or_username(identifier)

def verify_password(stored_hash, password):
    return db.verify_password(stored_hash, password)

if __name__ == '__main__':
    # Création d'un utilisateur Admin
    username = 'admin'
    email = 'admin@test.com'
    password = 'admin123'
    nom = 'Admin'
    prenom = 'Admin'
    fonction = 'Administrateur'
    success, error = add_user(username, email, password, nom, prenom, fonction)
    if success:
        print('Utilisateur Admin créé avec succès.')
    else:
        print(f'Erreur lors de la création de Admin : {error}')
    init_db()
    print('Base de données initialisée.')
    # Création d'un utilisateur Test
    username = 'Test'
    email = 'test@test.com'
    password = 'test123'
    nom = 'Test'
    prenom = 'Test'
    fonction = 'Utilisateur'
    success, error = add_user(username, email, password, nom, prenom, fonction)
    if success:
        print('Utilisateur Test créé avec succès.')
    else:
        print(f'Erreur lors de la création de Test : {error}')
