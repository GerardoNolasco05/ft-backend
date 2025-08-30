from db import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app
import jwt
from datetime import datetime, timedelta

class Coach(db.Model):
    __tablename__ = 'coaches'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    profile_name = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.String(128), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    time_zone = db.Column(db.String(100), nullable=False)
    training_speciality = db.Column(db.String(100), nullable=False)

    # One coach to many clients
    clients = db.relationship('Client', backref='coach', lazy=True)

    @property
    def password(self):
        raise AttributeError("Password is write-only.")

    @password.setter
    def password(self, plain_password):
        self.password_hash = generate_password_hash(plain_password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_token(self, expires_in=3600):
        payload = {
            'coach_id': self.id,
            'exp': datetime.utcnow() + timedelta(seconds=expires_in)
        }
        return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_token(token):
        try:
            payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            return payload['coach_id']
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'last_name': self.last_name,
            'profile_name': self.profile_name,
            'phone': self.phone,
            'email': self.email,
            'city': self.city,
            'time_zone': self.time_zone,
            'training_speciality': self.training_speciality,
            'clients': [client.id for client in self.clients]
        }
