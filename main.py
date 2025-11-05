from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from datetime import datetime
from dotenv import load_dotenv
import os

# Charger les variables d'environnement depuis .env
load_dotenv()

app = Flask(__name__)

# --- Configuration de la base de données ---
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.getenv('DATABASE_URL') or 'sqlite:///default.db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- Configuration de Flask-Mail ---
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() in ['true', '1', 'yes']
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

# Initialize extensions
db = SQLAlchemy(app)
mail = Mail(app)

# Database model for contact form submissions
class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    date_submitted = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Contact {self.name}>'

# Create the database tables
with app.app_context():
    db.create_all()

# Route to serve the homepage
@app.route('/')
def index():
    return render_template('index.html')

# Route to serve the best products
@app.route('/product-1')
def product_1():
    return render_template('product-details-1.html')

@app.route('/product-2')
def product_2():
    return render_template('product-details-2.html')

@app.route('/product-3')
def product_3():
    return render_template('product-details-3.html')

# Route to handle contact form submission
@app.route('/contact', methods=['POST'])
def contact():
    try:
        # Extract form data
        name = request.form['name']
        email = request.form['email']
        subject = request.form['subject']
        message = request.form['message']

        # Validate required fields
        if not all([name, email, subject, message]):
            return jsonify({'error': 'All fields are required.'}), 400

        # Store in database
        contact_entry = Contact(name=name, email=email, subject=subject, message=message)
        db.session.add(contact_entry)
        db.session.commit()

        # Send email
        msg = Message(subject=f"New Contact Form Submission: {subject}",
                      recipients=[email],  # Replace with recipient email
                      body=f"""
                      New message from {name} ({email}):
                      Subject: {subject}
                      Message: {message}
                      Submitted on: {datetime.utcnow()}
                      """)
        mail.send(msg)

        return jsonify({'message': 'Your message has been sent. Thank you!'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)

    