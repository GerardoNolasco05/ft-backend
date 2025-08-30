# app.py
import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from db import db
from routes import coaches_bp, clients_bp, workouts_bp, exercises_bp, load_weights_bp

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'change-me')

    # Prefer DATABASE_URL (Render Postgres). Fallback to an on-disk SQLite in /tmp (writable on Render).
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        # SQLAlchemy 2.x expects postgresql+psycopg etc; Render usually supplies a ready URL
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        os.makedirs('/tmp/proft', exist_ok=True)
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/proft/proft.db'

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    CORS(app, resources={r"/*": {"origins": os.getenv("CORS_ORIGINS", "*")}})

    db.init_app(app)
    with app.app_context():
        db.create_all()

    # blueprints
    app.register_blueprint(coaches_bp, url_prefix='/coaches')
    app.register_blueprint(clients_bp, url_prefix='/clients')
    app.register_blueprint(workouts_bp, url_prefix='/workouts')
    app.register_blueprint(exercises_bp, url_prefix='/exercises')
    app.register_blueprint(load_weights_bp, url_prefix='/load-weights')

    @app.get('/health')
    def health():
        return {"status": "ok"}

    @app.get('/')
    def home():
        return "Welcome to ProFT API!"

    return app

# WSGI entrypoint for gunicorn
app = create_app()

if __name__ == '__main__':
    # local dev only
    app.run(debug=True, port=5000)
