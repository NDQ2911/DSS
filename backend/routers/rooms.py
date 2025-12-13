from flask import Blueprint, abort, g, jsonify, request
from marshmallow import ValidationError

from .. import models
from ..schemas import RoomSchema

rooms_bp = Blueprint("rooms", __name__, url_prefix="/rooms")
room_schema = RoomSchema()
rooms_schema = RoomSchema(many=True)


def _get_db():
    db = getattr(g, "db", None)
    if db is None:
        abort(500, description="Database session not initialized")
    return db


@rooms_bp.route("/", methods=["GET"])
def list_rooms():
    db = _get_db()
    rooms = db.query(models.Room).order_by(models.Room.id).all()
    return jsonify(rooms_schema.dump(rooms))


@rooms_bp.route("/", methods=["POST"])
def create_room():
    payload = request.get_json(silent=True)
    if payload is None:
        abort(400, description="JSON body required")
    try:
        data = room_schema.load(payload)
    except ValidationError as exc:
        return jsonify({"errors": exc.messages}), 422

    db = _get_db()
    room = models.Room(**data)
    db.add(room)
    db.commit()
    db.refresh(room)
    return jsonify(room_schema.dump(room)), 201


@rooms_bp.route("/<int:room_id>", methods=["GET"])
def get_room(room_id: int):
    db = _get_db()
    room = db.get(models.Room, room_id)
    if not room:
        abort(404, description="Room not found")
    return jsonify(room_schema.dump(room))


@rooms_bp.route("/<int:room_id>", methods=["PUT"])
def update_room(room_id: int):
    payload = request.get_json(silent=True)
    if payload is None:
        abort(400, description="JSON body required")
    try:
        data = room_schema.load(payload, partial=True)
    except ValidationError as exc:
        return jsonify({"errors": exc.messages}), 422

    db = _get_db()
    room = db.get(models.Room, room_id)
    if not room:
        abort(404, description="Room not found")

    for field, value in data.items():
        setattr(room, field, value)

    db.commit()
    db.refresh(room)
    return jsonify(room_schema.dump(room))


@rooms_bp.route("/<int:room_id>", methods=["DELETE"])
def delete_room(room_id: int):
    db = _get_db()
    room = db.get(models.Room, room_id)
    if not room:
        abort(404, description="Room not found")

    db.delete(room)
    db.commit()
    return ("", 204)
