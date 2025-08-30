# coaches_routes.py
from flask import Blueprint, request, jsonify, current_app
from sqlalchemy.exc import IntegrityError
from functools import wraps

from db import db
from models.coach_model import Coach
from utils.timezone_utils import get_time_zone_for_city

coaches_bp = Blueprint("coaches", __name__, url_prefix="/coaches")  # added url_prefix


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if "Authorization" in request.headers:
            parts = request.headers["Authorization"].split(" ")
            if len(parts) == 2 and parts[0] == "Bearer":
                token = parts[1]

        if not token:
            return jsonify({"message": "Token is missing"}), 401

        coach_id = Coach.verify_token(token)
        if not coach_id:
            return jsonify({"message": "Invalid or expired token"}), 401

        coach = Coach.query.get(coach_id)
        if not coach:
            return jsonify({"message": "Coach not found"}), 404

        return f(coach, *args, **kwargs)
    return decorated


@coaches_bp.route("/", methods=["GET"])
def get_all_coaches():
    coaches = Coach.query.all()
    return jsonify([c.to_dict() for c in coaches]), 200


@coaches_bp.route("/<int:coach_id>", methods=["GET"])
def get_coach_by_id(coach_id):
    coach = Coach.query.get_or_404(coach_id)
    return jsonify(coach.to_dict()), 200


@coaches_bp.route("/<int:coach_id>/clients", methods=["GET"])
@token_required
def get_clients_for_coach(current_coach, coach_id):
    if current_coach.id != coach_id:
        return jsonify({"error": "Unauthorized access"}), 403
    return jsonify([client.to_dict() for client in current_coach.clients]), 200


@coaches_bp.route("/", methods=["POST"])
def register_coach():
    data = request.get_json() or {}

    required_fields = [
        "name", "last_name", "profile_name", "phone", "email",
        "password", "city", "training_speciality"
    ]
    missing = [f for f in required_fields if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    # Normalize profile_name if you want case-insensitive uniqueness behavior
    # (optional but recommended)
    data["profile_name"] = data["profile_name"].strip()

    # Pre-checks (fast, user-friendly)
    if Coach.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email already exists"}), 409
    if Coach.query.filter_by(profile_name=data["profile_name"]).first():
        return jsonify({"error": "Profile name already exists"}), 409

    time_zone = get_time_zone_for_city(data["city"])
    if not time_zone:
        return jsonify({"error": f"Unknown city '{data['city']}' – cannot determine time zone"}), 400

    try:
        coach = Coach(
            name=data["name"],
            last_name=data["last_name"],
            profile_name=data["profile_name"],
            phone=data["phone"],
            email=data["email"],
            city=data["city"],
            time_zone=time_zone,
            training_speciality=data["training_speciality"],
        )
        coach.password = data["password"]

        db.session.add(coach)
        db.session.commit()
        return jsonify(coach.to_dict()), 201

    except IntegrityError as ie:
        db.session.rollback()
        msg = str(getattr(ie, "orig", ie)).lower()
        if "email" in msg:
            return jsonify({"error": "Email already exists"}), 409
        if "profile_name" in msg or "uq_coaches_profile_name" in msg:
            return jsonify({"error": "Profile name already exists"}), 409
        return jsonify({"error": "Constraint failed"}), 400


@coaches_bp.route("/<int:coach_id>", methods=["PUT", "PATCH"])
def update_coach(coach_id):
    coach = Coach.query.get_or_404(coach_id)
    data = request.get_json() or {}

    if request.method == "PUT":
        required_fields = ["name", "last_name", "profile_name", "phone", "email", "city", "training_speciality"]
        missing = [f for f in required_fields if not data.get(f)]
        if missing:
            return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    # safe field updates
    for field in ["name", "last_name", "profile_name", "phone", "email", "city", "training_speciality"]:
        if field in data:
            setattr(coach, field, data[field])

    if "password" in data and data["password"]:
        coach.password = data["password"]  # re-hash

    if "city" in data:
        tz = get_time_zone_for_city(data["city"])
        if not tz:
            return jsonify({"error": f"Unknown city '{data['city']}' – cannot determine time zone"}), 400
        coach.time_zone = tz

    try:
        db.session.commit()
    except IntegrityError as ie:
        db.session.rollback()
        msg = str(getattr(ie, "orig", ie)).lower()
        if "email" in msg:
            return jsonify({"error": "Email already exists"}), 409
        if "profile_name" in msg:
            return jsonify({"error": "Profile name already exists"}), 409
        return jsonify({"error": "Constraint failed"}), 400

    return jsonify(coach.to_dict()), 200


@coaches_bp.route("/<int:coach_id>", methods=["DELETE"])
def delete_coach(coach_id):
    coach = Coach.query.get_or_404(coach_id)
    db.session.delete(coach)
    db.session.commit()
    return jsonify({"message": f"Coach {coach_id} deleted"}), 200


@coaches_bp.route("/login", methods=["POST"])
def login_coach():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    coach = Coach.query.filter_by(email=email).first()
    if coach and coach.check_password(password):
        token = coach.generate_token()
        return jsonify({
            "token": token,
            "coach_id": coach.id,
            "name": coach.name,
            "profile_name": coach.profile_name,  # handy for UI
        }), 200

    return jsonify({"error": "Invalid credentials"}), 401


@coaches_bp.route("/me", methods=["GET"])
@token_required
def get_my_profile(current_coach):
    return jsonify(current_coach.to_dict()), 200
