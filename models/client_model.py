from db import db

class Client(db.Model):
    __tablename__ = 'clients'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    profile_name = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(100), nullable=False)
    time_zone = db.Column(db.String(100), nullable=False)

    #Foreign key to Coach
    coach_id = db.Column(db.Integer, db.ForeignKey('coaches.id'), nullable=False)

    #Foreign key to Workouts
    workouts = db.relationship('Workout', back_populates='client', cascade='all, delete-orphan')


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
            'coach_id': self.coach_id,
            'workouts_count': len(self.workouts) if self.workouts is not None else 0
        }
