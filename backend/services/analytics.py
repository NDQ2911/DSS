from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from .. import models
from ..optimizer.cost import calculate_room_cost
from ..optimizer.sa import RoomProfile, StudentProfile

COST_BUCKETS = [(0, 2), (2, 4), (4, 6), (6, 8), (8, None)]
CRITICAL_COST_THRESHOLD = 4.0


@dataclass
class RoomAnalytics:
    room_code: str
    building: str
    floor: int
    capacity: int
    occupancy: int
    gender: str | None
    conflict_score: float


def _student_profile(student: models.Student) -> StudentProfile:
    return StudentProfile(
        id=student.id,
        gender=student.gender,
        introversion_score=int(student.introversion_score or 3),
        sleep_schedule_score=int(getattr(student, "sleep_schedule_score", 3) or 3),
        cleanliness_score=int(student.cleanliness_score or 3),
        noise_tolerance=int(student.noise_tolerance or 3),
        smoking=bool(student.smoking),
    )


def _room_profile(room: models.Room) -> RoomProfile:
    return RoomProfile(
        id=room.id,
        capacity=room.capacity,
        gender_restriction=room.gender_restriction,
        noise_level=room.noise_level,
    )


def _bucket_label(lower: float, upper: float | None) -> str:
    if upper is None:
        return f">= {lower:.0f}"
    return f"{lower:.0f} – {upper:.0f}"


def build_assignment_tree(db: Session) -> Dict[str, object]:
    rooms = (
        db.query(models.Room)
        .options(joinedload(models.Room.assignments).joinedload(models.Assignment.student))
        .order_by(models.Room.building, models.Room.floor, models.Room.room_code)
        .all()
    )

    blocks: Dict[str, Dict[str, object]] = {}
    for room in rooms:
        block = blocks.setdefault(
            room.building,
            {
                "building": room.building,
                "rooms": [],
            },
        )
        students_payload = [
            {
                "id": assignment.student.id,
                "name": assignment.student.name,
                "gender": assignment.student.gender,
                "major": assignment.student.major,
                "year": assignment.student.year,
                "smoking": assignment.student.smoking,
                "preferences": {
                    "introversion": int(assignment.student.introversion_score or 3),
                    "sleep_schedule": int(getattr(assignment.student, "sleep_schedule_score", 3) or 3),
                    "cleanliness": int(assignment.student.cleanliness_score or 3),
                    "noise_tolerance": int(assignment.student.noise_tolerance or 3),
                },
            }
            for assignment in sorted(room.assignments, key=lambda a: a.student.name)
        ]
        student_profiles = [_student_profile(a.student) for a in room.assignments]
        conflict_score = calculate_room_cost(_room_profile(room), student_profiles)
        room_code = room.room_code or f"{room.building}-{room.id}"
        block["rooms"].append(
            {
                "room_code": room_code,
                "building": room.building,
                "floor": room.floor,
                "capacity": room.capacity,
                "gender": room.gender_restriction,
                "occupancy": len(students_payload),
                "conflict_score": round(float(conflict_score), 3),
                "students": students_payload,
            }
        )

    return {
        "blocks": list(blocks.values()),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def summarize_conflicts(db: Session) -> Dict[str, object]:
    summary = build_assignment_tree(db)
    blocks = summary["blocks"]
    rooms_flat: List[Dict[str, object]] = [room for block in blocks for room in block["rooms"]]

    bucket_labels = [_bucket_label(*bucket) for bucket in COST_BUCKETS]
    bucket_counts = {label: 0 for label in bucket_labels}
    bucket_ranges = {label: bucket for label, bucket in zip(bucket_labels, COST_BUCKETS)}

    total_conflict = 0.0
    critical_rooms: List[Dict[str, object]] = []
    for room in rooms_flat:
        score = room["conflict_score"]
        total_conflict += score
        if score >= CRITICAL_COST_THRESHOLD or room["occupancy"] > room["capacity"]:
            critical_rooms.append({
                "room_code": room["room_code"],
                "score": score,
                "occupancy": room["occupancy"],
                "capacity": room["capacity"],
            })
        for label, (lower, upper) in bucket_ranges.items():
            if upper is None:
                if score >= lower:
                    bucket_counts[label] += 1
                    break
            elif lower <= score < upper:
                bucket_counts[label] += 1
                break

    rooms_evaluated = len(rooms_flat)
    total_students = db.query(func.count(models.Student.id)).scalar() or 0
    total_rooms = db.query(func.count(models.Room.id)).scalar() or 0
    rooms_filled = sum(1 for room in rooms_flat if room["occupancy"] > 0)
    total_capacity = db.query(func.coalesce(func.sum(models.Room.capacity), 0)).scalar() or 0

    return {
        "total_students": total_students,
        "avg_conflict_score": round(total_conflict / rooms_evaluated, 3) if rooms_evaluated else 0.0,
        "rooms_filled": rooms_filled,
        "total_rooms": total_rooms,
        "total_capacity": total_capacity,
        "critical_rooms": sorted(critical_rooms, key=lambda item: item["score"], reverse=True)[:8],
        "conflict_distribution": [
            {"label": label, "rooms": bucket_counts[label]} for label in bucket_labels
        ],
        "generated_at": summary["generated_at"],
    }
