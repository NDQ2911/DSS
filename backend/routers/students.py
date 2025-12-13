from flask import Blueprint, abort, g, jsonify, request
from marshmallow import ValidationError

from .. import models
from ..schemas import StudentSchema

students_bp = Blueprint("students", __name__, url_prefix="/students")
student_schema = StudentSchema()
students_schema = StudentSchema(many=True)


def _get_db():
    db = getattr(g, "db", None)
    if db is None:
        abort(500, description="Database session not initialized")
    return db


@students_bp.route("/", methods=["GET"])
def list_students():
    db = _get_db()
    students = db.query(models.Student).order_by(models.Student.id).all()
    return jsonify(students_schema.dump(students))


@students_bp.route("/", methods=["POST"])
def create_student():
    payload = request.get_json(silent=True)
    if payload is None:
        abort(400, description="JSON body required")
    try:
        data = student_schema.load(payload)
    except ValidationError as exc:
        return jsonify({"errors": exc.messages}), 422

    db = _get_db()
    student = models.Student(**data)
    db.add(student)
    db.commit()
    db.refresh(student)
    return jsonify(student_schema.dump(student)), 201


@students_bp.route("/<int:student_id>", methods=["GET"])
def get_student(student_id: int):
    db = _get_db()
    student = db.get(models.Student, student_id)
    if not student:
        abort(404, description="Student not found")
    return jsonify(student_schema.dump(student))


@students_bp.route("/<int:student_id>", methods=["PUT"])
def update_student(student_id: int):
    payload = request.get_json(silent=True)
    if payload is None:
        abort(400, description="JSON body required")
    try:
        data = student_schema.load(payload, partial=True)
    except ValidationError as exc:
        return jsonify({"errors": exc.messages}), 422

    db = _get_db()
    student = db.get(models.Student, student_id)
    if not student:
        abort(404, description="Student not found")

    for field, value in data.items():
        setattr(student, field, value)

    db.commit()
    db.refresh(student)
    return jsonify(student_schema.dump(student))


@students_bp.route("/<int:student_id>", methods=["DELETE"])
def delete_student(student_id: int):
    db = _get_db()
    student = db.get(models.Student, student_id)
    if not student:
        abort(404, description="Student not found")

    db.delete(student)
    db.commit()
    return ("", 204)
