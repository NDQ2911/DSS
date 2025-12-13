from __future__ import annotations

from itertools import combinations
from typing import Iterable, List, Sequence, Tuple

MAX_LIKERT_SPREAD = 4.0
MIXED_GENDER_PENALTY = 500.0

PAIR_WEIGHTS = {
    "introversion": 1.4,
    "sleep": 1.2,
    "cleanliness": 1.3,
    "noise": 1.1,
    "smoking": 2.0,
}


class StudentProfileProtocol:
    id: int
    gender: str
    introversion_score: int
    sleep_schedule_score: int
    cleanliness_score: int
    noise_tolerance: int
    smoking: bool


class RoomProfileProtocol:
    id: int
    capacity: int
    gender_restriction: str | None
    noise_level: float


def pair_compatibility_cost(a: StudentProfileProtocol, b: StudentProfileProtocol) -> float:
    sleep_diff = abs(a.sleep_schedule_score - b.sleep_schedule_score) / MAX_LIKERT_SPREAD
    intro_diff = abs(a.introversion_score - b.introversion_score) / MAX_LIKERT_SPREAD
    clean_diff = abs(a.cleanliness_score - b.cleanliness_score) / MAX_LIKERT_SPREAD
    noise_diff = abs(a.noise_tolerance - b.noise_tolerance) / MAX_LIKERT_SPREAD
    smoking_penalty = 0.0 if a.smoking == b.smoking else 1.0

    return (
        PAIR_WEIGHTS["sleep"] * sleep_diff
        + PAIR_WEIGHTS["introversion"] * intro_diff
        + PAIR_WEIGHTS["cleanliness"] * clean_diff
        + PAIR_WEIGHTS["noise"] * noise_diff
        + PAIR_WEIGHTS["smoking"] * smoking_penalty
    )


def room_constraint_penalty(room: RoomProfileProtocol, students: Sequence[StudentProfileProtocol]) -> float:
    penalty = 0.0

    if len(students) > room.capacity:
        penalty += (len(students) - room.capacity) * 150.0

    if room.gender_restriction:
        g_restriction = room.gender_restriction.lower()
        penalty += sum(50.0 for student in students if student.gender.lower() != g_restriction)

    unique_genders = {student.gender.lower() for student in students}
    if len(unique_genders) > 1:
        penalty += MIXED_GENDER_PENALTY

    if students:
        avg_noise = sum(s.noise_tolerance for s in students) / len(students)
        normalized_noise = avg_noise / 5.0
        penalty += abs(normalized_noise - room.noise_level) * 5.0

    return penalty


def calculate_room_cost(room: RoomProfileProtocol, students: Sequence[StudentProfileProtocol]) -> float:
    if len(students) < 2:
        return room_constraint_penalty(room, students)

    pair_cost = 0.0
    pair_count = 0
    for student_a, student_b in combinations(students, 2):
        pair_cost += pair_compatibility_cost(student_a, student_b)
        pair_count += 1

    avg_pair_cost = pair_cost / pair_count if pair_count else 0.0
    return avg_pair_cost + room_constraint_penalty(room, students)


def calculate_state_cost(state: Iterable[Tuple[RoomProfileProtocol, List[StudentProfileProtocol]]]) -> float:
    total = 0.0
    for room, occupants in state:
        total += calculate_room_cost(room, occupants)
    return total
