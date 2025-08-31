# routes/load_weights_routes.py
from flask import Blueprint, request, jsonify
from sqlalchemy.orm import joinedload
from models.load_weight_model import LoadWeight
from models.exercise_model import Exercise

load_weights_bp = Blueprint('load_weights', __name__, url_prefix='/load-weights')

def normalize_unit(u: str) -> str:
    if not u:
        return 'kg'
    u = u.lower().strip()
    return 'kg' if u not in ('kg', 'lbs') else u

def paginate(query, page: int, page_size: int):
    items = (query
             .offset((page - 1) * page_size)
             .limit(page_size)
             .all())
    return items

@load_weights_bp.route('/', methods=['GET'])
def list_load_weights():
    """
    GET /load-weights/?unit=kg|lbs&load_type_id=<int>&page=1&page_size=500
    Returns load weights ordered ascending.
    """
    unit = normalize_unit(request.args.get('unit'))
    load_type_id = request.args.get('load_type_id', type=int)

    # pagination (optional)
    try:
        page = max(int(request.args.get("page", 1)), 1)
    except ValueError:
        page = 1
    try:
        page_size = max(min(int(request.args.get("page_size", 500)), 2000), 1)
    except ValueError:
        page_size = 500

    q = LoadWeight.query.filter(LoadWeight.unit == unit)
    if load_type_id:
        q = q.filter(LoadWeight.load_type_id == load_type_id)

    q = q.order_by(LoadWeight.value.asc())
    rows = paginate(q, page, page_size)

    return jsonify([
        {'id': r.id, 'value': r.value, 'unit': r.unit, 'load_type_id': r.load_type_id}
        for r in rows
    ]), 200

@load_weights_bp.route('/by-exercise/<int:exercise_id>/', methods=['GET'])
def list_load_weights_by_exercise(exercise_id: int):
    """
    GET /load-weights/by-exercise/<exercise_id>/?unit=kg|lbs&page=1&page_size=500
    Resolves the exercise's load_type_id automatically and returns matching weights.
    """
    unit = normalize_unit(request.args.get('unit'))

    ex = (Exercise.query
          .options(joinedload(Exercise.load_type))
          .get_or_404(exercise_id))

    if not ex.load_type_id:
        return jsonify({'error': 'Exercise has no load_type_id'}), 400

    # pagination (optional)
    try:
        page = max(int(request.args.get("page", 1)), 1)
    except ValueError:
        page = 1
    try:
        page_size = max(min(int(request.args.get("page_size", 500)), 2000), 1)
    except ValueError:
        page_size = 500

    q = (LoadWeight.query
         .filter(LoadWeight.unit == unit,
                 LoadWeight.load_type_id == ex.load_type_id)
         .order_by(LoadWeight.value.asc()))
    rows = paginate(q, page, page_size)

    return jsonify([
        {'id': r.id, 'value': r.value, 'unit': r.unit, 'load_type_id': r.load_type_id}
        for r in rows
    ]), 200
