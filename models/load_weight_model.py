from db import db


class LoadWeight(db.Model):
    __tablename__ = 'load_weights'

    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Float, nullable=False)  # e.g., 2.5, 5.0
    unit = db.Column(db.String(10), nullable=False)  # 'kg' or 'lbs'
    load_type_id = db.Column(db.Integer, db.ForeignKey('load_types.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'value': self.value,
            'unit': self.unit,
            'load_type_id': self.load_type_id,
        }