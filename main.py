"""
Application Flask pour la gestion des produits Doppelherz
"""
import os
import json
from datetime import datetime

from flask import Flask, render_template, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# =============================================================================
# INITIALISATION DE L'APPLICATION
# =============================================================================

app = Flask(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

# Configuration de la base de données
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.getenv('DATABASE_URL') or 'sqlite:///default.db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuration de Flask-Mail
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() in ['true', '1', 'yes']
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

# =============================================================================
# CHARGEMENT DES DONNÉES
# =============================================================================

def load_json_file(filename):
    """Charge un fichier JSON et retourne son contenu"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Attention: Le fichier {filename} n'a pas été trouvé.")
        return []
    except json.JSONDecodeError:
        print(f"Erreur: Le fichier {filename} contient du JSON invalide.")
        return []

PRODUITS = load_json_file('produits_doppelherz.json')
PRODUITS_WITH_DETAILS = load_json_file('details_produits.json')

# =============================================================================
# INITIALISATION DES EXTENSIONS
# =============================================================================

db = SQLAlchemy(app)
mail = Mail(app)

# =============================================================================
# MODÈLES DE BASE DE DONNÉES
# =============================================================================

class Contact(db.Model):
    """Modèle pour les soumissions du formulaire de contact"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    date_submitted = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Contact {self.name}>'

# Créer les tables de la base de données
with app.app_context():
    db.create_all()

# =============================================================================
# ROUTES - PAGE D'ACCUEIL
# =============================================================================

@app.route('/')
def index():
    """Page d'accueil avec les 6 premiers produits"""
    return render_template('index.html', produits=PRODUITS[:6])


# =============================================================================
# ROUTES - PAGES PRODUITS DYNAMIQUES
# =============================================================================

@app.route('/produits')
def produits():
    """Page listant tous les produits"""
    produits_list = load_json_file('produits_doppelherz.json')
    return render_template('produits1.html', produits=produits_list)

@app.route('/produit/<slug>')
def produit_detail(slug):
    """Page de détail d'un produit basée sur son slug"""
    produit = next(
        (p for p in PRODUITS_WITH_DETAILS if p.get('slug') == slug), 
        None
    )
    
    if not produit:
        abort(404)
    
    return render_template('portfolio-details.html', produit=produit)

# =============================================================================
# ROUTES - FORMULAIRE DE CONTACT
# =============================================================================

@app.route('/contact', methods=['POST'])
def contact():
    """Gère la soumission du formulaire de contact"""
    try:
        # Extraction des données du formulaire
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()

        # Validation des champs requis
        if not all([name, email, subject, message]):
            return jsonify({'error': 'Tous les champs sont requis.'}), 400

        # Sauvegarde dans la base de données
        contact_entry = Contact(
            name=name,
            email=email,
            subject=subject,
            message=message
        )
        db.session.add(contact_entry)
        db.session.commit()

        # Envoi de l'email
        msg = Message(
            subject=f"Nouvelle soumission: {subject}",
            recipients=[app.config['MAIL_DEFAULT_SENDER']],
            body=f"""
            Nouveau message de {name} ({email}):
            
            Sujet: {subject}
            
            Message:
            {message}
            
            Soumis le: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
            """
        )
        mail.send(msg)

        return jsonify({'message': 'Votre message a été envoyé. Merci!'}), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Erreur lors de la soumission du contact: {str(e)}")
        return jsonify({'error': 'Une erreur est survenue lors de l\'envoi.'}), 500

# =============================================================================
# GESTIONNAIRES D'ERREURS
# =============================================================================

# @app.errorhandler(404)
# def page_not_found(e):
#     """Gestionnaire d'erreur 404"""
#     return render_template('404.html'), 404

# @app.errorhandler(500)
# def internal_server_error(e):
#     """Gestionnaire d'erreur 500"""
#     return render_template('500.html'), 500

# =============================================================================
# POINT D'ENTRÉE
# =============================================================================

if __name__ == '__main__':
    app.run(debug=True)