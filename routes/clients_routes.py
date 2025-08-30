# clients_routes.py

from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from db import db
from models.client_model import Client
from models.coach_model import Coach  # to validate coach_id exists
from utils.timezone_utils import get_time_zone_for_city

clients_bp = Blueprint("clients", __name__, url_prefix="/clients")


# ---------- helpers ----------

def _json():
    return request.get_json(silent=True) or {}

def _client_to_dict(c: Client) -> dict:
    if hasattr(c, "to_dict") and callable(getattr(c, "to_dict")):
        return c.to_dict()
    # Fallback if your model lacks to_dict()
    return {
        "id": c.id,
        "name": c.name,
        "last_name": c.last_name,
        "profile_name": c.profile_name,
        "phone": c.phone,
        "email": c.email,
        "city": c.city,
        "time_zone": c.time_zone,
        "coach_id": c.coach_id,
    }


# ---------- create ----------

@clients_bp.route("/", methods=["POST"])
def create_client():
    """
    Create a client.
    Auto-derives time_zone from city.
    Prevents duplicate email/profile_name with 409 responses.
    """
    data = _json()

    required = ["name", "last_name", "profile_name", "phone", "email", "city", "coach_id"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    # normalize user-facing identifiers to avoid sneaky duplicates
    data["profile_name"] = data["profile_name"].strip()

    # validate coach exists
    coach = Coach.query.get(data["coach_id"])
    if not coach:
        return jsonify({"error": f"Coach {data['coach_id']} not found"}), 404

    # derive time zone from city
    tz = get_time_zone_for_city(data["city"])
    if not tz:
        return jsonify({"error": f"Unknown city '{data['city']}' – cannot determine time zone"}), 400

    # pre-check duplicates for nice UX (DB constraint is still the source of truth)
    if Client.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email already exists"}), 409
    if Client.query.filter_by(profile_name=data["profile_name"]).first():
        return jsonify({"error": "Profile name already exists"}), 409

    c = Client(
        name=data["name"],
        last_name=data["last_name"],
        profile_name=data["profile_name"],
        phone=data["phone"],
        email=data["email"],
        city=data["city"],
        time_zone=tz,           # <-- auto-set
        coach_id=data["coach_id"]
    )

    try:
        db.session.add(c)
        db.session.commit()
    except IntegrityError as ie:
        db.session.rollback()
        msg = str(getattr(ie, "orig", ie)).lower()
        if "email" in msg:
            return jsonify({"error": "Email already exists"}), 409
        if "profile_name" in msg:
            return jsonify({"error": "Profile name already exists"}), 409
        if "foreign key" in msg and "coach" in msg:
            return jsonify({"error": f"Coach {data['coach_id']} not found"}), 404
        return jsonify({"error": "Constraint failed"}), 400

    return jsonify(_client_to_dict(c)), 201


# ---------- list ----------

@clients_bp.route("/", methods=["GET"])
def list_clients():
    """
    List clients.
      - ?coach_id=7
      - ?search=ana
      - ?limit=50&offset=0
      - ?include_counts=1   -> adds workouts_count via efficient aggregation (optional)
    """
    q = Client.query

    coach_id = request.args.get("coach_id", type=int)
    if coach_id is not None:
        q = q.filter(Client.coach_id == coach_id)

    search = request.args.get("search", type=str)
    if search:
        like = f"%{search.strip()}%"
        q = q.filter(
            db.or_(
                Client.name.ilike(like),
                Client.last_name.ilike(like),
                Client.profile_name.ilike(like),
                Client.email.ilike(like),
                Client.city.ilike(like),
            )
        )

    limit = max(1, min(request.args.get("limit", default=50, type=int), 200))
    offset = max(0, request.args.get("offset", default=0, type=int))
    include_counts = request.args.get("include_counts", default=0, type=int) == 1

    if include_counts:
        # if your model has a Workout FK, this computes counts without loading all rows
        from models.workout_model import Workout  # local import to avoid circulars
        rows = (
            db.session.query(Client, func.count(Workout.id).label("workouts_count"))
            .outerjoin(Workout, Workout.client_id == Client.id)
            .group_by(Client.id)
            .order_by(Client.id.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        items = []
        for client, workouts_count in rows:
            d = _client_to_dict(client)
            d["workouts_count"] = int(workouts_count or 0)
            items.append(d)
        return jsonify(items), 200

    clients = q.order_by(Client.id.desc()).offset(offset).limit(limit).all()
    return jsonify([_client_to_dict(c) for c in clients]), 200


# ---------- read ----------

@clients_bp.route("/<int:client_id>", methods=["GET"])
def get_client(client_id: int):
    c = Client.query.get_or_404(client_id)
    return jsonify(_client_to_dict(c)), 200


# ---------- update ----------

@clients_bp.route("/<int:client_id>", methods=["PUT", "PATCH"])
def update_client(client_id: int):
    """
    Update client. If city changes, time_zone is re-derived automatically.
    Blocks changing email/profile_name to duplicates.
    """
    c = Client.query.get_or_404(client_id)
    data = _json()

    if request.method == "PUT":
        required = ["name", "last_name", "profile_name", "phone", "email", "city", "coach_id"]
        missing = [f for f in required if not data.get(f)]
        if missing:
            return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    # normalize profile name if provided
    if "profile_name" in data and data["profile_name"]:
        data["profile_name"] = data["profile_name"].strip()

    # handle duplicates on change
    if "email" in data and data["email"] != c.email:
        if Client.query.filter_by(email=data["email"]).first():
            return jsonify({"error": "Email already exists"}), 409

    if "profile_name" in data and data["profile_name"] != c.profile_name:
        if Client.query.filter_by(profile_name=data["profile_name"]).first():
            return jsonify({"error": "Profile name already exists"}), 409

    # if coach_id changes, validate new coach
    if "coach_id" in data and data["coach_id"] != c.coach_id:
        new_coach = Coach.query.get(data["coach_id"])
        if not new_coach:
            return jsonify({"error": f"Coach {data['coach_id']} not found"}), 404
        c.coach_id = data["coach_id"]

    # set basic fields safely
    for field in ["name", "last_name", "profile_name", "phone", "email", "city"]:
        if field in data and data[field] is not None:
            setattr(c, field, data[field])

    # re-derive time zone if city changed
    if "city" in data:
        tz = get_time_zone_for_city(c.city)
        if not tz:
            return jsonify({"error": f"Unknown city '{c.city}' – cannot determine time zone"}), 400
        c.time_zone = tz

    try:
        db.session.commit()
    except IntegrityError as ie:
        db.session.rollback()
        msg = str(getattr(ie, "orig", ie)).lower()
        if "email" in msg:
            return jsonify({"error": "Email already exists"}), 409
        if "profile_name" in msg:
            return jsonify({"error": "Profile name already exists"}), 409
        if "foreign key" in msg and "coach" in msg:
            return jsonify({"error": "Coach not found"}), 404
        return jsonify({"error": "Constraint failed"}), 400

    return jsonify(_client_to_dict(c)), 200


# ---------- delete ----------

@clients_bp.route("/<int:client_id>", methods=["DELETE"])
def delete_client(client_id: int):
    c = Client.query.get_or_404(client_id)
    db.session.delete(c)
    db.session.commit()
    return jsonify({"status": "deleted", "id": client_id}), 200
