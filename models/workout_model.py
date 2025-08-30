# models/workout_model.py
from db import db
from datetime import datetime

class Workout(db.Model):
    """
    Workout model represents a complete workout entry tied to a specific exercise.
    It stores key metrics like weight, tempo, TUT (time under tension), rest, and density.
    """
    __tablename__ = 'workouts'

    id = db.Column(db.Integer, primary_key=True)

    exercise_id = db.Column(db.Integer, db.ForeignKey('exercises.id'), nullable=False)
    exercise = db.relationship('Exercise')

    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    client = db.relationship('Client', back_populates='workouts')

    # (Added sensible defaults for a smoother DX – optional)
    units = db.Column(db.String(10), nullable=False, default="kg")

    rm = db.Column(db.Integer, nullable=False)
    rm_percentage = db.Column(db.Integer, nullable=False)
    max_repetitions = db.Column(db.Integer, nullable=False)
    rir_repetitions = db.Column(db.Integer, nullable=False)

    cc_tempo = db.Column(db.Integer, nullable=False)
    iso_tempo_one = db.Column(db.Integer, nullable=False)
    ecc_tempo = db.Column(db.Integer, nullable=False)
    iso_tempo_two = db.Column(db.Integer, nullable=False)

    reps = db.Column(db.Integer, nullable=False)
    sets = db.Column(db.Integer, nullable=False)
    exercise_time = db.Column(db.Integer, nullable=False, default=0)
    rom = db.Column(db.Integer, nullable=False)

    weight = db.Column(db.Integer, nullable=False)
    repetitions = db.Column(db.Integer, nullable=False)
    total_tempo = db.Column(db.Integer, nullable=False)
    tut = db.Column(db.Integer, nullable=False)
    total_rest = db.Column(db.Integer, nullable=False)

    density = db.Column(db.Float, nullable=False, default=0.0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "exercise_id": self.exercise_id,
            "exercise_name": self.exercise.name if self.exercise else None,
            "client_id": self.client_id,
            "units": self.units,
            "rm": self.rm,
            "rm_percentage": self.rm_percentage,
            "max_repetitions": self.max_repetitions,
            "rir_repetitions": self.rir_repetitions,
            "cc_tempo": self.cc_tempo,
            "iso_tempo_one": self.iso_tempo_one,
            "ecc_tempo": self.ecc_tempo,
            "iso_tempo_two": self.iso_tempo_two,
            "reps": self.reps,
            "sets": self.sets,
            "exercise_time": self.exercise_time,
            "rom": self.rom,
            "weight": self.weight,
            "repetitions": self.repetitions,
            "total_tempo": self.total_tempo,
            "tut": self.tut,
            "total_rest": self.total_rest,
            "density": self.density,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
