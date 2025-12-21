from __future__ import annotations

from itertools import combinations
from typing import Iterable, List, Sequence, Tuple

MAX_LIKERT_SPREAD = 4.0
MIXED_GENDER_PENALTY = 500.0
HARD_CONSTRAINT_PENALTY = 1_000_000.0

# Pair weights aligned with KMeans weights (weights.py)
# Feature order: [introversion, sleep, cleanliness, noise, year, major]
PAIR_WEIGHTS = {
    "introversion": 3.0,
    "sleep": 2.5,
    "cleanliness": 2.0,
    "noise": 1.5,
    "year": 0.1,
    "major": 0.1,
}


class StudentProfileProtocol:
    id: int
    gender: str
    introversion_score: int
    sleep_schedule_score: int
    cleanliness_score: int
    noise_tolerance: int
    smoking: bool
    year: int
    major: str


class RoomProfileProtocol:
    id: int
    capacity: int
    gender_restriction: str | None
    noise_level: float


def pair_compatibility_cost(a: StudentProfileProtocol, b: StudentProfileProtocol) -> float:
    # Continuous features (normalized to 0-1 from 1-5 scale)
    sleep_diff = abs(a.sleep_schedule_score - b.sleep_schedule_score) / MAX_LIKERT_SPREAD
    intro_diff = abs(a.introversion_score - b.introversion_score) / MAX_LIKERT_SPREAD
    clean_diff = abs(a.cleanliness_score - b.cleanliness_score) / MAX_LIKERT_SPREAD
    noise_diff = abs(a.noise_tolerance - b.noise_tolerance) / MAX_LIKERT_SPREAD
    year_penalty = 0.0 if a.year == b.year else 1.0
    major_penalty = 0.0 if (a.major or "").strip().lower() == (b.major or "").strip().lower() else 1.0

    return (
        PAIR_WEIGHTS["introversion"] * intro_diff
        + PAIR_WEIGHTS["sleep"] * sleep_diff
        + PAIR_WEIGHTS["cleanliness"] * clean_diff
        + PAIR_WEIGHTS["noise"] * noise_diff
        + PAIR_WEIGHTS["year"] * year_penalty
        + PAIR_WEIGHTS["major"] * major_penalty
    )


def room_constraint_penalty(room: RoomProfileProtocol, students: Sequence[StudentProfileProtocol]) -> float:
    penalty = 0.0

    if len(students) > room.capacity:
        penalty += (len(students) - room.capacity) * 150.0

    if room.gender_restriction:
        g_restriction = room.gender_restriction.lower()
        if any(student.gender.lower() != g_restriction for student in students):
            return HARD_CONSTRAINT_PENALTY

    unique_genders = {student.gender.lower() for student in students}
    if len(unique_genders) > 1:
        return HARD_CONSTRAINT_PENALTY

    unique_smoking = {student.smoking for student in students}
    if len(unique_smoking) > 1:
        return HARD_CONSTRAINT_PENALTY
    return penalty


def calculate_room_cost(room: RoomProfileProtocol, students: Sequence[StudentProfileProtocol]) -> float:
    constraint_penalty = room_constraint_penalty(room, students)
    if constraint_penalty >= HARD_CONSTRAINT_PENALTY or len(students) < 2:
        return constraint_penalty

    pair_cost = 0.0
    pair_count = 0
    for student_a, student_b in combinations(students, 2):
        pair_cost += pair_compatibility_cost(student_a, student_b)
        pair_count += 1

    avg_pair_cost = pair_cost / pair_count if pair_count else 0.0
    return avg_pair_cost + constraint_penalty


def calculate_state_cost(state: Iterable[Tuple[RoomProfileProtocol, List[StudentProfileProtocol]]]) -> float:
    total = 0.0
    for room, occupants in state:
        total += calculate_room_cost(room, occupants)
    return total
