# exercises-routes.py
from flask import Blueprint, jsonify, request, abort
from models.exercise_model import Exercise
from models.load_weight_model import LoadWeight

exercises_bp = Blueprint('exercises', __name__, url_prefix='/exercises')


@exercises_bp.route('/', methods=['GET'])
def list_exercises():
    # minimal list for index / navigation
    rows = Exercise.query.with_entities(
        Exercise.id, Exercise.name, Exercise.load_type_id
    ).all()
    return jsonify([
        {'id': r.id, 'name': r.name, 'load_type_id': r.load_type_id}
        for r in rows
    ]), 200


@exercises_bp.route('/<int:exercise_id>', methods=['GET'])
def get_exercise(exercise_id: int):
    """
    Full detail for a single exercise.
    Prefer Exercise.to_dict() if the model defines it; otherwise build a rich dict.
    """
    ex = Exercise.query.get_or_404(exercise_id)

    # If your model already has a serializer, use it
    if hasattr(ex, "to_dict") and callable(getattr(ex, "to_dict")):
        data = ex.to_dict()
        return jsonify(data), 200

    # Fallback serializer (covers common fields + many-to-many names)
    def pick(obj, *fields):
        out = {}
        for f in fields:
            out[f] = getattr(obj, f, None)
        return out

    def names(seq):
        try:
            return [{'id': x.id, 'name': getattr(x, 'name', None)} for x in (seq or [])]
        except Exception:
            return []

    data = {
        'id': ex.id,
        'name': ex.name,
        # simple fields (adjust names if your model differs)
        **pick(ex,
               'movement_category',
               'body_part',
               'movement_pattern',
               'resistance_modality',
               'training_type',
               'muscle_action',
               'joint_involvement',
               'plane_of_motion',    # try to include both spellings
        ),
        'plane_motion': getattr(ex, 'plane_motion', None),  # some models use this name
        'image_url': getattr(ex, 'image_url', None),

        # related single object
        'load_type': (
            {'id': ex.load_type.id, 'name': ex.load_type.name}
            if getattr(ex, 'load_type', None) else None
        ),

        # many-to-many collections (adjust attribute names if different in your model)
        'primary_muscles':   names(getattr(ex, 'primary_muscles',   [])),
        'secondary_muscles': names(getattr(ex, 'secondary_muscles', [])),
        'muscular_groups':   names(getattr(ex, 'muscular_groups',   [])),
        'joint_actions':     names(getattr(ex, 'joint_actions',     [])),
        'equipments':        names(getattr(ex, 'equipments',        [])),
    }
    return jsonify(data), 200


@exercises_bp.route('/<int:exercise_id>/weights', methods=['GET'])
def exercise_weights(exercise_id: int):
    unit = (request.args.get('unit') or 'kg').lower()
    if unit not in ('kg', 'lbs'):
        unit = 'kg'

    ex = Exercise.query.get_or_404(exercise_id)
    q = (
        LoadWeight.query
        .filter(LoadWeight.load_type_id == ex.load_type_id,
                LoadWeight.unit == unit)
        .order_by(LoadWeight.value.asc())
    )
    rows = q.all()
    return jsonify([{
        'id': w.id,
        'value': w.value,
        'unit': w.unit,
        'load_type_id': w.load_type_id
    } for w in rows]), 200

