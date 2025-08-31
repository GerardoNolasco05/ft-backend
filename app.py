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

    # Prefer DATABASE_URL (Render Postgres). Fallback to SQLite in /tmp (Render’s writable dir)
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        database_url = database_url.strip()
        if database_url.startswith("postgres://"):
            # Normalize to SQLAlchemy’s expected prefix
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        os.makedirs('/tmp/proft', exist_ok=True)
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/proft/proft.db'

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # --- CORS setup (supports multiple comma-separated origins) ---
    origins_env = os.getenv("CORS_ORIGINS", "*")
    if origins_env == "*":
        origins = "*"
    else:
        origins = [o.strip() for o in origins_env.split(",") if o.strip()]
    CORS(app, resources={r"/*": {"origins": origins}})
    # -------------------------------------------------------------

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

    # --- TEMP: DB debug endpoint ---
    from sqlalchemy import text
    @app.get('/debug/db')
    def debug_db():
        try:
            url = db.engine.url.render_as_string(hide_password=True)
            with db.engine.connect() as conn:
                conn.execute(text("select 1"))
            return {"ok": True, "db_url": url}
        except Exception as e:
            return {"ok": False, "error": str(e)}, 500
    # -------------------------------

    return app


# WSGI entrypoint for gunicorn
app = create_app()

if __name__ == '__main__':
    # local dev only
    app.run(debug=True, port=5000)
