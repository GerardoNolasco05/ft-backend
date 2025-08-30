from db import db

class JointAction(db.Model):
    __tablename__ = 'joint_actions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
   

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,     
        }