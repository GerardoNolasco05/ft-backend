from flask import Blueprint, request, jsonify
from models.load_weight_model import LoadWeight

load_weights_bp = Blueprint('load_weights', __name__)

@load_weights_bp.route('/', methods=['GET'])
def list_load_weights():
    unit = request.args.get('unit', type=str)
    load_type_id = request.args.get('load_type_id', type=int)

    q = LoadWeight.query
    if unit:
        q = q.filter(LoadWeight.unit == unit.lower())
    if load_type_id:
        q = q.filter(LoadWeight.load_type_id == load_type_id)

    q = q.order_by(LoadWeight.value.asc())
    rows = q.all()
    return jsonify([{'id': r.id, 'value': r.value, 'unit': r.unit, 'load_type_id': r.load_type_id} for r in rows]), 200
