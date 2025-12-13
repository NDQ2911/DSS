from flask import Blueprint, abort, g, jsonify, request
from marshmallow import ValidationError

from ..services import generation
from ..schemas import RoomGenerationSchema, StudentGenerationSchema


def _get_db():
    db = getattr(g, "db", None)
    if db is None:
        abort(500, description="Database session not initialized")
    return db


generators_bp = Blueprint("generators", __name__, url_prefix="/generators")
student_generation_schema = StudentGenerationSchema()
room_generation_schema = RoomGenerationSchema()


@generators_bp.route("/students", methods=["POST"])
def generate_students():
    payload = request.get_json(silent=True) or {}
    try:
        params = student_generation_schema.load(payload)
    except ValidationError as exc:
        return jsonify({"errors": exc.messages}), 422

    db = _get_db()
    summary = generation.generate_students(db, **params)
    return jsonify(summary), 201


@generators_bp.route("/rooms", methods=["POST"])
def generate_rooms():
    payload = request.get_json(silent=True) or {}
    try:
        params = room_generation_schema.load(payload)
    except ValidationError as exc:
        return jsonify({"errors": exc.messages}), 422

    db = _get_db()
    summary = generation.generate_rooms(db, **params)
    return jsonify(summary), 201
