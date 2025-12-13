# Dormitory Room Assignment DSS

A full-stack decision support system for assigning dormitory rooms using a simulated annealing (SA) optimizer. The backend is built with Flask + SQLAlchemy, while the frontend is a lightweight HTML/JS dashboard.

## Features

- CRUD APIs for students, rooms, and assignments (SQLite by default).
- Simulated annealing optimizer that balances compatibility traits and room constraints.
- Sample data auto-seeded on first run for quick demos.
- One-click student/room generators seeded with authentic Vietnamese names and majors.
- Analytics layer exposing assignment trees, KPIs, and conflict distributions.
- Modern dashboard UI with data-generation screen, optimization tab, and monitoring tab.

## Quickstart

```bash
# 1. Backend setup
cd backend
pip install -r requirements.txt
flask --app app run --debug --port 8000

# 2. Frontend (separate terminal)
cd ../frontend
python -m http.server 8080
```

Open <http://localhost:8080> to interact with the system. Use the **Data Generation** view to create students/rooms instantly, then hop to **Optimization & Dashboard** to run SA, inspect assignments grouped by block, and monitor KPIs via the conflict chart and critical-room list.

### API highlights

- `POST /generators/students` – bulk-generate realistic student records (Vietnamese names, birthdays, majors, Likert scores).
- `POST /generators/rooms` – auto-build dorm blocks/floors/rooms sized to host all registered students.
- `GET /analytics/assignment-map` – retrieve persisted assignments grouped by block → room → students.
- `GET /analytics/summary` – dashboard metrics (total students, avg conflict, fill rates, capacity, conflict buckets, critical rooms).

For deeper details, including architecture, database schema, and API references, see `instructions.md`.
