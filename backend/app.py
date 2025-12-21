from flask import Flask, g, jsonify
from flask_cors import CORS

from .database import SessionLocal, init_db
from .routers import (
    analytics_bp,
    assignments_bp,
    generators_bp,
    rooms_bp,
    students_bp,
)


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app, resources={r"*": {"origins": "*"}})

    init_db()

    @app.before_request
    def create_session():
        g.db = SessionLocal()

    @app.teardown_request
    def shutdown_session(exception=None):
        db = g.pop("db", None)
        if db is not None:
            if exception:
                db.rollback()
            db.close()

    app.register_blueprint(students_bp)
    app.register_blueprint(rooms_bp)
    app.register_blueprint(assignments_bp)
    app.register_blueprint(generators_bp)
    app.register_blueprint(analytics_bp)

    @app.get("/health")
    def healthcheck():
        return jsonify({"status": "ok"})

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
