# routes/workouts_routes.py
from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import BadRequest
from db import db
from models.workout_model import Workout
from models.client_model import Client

workouts_bp = Blueprint("workouts", __name__, url_prefix="/workouts")

# ---------- helpers ----------

def _json():
    """Return JSON body or {}. Raise 400 if invalid JSON."""
    try:
        data = request.get_json(silent=False)
        if data is None:
            raise BadRequest("Request body must be valid JSON (object, not array)")
        if isinstance(data, list):
            raise BadRequest("Request body must be a JSON object, not an array")
        return data
    except BadRequest as e:
        raise BadRequest(str(e))

def _model_to_dict(w: Workout) -> dict:
    if hasattr(w, "to_dict") and callable(getattr(w, "to_dict")):
        return w.to_dict()
    return {
        "id": w.id,
        "exercise_id": getattr(w, "exercise_id", None),
        "client_id": getattr(w, "client_id", None),
        "created_at": getattr(w, "created_at", None).isoformat() if getattr(w, "created_at", None) else None,
    }

def _set_attrs_from_payload(instance, payload, allowed_fields):
    for key in allowed_fields:
        if key in payload:
            setattr(instance, key, payload[key])

def _to_int(val, field, errors):
    """Coerce to int; record error if invalid/empty."""
    if val is None or val == "":
        errors.append(f"{field} is required and must be a number")
        return None
    try:
        return int(val)
    except (TypeError, ValueError):
        errors.append(f"{field} must be an integer")
        return None

def _to_float(val, field, errors):
    """Coerce to float; record error if invalid/empty."""
    if val is None or val == "":
        errors.append(f"{field} is required and must be a number")
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        errors.append(f"{field} must be a number")
        return None

def _compute_derived(data, errors):
    """
    Compute total_tempo, tut, total_rest, density from provided inputs.
    Mutates and returns the same dict.
    """
    # Coerce required atomic fields for formulas
    # (Do NOT return on error; collect all errors)
    cc = _to_int(data.get("cc_tempo"), "cc_tempo", errors)
    iso1 = _to_int(data.get("iso_tempo_one"), "iso_tempo_one", errors)
    ecc = _to_int(data.get("ecc_tempo"), "ecc_tempo", errors)
    iso2 = _to_int(data.get("iso_tempo_two"), "iso_tempo_two", errors)
    reps = _to_int(data.get("reps"), "reps", errors)
    sets = _to_int(data.get("sets"), "sets", errors)
    weight = _to_float(data.get("weight"), "weight", errors)

    # Some other required (NOT NULL) fields we should coerce too
    data["rm"] = _to_int(data.get("rm"), "rm", errors)
    data["rm_percentage"] = _to_int(data.get("rm_percentage"), "rm_percentage", errors)
    data["max_repetitions"] = _to_int(data.get("max_repetitions"), "max_repetitions", errors)
    data["rir_repetitions"] = _to_int(data.get("rir_repetitions"), "rir_repetitions", errors)
    data["exercise_time"] = _to_int(data.get("exercise_time", 0), "exercise_time", errors)
    data["rom"] = _to_int(data.get("rom"), "rom", errors)

    # Units: keep as-is but validate presence
    if not data.get("units"):
        errors.append("units is required")

    # If we already collected errors, still compute as best as possible to avoid None
    total_tempo = None if None in (cc, iso1, ecc, iso2) else (cc + iso1 + ecc + iso2)
    data["total_tempo"] = total_tempo if total_tempo is not None else data.get("total_tempo") or 0

    tut = None if None in (data["total_tempo"], reps, sets) else (data["total_tempo"] * reps * sets)
    data["tut"] = tut if tut is not None else data.get("tut") or 0

    # total_rest: allow caller to provide either total_rest directly OR rest_per_set
    rest_per_set = request.json.get("rest_per_set") if request.is_json else None
    if rest_per_set not in (None, ""):
        try:
            rps = int(rest_per_set)
            data["total_rest"] = max(0, (sets if sets is not None else 0) - 1) * rps
        except (TypeError, ValueError):
            errors.append("rest_per_set must be an integer if provided")
    else:
        # Coerce provided total_rest if present, else 0
        traw = data.get("total_rest", 0)
        try:
            data["total_rest"] = int(traw)
        except (TypeError, ValueError):
            errors.append("total_rest must be an integer")
            data["total_rest"] = 0

    # density
    denom = (data["tut"] or 0) + (data["total_rest"] or 0)
    data["density"] = round((weight or 0) * (reps or 0) * (sets or 0) / denom, 2) if denom > 0 else 0.0

    return data, errors


# ---------- field whitelists ----------
ALLOWED_CREATE_FIELDS = {
    "exercise_id",
    "client_id",
    "units",

    "rm",
    "rm_percentage",
    "max_repetitions",
    "rir_repetitions",

    "cc_tempo",
    "iso_tempo_one",
    "ecc_tempo",
    "iso_tempo_two",

    "reps",
    "sets",
    "exercise_time",
    "rom",

    "weight",
    "repetitions",

    # derived / computed server-side now
    "total_tempo",
    "tut",
    "total_rest",
    "density",

    # optional/extra fields
    "notes",
    "scheduled_for",
    "duration_sec",
    "rpe",
}
ALLOWED_UPDATE_FIELDS = ALLOWED_CREATE_FIELDS


# ---------- routes ----------

@workouts_bp.route("/", methods=["POST"])
def create_workout():
    data = _json()

    # Validate client exists
    client_id = data.get("client_id")
    if not client_id:
        return jsonify({"error": "client_id is required"}), 400
    client = Client.query.get(client_id)
    if not client:
        return jsonify({"error": f"Client {client_id} not found"}), 404

    # Validate exercise_id presence
    if "exercise_id" not in data or data.get("exercise_id") in (None, ""):
        return jsonify({"error": "exercise_id is required"}), 400

    # Coerce exercise_id
    try:
        data["exercise_id"] = int(data["exercise_id"])
    except (TypeError, ValueError):
        return jsonify({"error": "exercise_id must be an integer"}), 400

    # Compute derived & coerce all numerics
    errors = []
    data, errors = _compute_derived(data, errors)

    # Make sure repetitions (NOT NULL) is provided & numeric
    data["repetitions"] = _to_int(data.get("repetitions"), "repetitions", errors)

    # If any coercion/validation failed, return 400 with details
    if errors:
        return jsonify({"error": "Validation failed", "details": errors}), 400

    w = Workout()
    _set_attrs_from_payload(w, data, ALLOWED_CREATE_FIELDS)

    try:
        db.session.add(w)
        db.session.commit()
    except IntegrityError as ie:
        db.session.rollback()
        return jsonify({"error": "Invalid data or constraint failed", "details": str(ie.orig)}), 400

    return jsonify(_model_to_dict(w)), 201


@workouts_bp.route("/", methods=["GET"])
def list_workouts():
    q = Workout.query

    client_id = request.args.get("client_id", type=int)
    if client_id is not None:
        q = q.filter(Workout.client_id == client_id)

    exercise_id = request.args.get("exercise_id", type=int)
    if exercise_id is not None:
        q = q.filter(Workout.exercise_id == exercise_id)

    limit = request.args.get("limit", default=50, type=int)
    limit = max(1, min(limit, 200))
    offset = request.args.get("offset", default=0, type=int)
    offset = max(0, offset)

    items = q.order_by(Workout.id.desc()).offset(offset).limit(limit).all()
    return jsonify([_model_to_dict(w) for w in items]), 200


@workouts_bp.route("/<int:workout_id>", methods=["GET"])
def get_workout(workout_id: int):
    w = Workout.query.get_or_404(workout_id)
    return jsonify(_model_to_dict(w)), 200


@workouts_bp.route("/<int:workout_id>", methods=["PATCH", "PUT"])
def update_workout(workout_id: int):
    data = _json()
    w = Workout.query.get_or_404(workout_id)

    # if moving workout to a different client, validate it exists
    if "client_id" in data:
        new_client_id = data.get("client_id")
        try:
            new_client_id_int = int(new_client_id)
        except (TypeError, ValueError):
            return jsonify({"error": "client_id must be an integer"}), 400
        client = Client.query.get(new_client_id_int)
        if not client:
            return jsonify({"error": f"Client {new_client_id_int} not found"}), 404
        data["client_id"] = new_client_id_int

    # if exercise_id present, coerce
    if "exercise_id" in data:
        try:
            data["exercise_id"] = int(data["exercise_id"])
        except (TypeError, ValueError):
            return jsonify({"error": "exercise_id must be an integer"}), 400

    # If any of the dependent fields are present, recompute derived
    depends = {"cc_tempo","iso_tempo_one","ecc_tempo","iso_tempo_two","reps","sets","weight","total_rest","tut","total_tempo"}
    if any(k in data for k in depends) or any(k in data for k in ("rm","rm_percentage","max_repetitions","rir_repetitions","exercise_time","rom")):
        errors = []
        # Start with current DB values to allow partial PATCH
        merged = {
            "units": w.units,
            "rm": w.rm,
            "rm_percentage": w.rm_percentage,
            "max_repetitions": w.max_repetitions,
            "rir_repetitions": w.rir_repetitions,
            "cc_tempo": w.cc_tempo,
            "iso_tempo_one": w.iso_tempo_one,
            "ecc_tempo": w.ecc_tempo,
            "iso_tempo_two": w.iso_tempo_two,
            "reps": w.reps,
            "sets": w.sets,
            "exercise_time": w.exercise_time,
            "rom": w.rom,
            "weight": w.weight,
            "repetitions": w.repetitions,
            "total_tempo": w.total_tempo,
            "tut": w.tut,
            "total_rest": w.total_rest,
            "density": w.density,
        }
        merged.update(data)  # overlay new values
        merged, errors = _compute_derived(merged, errors)
        merged["repetitions"] = _to_int(merged.get("repetitions"), "repetitions", errors)
        if errors:
            return jsonify({"error": "Validation failed", "details": errors}), 400
        data = merged

    _set_attrs_from_payload(w, data, ALLOWED_UPDATE_FIELDS)

    try:
        db.session.commit()
    except IntegrityError as ie:
        db.session.rollback()
        return jsonify({"error": "Invalid data or constraint failed", "details": str(ie.orig)}), 400

    return jsonify(_model_to_dict(w)), 200


@workouts_bp.route("/<int:workout_id>", methods=["DELETE"])
def delete_workout(workout_id: int):
    w = Workout.query.get_or_404(workout_id)
    db.session.delete(w)
    db.session.commit()
    return jsonify({"status": "deleted", "id": workout_id}), 200


@workouts_bp.route("/by-client/<int:client_id>", methods=["GET"])
def list_workouts_by_client(client_id: int):
    Client.query.get_or_404(client_id)  # ensure client exists
    q = Workout.query.filter_by(client_id=client_id).order_by(Workout.id.desc())
    items = q.all()
    return jsonify([_model_to_dict(w) for w in items]), 200
