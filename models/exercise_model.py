from db import db
from models.association_model import (
    exercise_primary_muscle,
    exercise_secondary_muscle,
    exercise_muscular_group,
    exercise_joint_action,
    exercise_equipment
)
from models.load_type_model import LoadType  # Ensure it's imported for clarity (optional)


class Exercise(db.Model):
    __tablename__ = 'exercises'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    load_type_id = db.Column(db.Integer, db.ForeignKey('load_types.id'), nullable=False)
    load_type = db.relationship('LoadType', backref='exercises')
    type_training = db.Column(db.String(100), nullable=False)
    movement_category = db.Column(db.String(100), nullable=False)
    body_part = db.Column(db.String(100), nullable=False)
    muscle_action = db.Column(db.String(100), nullable=False)
    movement_pattern = db.Column(db.String(100), nullable=False)
    plane_motion = db.Column(db.String(100), nullable=False)
    joint_involvement = db.Column(db.String(100), nullable=False)
    joint_position = db.Column(db.String(100), nullable=False)
    resistance_modality = db.Column(db.String(100), nullable=False)

    # many-to-many association tables
    muscular_groups = db.relationship(
        'MuscularGroup',
        secondary=exercise_muscular_group,
        backref='muscular_exercises'
    )

    primary_muscles = db.relationship(
        'Muscle',
        secondary=exercise_primary_muscle,
        backref='primary_exercises'
    )

    secondary_muscles = db.relationship(
        'Muscle', secondary=exercise_secondary_muscle,
        backref='secondary_exercises'
    )

    joint_actions = db.relationship(
        'JointAction', secondary=exercise_joint_action,
        backref='joint_actions_exercises')

    equipments = db.relationship(
        'Equipment', secondary=exercise_equipment,
        backref='equipment_exercises'
    )

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'load_type_id': self.load_type_id,
            'load_type': self.load_type.name if self.load_type else None,
            'type_training': self.type_training,
            'movement_category': self.movement_category,
            'body_part': self.body_part,
            'muscle_action': self.muscle_action,
            'movement_pattern': self.movement_pattern,
            'plane_motion': self.plane_motion,
            'joint_involvement': self.joint_involvement,
            'joint_position': self.joint_position,
            'resistance_modality': self.resistance_modality,

            'muscular_groups': [{'id': mg.id, 'name': mg.name} for mg in self.muscular_groups],
            'primary_muscles': [{'id': m.id, 'name': m.name} for m in self.primary_muscles],
            'secondary_muscles': [{'id': m.id, 'name': m.name} for m in self.secondary_muscles],
            'equipments': [{'id': eq.id, 'name': eq.name} for eq in self.equipments],
            'joint_actions': [{'id': ja.id, 'name': ja.name} for ja in self.joint_actions],
        }
