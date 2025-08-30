from db import db

class Muscle(db.Model):
    __tablename__ = 'muscles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
   

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,     
        }