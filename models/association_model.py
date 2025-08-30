from db import db

# Muscular group association table
exercise_muscular_group = db.Table(
    'exercise_muscular_group',
    db.Column('exercise_id', db.Integer, db.ForeignKey('exercises.id'), primary_key=True),
    db.Column('muscular_group_id', db.Integer, db.ForeignKey('muscular_groups.id'), primary_key=True),
    db.Column('mg_percentage', db.Float)
)

# Primary muscle association table
exercise_primary_muscle = db.Table(
    'exercise_primary_muscle',
    db.Column('exercise_id', db.Integer, db.ForeignKey('exercises.id'), primary_key=True),
    db.Column('muscle_id', db.Integer, db.ForeignKey('muscles.id'), primary_key=True),
    db.Column('pm_percentage', db.Float)
)

# Secondary muscle association table
exercise_secondary_muscle = db.Table(
    'exercise_secondary_muscle',
    db.Column('exercise_id', db.Integer, db.ForeignKey('exercises.id'), primary_key=True),
    db.Column('muscle_id', db.Integer, db.ForeignKey('muscles.id'), primary_key=True)
)


# Joint Action association table
exercise_joint_action = db.Table(
    'exercise_joint_action',
    db.Column('exercise_id', db.Integer, db.ForeignKey('exercises.id'), primary_key=True),
    db.Column('joint_action_id', db.Integer, db.ForeignKey('joint_actions.id'), primary_key=True)
)


# Equipment association table
exercise_equipment = db.Table(  
    'exercise_equipment',
    db.Column('exercise_id', db.Integer, db.ForeignKey('exercises.id'), primary_key=True),
    db.Column('equipment_id', db.Integer, db.ForeignKey('equipments.id'), primary_key=True),
)