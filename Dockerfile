# Étape 1 : base Python
FROM python:3.13-slim

# Étape 2 : définir le répertoire de travail
WORKDIR /app

# Étape 3 : copier les fichiers
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Étape 4 : définir les variables d'environnement
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production

# Étape 5 : exposer le port
EXPOSE 5000

# Étape 6 : lancer l'app avec Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "wsgi:app"]
