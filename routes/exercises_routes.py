# exercises_routes.py
from flask import Blueprint, jsonify, request
from sqlalchemy.orm import joinedload

from models.exercise_model import Exercise
from models.load_weight_model import LoadWeight

exercises_bp = Blueprint("exercises", __name__, url_prefix="/exercises")


def eager_options():
    """
    Eager-load all relationships we serialize to avoid N+1 queries.
    """
    return (
        joinedload(Exercise.load_type),
        joinedload(Exercise.muscular_groups),
        joinedload(Exercise.primary_muscles),
        joinedload(Exercise.secondary_muscles),
        joinedload(Exercise.joint_actions),
        joinedload(Exercise.equipments),
    )


@exercises_bp.route("/", methods=["GET"])
def list_exercises():
    """
    GET /exercises/            -> minimal list (id, name, load_type_id)
    GET /exercises/?full=1     -> full list with all fields (uses Exercise.to_dict)
    Optional: basic pagination ?page=1&page_size=50 (works for both modes)
    """
    full = (request.args.get("full") or "").lower() in ("1", "true", "yes")

    # pagination (optional)
    try:
        page = max(int(request.args.get("page", 1)), 1)
    except ValueError:
        page = 1
    try:
        page_size = max(min(int(request.args.get("page_size", 100)), 500), 1)
    except ValueError:
        page_size = 100

    query = Exercise.query
    if full:
        # only eager load when we need full objects
        for opt in eager_options():
            query = query.options(opt)

    # simple pagination
    items = (
        query.order_by(Exercise.id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    if full:
        return jsonify([e.to_dict() for e in items]), 200

    # minimal list for fast navigation
    return jsonify(
        [{"id": e.id, "name": e.name, "load_type_id": e.load_type_id} for e in items]
    ), 200


@exercises_bp.route("/<int:exercise_id>/", methods=["GET"])
def get_exercise(exercise_id: int):
    """
    Full detail for a single exercise (always full).
    """
    query = Exercise.query
    for opt in eager_options():
        query = query.options(opt)

    ex = query.get_or_404(exercise_id)
    return jsonify(ex.to_dict()), 200


@exercises_bp.route("/<int:exercise_id>/weights", methods=["GET"])
def exercise_weights(exercise_id: int):
    """
    GET /exercises/<id>/weights?unit=kg|lbs
    """
    unit = (request.args.get("unit") or "kg").lower()
    if unit not in ("kg", "lbs"):
        unit = "kg"

    # we only need load_type_id here; to keep it simple reuse the eager query
    query = Exercise.query
    for opt in eager_options():
        query = query.options(opt)
    ex = query.get_or_404(exercise_id)

    q = (
        LoadWeight.query
        .filter(LoadWeight.load_type_id == ex.load_type_id, LoadWeight.unit == unit)
        .order_by(LoadWeight.value.asc())
    )
    rows = q.all()
    return jsonify(
        [{"id": w.id, "value": w.value, "unit": w.unit, "load_type_id": w.load_type_id} for w in rows]
    ), 200

