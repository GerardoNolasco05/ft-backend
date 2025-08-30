from flask import Flask
from flask_cors import CORS
from db import db
from routes import coaches_bp, clients_bp, workouts_bp, exercises_bp, load_weights_bp
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'proft.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


CORS(app, resources={r"/*": {"origins": ["http://localhost:5173"]}}, supports_credentials=True)

db.init_app(app)

app.register_blueprint(coaches_bp, url_prefix='/coaches')
app.register_blueprint(clients_bp, url_prefix='/clients')
app.register_blueprint(workouts_bp, url_prefix='/workouts')
app.register_blueprint(exercises_bp, url_prefix='/exercises')
app.register_blueprint(load_weights_bp, url_prefix='/load-weights')

@app.route('/')
def home():
    return "Welcome to ProFT API!"

if __name__ == '__main__':
    os.makedirs(app.instance_path, exist_ok=True)
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)


