from typing import Dict

from flask import Blueprint, abort, g, jsonify, request
from marshmallow import ValidationError

from .. import models
from ..optimizer.sa import SimulatedAnnealingOptimizer
from ..optimizer.kmeans_assign import kmeans_room_assignment
from ..optimizer.weights import get_weight_dict
from ..schemas import AssignmentSchema, OptimizeParamsSchema

assignments_bp = Blueprint("assignments", __name__, url_prefix="/assignments")
assignment_schema = AssignmentSchema()
assignments_schema = AssignmentSchema(many=True)
optimize_params_schema = OptimizeParamsSchema()


def _get_db():
    db = getattr(g, "db", None)
    if db is None:
        abort(500, description="Database session not initialized")
    return db


@assignments_bp.route("/", methods=["GET"])
def list_assignments():
    db = _get_db()
    assignments = db.query(models.Assignment).order_by(models.Assignment.id).all()
    return jsonify(assignments_schema.dump(assignments))


@assignments_bp.route("/", methods=["POST"])
def create_assignment():
    payload = request.get_json(silent=True)
    if payload is None:
        abort(400, description="JSON body required")
    try:
        data = assignment_schema.load(payload)
    except ValidationError as exc:
        return jsonify({"errors": exc.messages}), 422

    db = _get_db()
    student = db.get(models.Student, data["student_id"])
    room = db.get(models.Room, data["room_id"])

    if not student or not room:
        abort(404, description="Student or room not found")

    existing = db.query(models.Assignment).filter_by(student_id=data["student_id"]).first()
    if existing:
        abort(400, description="Student already assigned to a room")

    if room.current_occupancy >= room.capacity:
        abort(400, description="Room is already full")

    assignment = models.Assignment(**data)
    db.add(assignment)
    room.current_occupancy += 1
    db.commit()
    db.refresh(assignment)
    return jsonify(assignment_schema.dump(assignment)), 201


@assignments_bp.route("/optimize", methods=["POST"])
def optimize_assignments():
    payload = request.get_json(silent=True)
    if payload is None:
        abort(400, description="JSON body required")
    try:
        params = optimize_params_schema.load(payload)
    except ValidationError as exc:
        return jsonify({"errors": exc.messages}), 422

    db = _get_db()
    students = db.query(models.Student).all()
    rooms = db.query(models.Room).order_by(models.Room.capacity.desc()).all()

    if not students:
        abort(400, description="No students available for optimization")
    if not rooms:
        abort(400, description="No rooms available for optimization")

    try:
        optimizer = SimulatedAnnealingOptimizer(
            students,
            rooms,
            initial_temperature=params["initial_temperature"],
            cooling_rate=params["cooling_rate"],
        )
        result = optimizer.optimize(iterations=params["iterations"])
    except ValueError as exc:
        abort(400, description=str(exc))

    db.query(models.Assignment).delete(synchronize_session=False)
    assignment_payload: Dict[int, int] = {}
    for room_id, student_ids in result["assignments"].items():
        assignment_payload[int(room_id)] = len(student_ids)
        for student_id in student_ids:
            db.add(models.Assignment(room_id=int(room_id), student_id=student_id))

    for room in rooms:
        room.current_occupancy = assignment_payload.get(room.id, 0)

    db.commit()

    response = {
        "best_cost": float(result["best_cost"]),
        "assignments": {room_id: ids for room_id, ids in result["assignments"].items()},
        "iterations": result["iterations"],
        "runtime_ms": result["runtime_ms"],
    }
    return jsonify(response)


@assignments_bp.route("/kmeans-optimize", methods=["POST"])
def kmeans_optimize_assignments():
    """Optimize assignments using k-means clustering."""
    db = _get_db()
    students = db.query(models.Student).all()
    rooms = db.query(models.Room).order_by(models.Room.capacity.desc()).all()

    if not students:
        abort(400, description="No students available for optimization")
    if not rooms:
        abort(400, description="No rooms available for optimization")

    try:
        assignments = kmeans_room_assignment(students, rooms)
    except (ValueError, RuntimeError) as exc:
        import traceback
        print(f"KMeans optimization error: {str(exc)}\n{traceback.format_exc()}")
        abort(400, description=str(exc))
    except Exception as exc:
        import traceback
        print(f"KMeans optimization error: {str(exc)}\n{traceback.format_exc()}")
        abort(500, description=f"Internal error: {str(exc)}")

    db.query(models.Assignment).delete(synchronize_session=False)
    occupancy_by_room: Dict[int, int] = {}
    for room_id, student_ids in assignments.items():
        occupancy_by_room[room_id] = len(student_ids)
        for student_id in student_ids:
            db.add(models.Assignment(room_id=room_id, student_id=student_id))

    for room in rooms:
        room.current_occupancy = occupancy_by_room.get(room.id, 0)

    db.commit()

    return jsonify(
        {
            "assignments": assignments,
            "strategy": "kmeans",
            "weights": get_weight_dict(),
        }
    )
