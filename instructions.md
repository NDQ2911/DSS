# Dormitory Room Assignment DSS — Instruction Manual

## 1. Project Overview

This Decision Support System (DSS) assigns students to dormitory rooms using a **simulated annealing (SA)** metaheuristic.
The goal is to optimize multiple compatibility criteria while respecting capacity, gender restrictions, and room constraints.

Core components:

* **Backend:** Flask (Python) providing REST APIs, executing SA optimization, and storing data in a SQL database.
* **Frontend:** HTML/CSS/JavaScript for interacting with the backend.
* **Database:** SQLite (default) or PostgreSQL.

The system is designed to be simple, extensible, and suitable for academic or small-scale operational use.

---

## 2. System Architecture

### 2.1 High-Level Architecture

```text
Frontend (HTML/CSS/JS)
   └── API calls (REST, JSON)
Backend (Flask)
   ├── CRUD: Students / Rooms / Assignments
   ├── Simulated Annealing Optimizer
   └── SQL Database (SQLite/PostgreSQL)
```

### 2.2 Folder Structure

```text
project-root/
│
├── backend/
│   ├── app.py                # Flask entry point
│   ├── database.py           # DB engine, session, initialization
│   ├── models.py             # SQLAlchemy ORM models
│   ├── schemas.py            # Marshmallow request/response schemas
│   ├── routers/
│   │   ├── students.py
│   │   ├── rooms.py
│   │   └── assignments.py
│   ├── optimizer/
│   │   ├── sa.py             # Simulated annealing core
│   │   └── cost.py           # Cost function utilities
│   ├── sample_data/
│   │   ├── students.json
│   │   └── rooms.json
│   ├── requirements.txt
│   └── alembic/              # Optional migrations for PostgreSQL
│
├── frontend/
│   ├── index.html
│   ├── app.js                # API integration
│   ├── style.css
│   └── assets/
│
└── instruction.md
```

---

## 3. Database Schema

### 3.1 Students Table

| Column                | Type          | Description                                   |
| --------------------- | ------------- | --------------------------------------------- |
| id                    | UUID / INT PK | Unique student ID                             |
| name                  | TEXT          | Full name                                     |
| gender                | TEXT          | `male` / `female`                             |
| major                 | TEXT          | Academic major                                |
| birthday              | DATE          | Randomized between 2002-01-01 and 2007-12-31  |
| year                  | INT           | Year of study (1‑4)                           |
| introversion_score    | INT           | Likert 1 (extrovert) → 5 (introvert)          |
| sleep_schedule_score  | INT           | Likert 1 (sleep at 21h) → 5 (sleep at 2-3am)  |
| cleanliness_score     | INT           | Likert 1 (messy) → 5 (tidy daily)             |
| noise_tolerance       | INT           | Likert 1 (low tolerance) → 5 (festival proof) |
| smoking               | BOOLEAN       | Hard constraint for roommate compatibility    |
| additional_attributes | JSON          | Extra metadata (e.g., readable sleep window)  |

### 3.2 Rooms Table

| Column             | Type                      | Description                                      |
| ------------------ | ------------------------- | ------------------------------------------------ |
| id                 | UUID / INT PK             |                                                  |
| building           | TEXT                      | Block identifier (e.g., B1)                      |
| room_code          | TEXT (unique)             | Block-floor-room string (e.g., `B1-203`)         |
| floor              | INT                       | Floor number (1-indexed)                          |
| capacity           | INT                       | Allowed values: 6 / 8 / 10                        |
| gender_restriction | TEXT (nullable)           | `male`, `female`, or `NULL` (mixed)               |
| room_type          | TEXT                      | e.g., collective                                  |
| noise_level        | FLOAT (0–1)               | Preferred average noise tolerance (normalized)    |
| facilities         | JSON (wifi, AC, etc.)     |                                                  |
| current_occupancy  | INT                       | Updated automatically after optimization/generation |

### 3.3 Assignments Table

| Column     | Type            | Description |
| ---------- | --------------- | ----------- |
| id         | INT PK          |             |
| student_id | FK(students.id) |             |
| room_id    | FK(rooms.id)    |             |

---

## 4. Example Data

### 4.1 Students (JSON)

```json
[
  {
    "id": 1,
    "name": "Alice Nguyen",
    "gender": "female",
    "major": "Kỹ thuật Sinh học",
    "birthday": "2004-03-12",
    "year": 2,
    "introversion_score": 4,
    "sleep_schedule_score": 2,
    "cleanliness_score": 4,
    "noise_tolerance": 2,
    "smoking": false
  },
  {
    "id": 2,
    "name": "Bao Tran",
    "gender": "male",
    "major": "Khoa học Máy tính",
    "birthday": "2003-11-05",
    "year": 1,
    "introversion_score": 2,
    "sleep_schedule_score": 4,
    "cleanliness_score": 2,
    "noise_tolerance": 4,
    "smoking": true
  }
]
```

### 4.2 Rooms (JSON)

```json
[
  {
    "id": 101,
    "building": "B1",
    "room_code": "B1-201",
    "floor": 2,
    "capacity": 6,
    "gender_restriction": "female",
    "room_type": "collective",
    "noise_level": 0.3,
    "facilities": ["wifi", "AC"],
    "current_occupancy": 0
  },
  {
    "id": 102,
    "building": "C1",
    "room_code": "C1-305",
    "floor": 3,
    "capacity": 8,
    "gender_restriction": "male",
    "room_type": "collective",
    "noise_level": 0.5,
    "facilities": ["wifi"],
    "current_occupancy": 1
  }
]
```

---

## 5. Simulated Annealing for Multi-Criteria Room Assignment

### 5.1 State Representation

A state is:

```text
{
  room_id: [student_id, ...]
}
```

All students must appear exactly once.

### 5.2 Cost Function Components

The goal is **minimization**. Typical components:

1. **Compatibility penalties**

   * difference in introversion score
   * sleep schedule mismatch
   * noise tolerance differences
   * cleanliness mismatch
   * smoking conflicts

2. **Room constraint penalties**

   * gender violation
   * capacity overflow
   * room noise vs student tolerance mismatch

3. **Hard constraints** (heavily penalized)

   * invalid assignments (student assigned twice)
   * assigning to a full room

The cost is computed as:

```text
total_cost = compatibility_cost + constraint_cost
```

### 5.3 Temperature Schedule

Recommended exponential cooling:

```text
T0 = 1000
cooling_rate = 0.95
T_next = T * cooling_rate
```

### 5.4 Acceptance Probability

```text
p = exp(-Δ / T)
```

If `Δ < 0`, always accept.

### 5.5 Neighbor Generation

Randomly:

* Swap two students between rooms
* Move one student to another room
  Both options must maintain valid structure.

---

## 6. Setup Instructions

### 6.1 Backend Installation

```bash
cd backend
pip install -r requirements.txt
```

### 6.2 Database Initialization

SQLite (default):

```bash
python -m backend.database --init
```

PostgreSQL:

1. Update `DATABASE_URL` in `backend/database.py`.
2. Run migrations:

```bash
alembic upgrade head
```

### 6.3 Start Backend

```bash
uvicorn app:app --reload --port 8000
```

---

## 7. Frontend Setup

No build system required.

Open directly:

```bash
frontend/index.html
```

Or serve:

```bash
cd frontend
python -m http.server 8080
```

---

## 8. Running & Testing

* Use the **Data Generation** view (or the generator APIs) to seed students and rooms.
* Switch to **Optimization & Dashboard → Assignments** and click **Run Optimization**, or trigger the API:

  ```http
  POST /assignments/optimize
  ```

* Inspect results under the **Assignments** tab (grouped by block → room) and monitor KPIs via the **Dashboard** tab.
* All accepted assignments are persisted in the `assignments` table.

---

## 9. Customizing Parameters

Send in optimization request:

```json
{
  "initial_temperature": 1500,
  "cooling_rate": 0.90,
  "iterations": 5000
}
```

Or configure defaults in `optimizer/sa.py`.

---

## 10. API Documentation

Base URL: `http://localhost:8000`

### 10.1 Students

#### GET /students
Returns list of students.

#### POST /students

```json
{
  "name": "Test User",
  "gender": "female",
  "major": "Kỹ thuật Sinh học",
  "birthday": "2004-03-12",
  "year": 2,
  "introversion_score": 4,
  "sleep_schedule_score": 2,
  "cleanliness_score": 4,
  "noise_tolerance": 3,
  "smoking": false
}
```

#### PUT /students/{id}
Partial updates are supported.

#### DELETE /students/{id}

---

### 10.2 Rooms

#### GET /rooms
List every room.

#### POST /rooms

```json
{
  "building": "B1",
  "room_code": "B1-203",
  "floor": 2,
  "capacity": 8,
  "gender_restriction": "female",
  "room_type": "collective",
  "noise_level": 0.45,
  "facilities": ["wifi", "laundry"]
}
```

#### PUT /rooms/{id}
Update metadata such as facilities or gender restriction.

#### DELETE /rooms/{id}

---

### 10.3 Assignments

#### GET /assignments
Returns the flat student → room mapping (mainly for admin tooling).

---

### 10.4 Optimization

#### POST /assignments/optimize

```json
{
  "initial_temperature": 1000,
  "cooling_rate": 0.95,
  "iterations": 3000
}
```

#### Example response

```json
{
  "best_cost": 42.7,
  "assignments": {
    "B1-201": [1, 4],
    "C1-305": [2, 3]
  },
  "iterations": 3000,
  "runtime_ms": 512
}
```

### 10.5 Generators

#### POST /generators/students
Bulk-generate realistic Vietnamese student profiles using the seed lists under `backend/data/`.

```json
{
  "count": 800,
  "male_ratio": 0.55,
  "smoking_ratio": 0.1,
  "clear_existing": true
}
```

#### POST /generators/rooms
Create dorm inventory (blocks → floors → rooms) sized to host every student. Capacity choices must be a subset of `[6, 8, 10]`.

```json
{
  "target_students": 800,
  "blocks": 6,
  "floors_per_block": 6,
  "rooms_per_floor": 12,
  "capacity_choices": [6, 8, 10],
  "gender_strategy": "alternating",
  "clear_existing": true
}
```

### 10.6 Analytics

#### GET /analytics/assignment-map
Returns a hierarchical payload grouped by block → room → students. Each room also includes the latest conflict score computed from the optimizer cost function.

#### GET /analytics/summary
Returns dashboard KPIs (total students, average conflict, rooms filled vs. total rooms, capacity) plus the conflict-distribution buckets and top critical rooms list.

---

## 11. Extensibility Guidelines

* **New constraints:**
  Add to `optimizer/cost.py` with appropriate penalties.
* **New student attributes:**
  Add DB columns → update schema → cost function.
* **Large-scale datasets:**
  Migrate to PostgreSQL, enable indexing, batch neighbor generation.
* **Better optimization:**
  Replace SA with genetic algorithms, tabu search, or hybrid heuristics.

---

## 12. Known Limitations

* SA may converge to local minima; randomness affects results.
* JSON-based facilities/attributes require validation on the client.
* Not optimized for 10k+ students without adjusting neighbor search.
* No authentication or RBAC included.
* Frontend is minimal for demonstration purposes only.

---

## 13. Quickstart (This Repository)

1. **Install backend dependencies**

  ```bash
  cd backend
  pip install -r requirements.txt
  ```

1. **Run the Flask server** (auto-creates `dss.db` and seeds sample data)

  ```bash
  flask --app app run --debug --port 8000
  ```

1. **Launch the frontend**

  ```bash
  cd ../frontend
  python -m http.server 8080
  ```

1. **Open** `http://localhost:8080` and use the dashboard to manage students, rooms, and trigger the simulated annealing optimizer.
