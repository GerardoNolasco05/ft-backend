from db import db


class LoadType(db.Model):
    __tablename__ = 'load_types'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    weights = db.relationship('LoadWeight', backref='load_type', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
        }