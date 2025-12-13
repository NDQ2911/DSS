from flask import Blueprint, abort, g, jsonify

from ..services import analytics

analytics_bp = Blueprint("analytics", __name__, url_prefix="/analytics")


def _get_db():
    db = getattr(g, "db", None)
    if db is None:
        abort(500, description="Database session not initialized")
    return db


@analytics_bp.route("/assignment-map", methods=["GET"])
def assignment_map():
    db = _get_db()
    data = analytics.build_assignment_tree(db)
    return jsonify(data)


@analytics_bp.route("/summary", methods=["GET"])
def summary():
    db = _get_db()
    data = analytics.summarize_conflicts(db)
    return jsonify(data)
