from __future__ import annotations

import itertools
import random
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

from sqlalchemy.orm import Session

from .. import models

SEED_DIR = Path(__file__).resolve().parent.parent / "data"
BIRTHDAY_START = date(2002, 1, 1)
BIRTHDAY_END = date(2007, 12, 31)
LIKERT_MIN = 1
LIKERT_MAX = 5
SLEEP_WINDOWS = {
    1: "21:00 - 22:00",
    2: "22:00 - 23:00",
    3: "23:00 - 00:00",
    4: "00:00 - 01:00",
    5: "01:00 - 03:00",
}
BLOCK_LETTERS = [
    "A",
    "B",
    "C",
    "D",
    "E",
    "F",
    "G",
    "H",
    "J",
    "K",
    "L",
    "M",
    "N",
    "P",
    "Q",
    "R",
    "S",
    "T",
    "U",
]
FACILITIES = [
    "wifi",
    "laundry",
    "parking",
    "gym",
    "canteen",
    "study room",
    "air conditioning",
]


@dataclass
class StudentGenerationSummary:
    created: int
    total_students: int
    male_ratio: float
    female_ratio: float

    def as_dict(self) -> Dict[str, float]:
        return asdict(self)


@dataclass
class RoomGenerationSummary:
    rooms_created: int
    total_rooms: int
    total_capacity: int
    target_capacity: int

    def as_dict(self) -> Dict[str, int]:
        return asdict(self)


def _load_seed_list(filename: str) -> List[str]:
    path = SEED_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Seed file not found: {path}")
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _random_birthday() -> date:
    span_days = (BIRTHDAY_END - BIRTHDAY_START).days
    offset = random.randint(0, span_days)
    return BIRTHDAY_START + timedelta(days=offset)


def _random_score() -> int:
    return random.randint(LIKERT_MIN, LIKERT_MAX)


def _random_sleep_score() -> int:
    return random.randint(1, 5)


def _build_full_name(surnames: Sequence[str], names: Sequence[str]) -> str:
    total_words = random.randint(2, 4)
    surname = random.choice(surnames)
    middle_word_count = max(total_words - 2, 0)
    middle_words: List[str] = []
    for _ in range(middle_word_count):
        pool = random.choice([surnames, names])
        middle_words.append(random.choice(pool))
    given_name = random.choice(names)
    return " ".join([surname, *middle_words, given_name])


def generate_students(
    db: Session,
    *,
    count: int = 500,
    male_ratio: float = 0.5,
    smoking_ratio: float = 0.15,
    clear_existing: bool = True,
) -> Dict[str, float]:
    if count <= 0:
        raise ValueError("Count must be positive")
    male_ratio = min(max(male_ratio, 0.0), 1.0)
    smoking_ratio = min(max(smoking_ratio, 0.0), 1.0)

    surnames = _load_seed_list("surnames.txt")
    names = _load_seed_list("names.txt")
    majors = _load_seed_list("majors.txt")
    if not surnames or not names:
        raise ValueError("Names and surnames seed files must not be empty")

    if clear_existing:
        db.query(models.Assignment).delete(synchronize_session=False)
        db.query(models.Student).delete(synchronize_session=False)

    created = 0
    male_count = 0
    female_count = 0

    for _ in range(count):
        gender = "male" if random.random() < male_ratio else "female"
        if gender == "male":
            male_count += 1
        else:
            female_count += 1

        smoking = random.random() < smoking_ratio
        introversion = _random_score()
        cleanliness = _random_score()
        noise = _random_score()
        sleep_score = _random_sleep_score()

        student = models.Student(
            name=_build_full_name(surnames, names),
            gender=gender,
            major=random.choice(majors) if majors else None,
            birthday=_random_birthday(),
            year=random.randint(1, 4),
            introversion_score=introversion,
            cleanliness_score=cleanliness,
            noise_tolerance=noise,
            sleep_schedule_score=sleep_score,
            smoking=smoking,
            additional_attributes={
                "sleep_window": SLEEP_WINDOWS.get(sleep_score, "Not specified"),
            },
        )
        db.add(student)
        created += 1

    db.commit()

    total_students = db.query(models.Student).count()
    total = max(total_students, 1)
    summary = StudentGenerationSummary(
        created=created,
        total_students=total_students,
        male_ratio=male_count / total if total else 0.0,
        female_ratio=female_count / total if total else 0.0,
    )
    return summary.as_dict()


def _block_name_generator() -> Iterable[str]:
    letter_cycle = itertools.cycle(BLOCK_LETTERS)
    number = 1
    while True:
        letter = next(letter_cycle)
        yield f"{letter}{number}"
        if letter == BLOCK_LETTERS[-1]:
            number += 1


def _room_facilities() -> List[str]:
    count = random.randint(2, min(4, len(FACILITIES)))
    return random.sample(FACILITIES, count)


def generate_rooms(
    db: Session,
    *,
    target_students: int | None = None,
    blocks: int = 6,
    floors_per_block: int = 6,
    rooms_per_floor: int = 12,
    capacity_choices: Sequence[int] | None = None,
    clear_existing: bool = True,
    gender_strategy: str = "alternating",
) -> Dict[str, int]:
    if rooms_per_floor > 20:
        raise ValueError("rooms_per_floor cannot exceed 20 per requirements")
    if blocks <= 0:
        raise ValueError("blocks must be positive")
    if floors_per_block <= 0:
        raise ValueError("floors_per_block must be positive")

    capacity_choices = capacity_choices or [6, 8, 10]
    if any(capacity not in (6, 8, 10) for capacity in capacity_choices):
        raise ValueError("capacity choices must be a subset of {6, 8, 10}")

    if target_students is None:
        target_students = db.query(models.Student).count() or 600
    if target_students <= 0:
        raise ValueError("target_students must be positive")

    max_possible_capacity = blocks * floors_per_block * rooms_per_floor * max(capacity_choices)
    if target_students > max_possible_capacity:
        raise ValueError(
            "Configuration cannot satisfy capacity requirements. Increase blocks, floors, or rooms per floor."
        )

    if clear_existing:
        db.query(models.Assignment).delete(synchronize_session=False)
        db.query(models.Room).delete(synchronize_session=False)

    block_iter = _block_name_generator()
    used_blocks: List[str] = []
    total_capacity = 0
    rooms_created = 0

    gender_cycle: Iterable[str | None]
    if gender_strategy == "alternating":
        gender_cycle = itertools.cycle(["female", "male"])
    elif gender_strategy == "mixed":
        gender_cycle = itertools.cycle([None])
    else:
        raise ValueError("gender_strategy must be 'alternating' or 'mixed'")

    gender_iter = iter(gender_cycle)

    while total_capacity < target_students and len(used_blocks) < blocks:
        block_name = next(block_iter)
        used_blocks.append(block_name)
        for floor in range(1, floors_per_block + 1):
            for room_index in range(1, rooms_per_floor + 1):
                if total_capacity >= target_students:
                    break
                capacity = random.choice(capacity_choices)
                gender_restriction = next(gender_iter)
                room_code = f"{block_name}-{floor}{room_index:02d}"
                room = models.Room(
                    building=block_name,
                    room_code=room_code,
                    floor=floor,
                    capacity=capacity,
                    gender_restriction=gender_restriction,
                    room_type="collective",
                    noise_level=round(random.uniform(0.2, 0.9), 2),
                    facilities=_room_facilities(),
                    current_occupancy=0,
                )
                db.add(room)
                total_capacity += capacity
                rooms_created += 1
            if total_capacity >= target_students:
                break

    db.commit()

    total_rooms = db.query(models.Room).count()
    summary = RoomGenerationSummary(
        rooms_created=rooms_created,
        total_rooms=total_rooms,
        total_capacity=sum(room.capacity for room in db.query(models.Room).all()),
        target_capacity=target_students,
    )
    return summary.as_dict()
