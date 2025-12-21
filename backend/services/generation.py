from __future__ import annotations

import itertools
import random
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from pathlib import Path
import math
from typing import Dict, Iterable, List, Sequence

from sqlalchemy.orm import Session

from .. import models

SEED_DIR = Path(__file__).resolve().parent.parent / "data"
BIRTHDAY_START = date(2004, 1, 1)
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

# Vietnamese name data
NAME_DATA = {
    "first_names": [
        "Nguyễn", "Trần", "Lê", "Phạm", "Vũ", "Hoàng", "Hồ", "Đặng", "Bùi", "Dương", "Trương", "Đỗ",
        "Lý", "Tô", "Ngô", "Đoàn", "Mai", "Võ", "Phan", "Trịnh", "Doãn", "Tạ", "Lương", "Đinh", "Hà",
        "Lâm", "Cao", "Chu", "Tống", "Quách", "Tôn", "Khương", "Tăng", "Bành", "Thái", "Hứa", "Ninh",
        "Khuất", "Đồng", "Lưu"
    ],
    "male_last_names": [
        "Văn Minh Đức", "Văn Hoàng Anh", "Văn Quang Huy", "Văn Đức Anh", "Văn Thành Công",
        "Văn Tuấn Anh", "Văn Hùng Anh", "Văn Minh Tuấn", "Văn Đức Khang", "Văn Quang Minh",
        "Hoàng Minh Đức", "Hoàng Anh Tuấn", "Hoàng Quang Huy", "Hoàng Đức Anh", "Hoàng Thành Công",
        "Hoàng Tuấn Anh", "Hoàng Hùng Anh", "Hoàng Minh Tuấn", "Hoàng Đức Khang", "Hoàng Quang Minh",
        "Trần Minh Đức", "Trần Thành Công",
        "Trần Tuấn Anh", "Trần Hùng Anh", "Trần Minh Tuấn", "Trần Đức Khang", "Trần Quang Minh",
        "Lê Minh Đức", "Lê Hoàng Anh", "Lê Quang Huy", "Lê Đức Anh", "Lê Thành Công",
        "Lê Tuấn Anh", "Lê Hùng Anh", "Lê Minh Tuấn", "Lê Đức Khang", "Lê Quang Minh",
        "Phạm Minh Đức", "Phạm Hoàng Anh", "Phạm Quang Huy", "Phạm Đức Anh", "Phạm Thành Công",
        "Phạm Tuấn Anh", "Phạm Hùng Anh", "Phạm Minh Tuấn", "Phạm Đức Khang", "Phạm Quang Minh",
        "Vũ Minh Đức", "Vũ Hoàng Anh", "Vũ Quang Huy", "Vũ Đức Anh", "Vũ Thành Công",
        "Minh Tuấn Anh", "Minh Hùng Anh", "Minh Tuấn Đức", "Minh Đức Khang", "Minh Quang Đức",
        "Tuấn Anh Đức", "Tuấn Hùng Anh", "Tuấn Minh Anh", "Tuấn Đức Khang", "Tuấn Quang Minh",
        "Minh Huy", "Hải Đăng", "Hoàng Tùng", "Quang Hieu", "Minh Tuấn", "Anh Duy",
        "Mạnh Cường", "Đức Khang", "Phước Tài", "Đoàn Lâm", "Vũ Quang", "Hải Nam", "Kiên An", "Đình Tú",
        "Bảo Nam", "Gia Hưng", "Trường Giang", "Khánh Lâm", "Vũ Đức", "Tiến Hòa", "Trí Quân",
        "Hùng Anh", "Thanh Tùng", "Văn Sơn", "Quốc Duy", "Khoa Minh", "Kiên Văn", "Đức Tuấn", "Hoàng Phúc",
        "Duy Tuấn", "Trường Sơn", "Tuấn Kiệt", "Phúc Thịnh", "Hưng Lợi", "Quang Đạt", "Vinh Hoàng",
        "Thành Tâm", "Thanh Quang", "Công Sơn", "Lâm Quang", "Ngọc Thành", "Lộc Phát", "Trí Dũng", "Khang Đạt",
        "Quốc Trung", "Hải Vũ", "Duy Khánh", "Khuê Minh", "Đức Anh", "Quang Đức", "Trung Kiên",
        "Tùng Quân", "Hà Quang", "Ngọc Sơn", "Vinh Khoa", "Tài Đức", "Hữu Tài", "Sơn Hải", "Hồng Sơn",
        "Hải Thanh", "Quang Bình", "Thiện Đức", "Hữu Trí", "Vương Anh"
    ],
    "female_last_names": [
        "Thị Minh Thảo", "Thị Hồng Nhung", "Thị Lan Hương", "Thị Thu Hà", "Thị Ngọc Anh",
        "Thị Linh Chi", "Thị Phương Nhi", "Thị Thanh Lan", "Thị Bảo Ngọc", "Thị Khánh Linh",
        "Thị Linh Hương", "Thị Thảo Nguyên", "Thị Ánh Tuyết", "Thị Thu Hà", "Thị Hải Đan",
        "Thị Trâm Anh", "Thị Diễm My", "Thị Mỹ Linh", "Thị Quỳnh Chi", "Thị Ngọc Hân",
        "Thị Kim Ngân", "Thị Phương Thảo", "Thị Thảo Ly", "Thị Linh Chi", "Thị Tú Anh",
        "Thị Như Quỳnh", "Thị Thiên Kim", "Thị Quỳnh Như", "Thị Bích Thuỳ", "Thị Thanh Mai",
        "Thị Minh Thảo", "Thị Ngọc Thảo", "Thị Ánh Lan", "Thị Hồng Nhung", "Thị Thúy Anh",
        "Thị Nhật Lan", "Thị Diễm Kiều", "Thị Minh Ngọc", "Thị Trang Nhung", "Thị Bảo Hà",
        "Thị Thuý Vân", "Thị Hải Yến", "Thị Thùy Linh", "Thị Lan Hương", "Thị Bích Hạnh",
        "Thị Thuỳ Dung", "Thị Kim Liên", "Thị Tú Quỳnh", "Thị Thảo Quyên", "Thị Phúc An",
        "Thị Diễm Thanh", "Thị Hạnh Dung", "Thị Thiên Hương", "Thị Bích Lệ", "Thị Ngọc Tâm",
        "Thùy Tiên", "Phương Nhi", "Thanh Lan", "Bảo Ngọc", "Khánh Linh", "Linh Hương",
        "Thảo Nguyên", "Ánh Tuyết", "Thu Hà", "Hải Đan", "Trâm Anh", "Diễm My", "Mỹ Linh",
        "Quỳnh Chi", "Ngọc Hân", "Kim Ngân", "Phương Thảo", "Thảo Ly", "Linh Chi", "Tú Anh", "Như Quỳnh",
        "Thiên Kim", "Quỳnh Như", "Bích Thuỳ", "Thanh Mai", "Minh Thảo", "Ngọc Thảo", "Ánh Lan", "Hồng Nhung",
        "Thúy Anh", "Nhật Lan", "Diễm Kiều", "Minh Ngọc", "Trang Nhung", "Bảo Hà", "Thuý Vân", "Hải Yến",
        "Thùy Linh", "Lan Hương", "Bích Hạnh", "Thuỳ Dung", "Kim Liên", "Tú Quỳnh", "Thảo Quyên",
        "Phúc An", "Diễm Thanh", "Hạnh Dung", "Thiên Hương", "Bích Lệ", "Ngọc Tâm", "Quỳnh Duyên", "Thùy Trang",
        "Ánh Hồng", "Kim Chi", "Thiều Lan", "Hương Lan", "Khánh Hương", "Như Lan", "Hồng Quỳnh", "Thúy Vân",
        "Thiên Tiên", "Thanh Hòa", "Thu Lan", "Thu Hương", "Thủy Tiên", "Hải Linh", "Như Hoa", "Bảo Như",
        "Ngọc Dung", "Thiều Thư", "Tâm Hương", "Thúy Dung", "Thảo Linh"
    ]
}

FACULTIES = [
    "Trường Công nghệ Thông tin và Truyền thông",
    "Trường Điện - Điện tử",
    "Trường Cơ khí",
    "Trường Kinh tế",
    "Khoa Toán tin",
    "Khoa Vật lý kỹ thuật",
    "Khoa Ngoại ngữ",
    "Trường Hóa và Khoa học sự sống",
    "Khoa kỹ thuật vật liệu",
    "Khoa công nghệ sinh học"
]

BEDTIME_TO_SLEEP_SCORE = {
    21: 1,
    22: 2,
    23: 3,
    0: 4,
    1: 5,
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
    """Generate random bedtime hour and convert to sleep_schedule_score"""
    bedtime = random.choice([21, 22, 23, 0, 1])
    return BEDTIME_TO_SLEEP_SCORE.get(bedtime, 3)


def _build_full_name(surnames: Sequence[str], names: Sequence[str]) -> str:
    """Build full name using Vietnamese name data, avoiding surname duplication"""
    first_name = random.choice(NAME_DATA["first_names"])
    # Randomly choose gender for name selection
    gender = random.choice(["male", "female"])
    if gender == "male":
        last_names = NAME_DATA["male_last_names"]
    else:
        last_names = NAME_DATA["female_last_names"]

    # Filter out names that start with the same surname
    valid_last_names = [name for name in last_names if not name.startswith(first_name)]
    if not valid_last_names:
        valid_last_names = last_names

    last_name = random.choice(valid_last_names)
    return f"{first_name} {last_name}"


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

        first_name = random.choice(NAME_DATA["first_names"])
        if gender == "male":
            last_names = NAME_DATA["male_last_names"]
        else:
            last_names = NAME_DATA["female_last_names"]

        valid_last_names = [name for name in last_names if not name.startswith(first_name)]
        if not valid_last_names:
            valid_last_names = last_names

        last_name = random.choice(valid_last_names)
        full_name = f"{first_name} {last_name}"

        smoking = random.random() < smoking_ratio
        introversion = _random_score()
        cleanliness = _random_score()

        bedtime = random.choice([21, 22, 23, 0, 1])
        sleep_score = BEDTIME_TO_SLEEP_SCORE.get(bedtime, 3)

        noise_tolerance = _random_score()

        birthday = _random_birthday()
        birth_year = birthday.year
        year = {2004: 4, 2005: 3, 2006: 2, 2007: 1}.get(birth_year, random.randint(1, 4))

        major = random.choice(FACULTIES) if FACULTIES else None

        student = models.Student(
            name=full_name,
            gender=gender,
            major=major,
            birthday=birthday,
            year=year,
            introversion_score=introversion,
            cleanliness_score=cleanliness,
            noise_tolerance=noise_tolerance,
            sleep_schedule_score=sleep_score,
            smoking=smoking,
            additional_attributes={
                "sleep_window": SLEEP_WINDOWS.get(sleep_score, "Not specified"),
                "bedtime": bedtime,
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
        gender_strategy: str = "mixed",
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

    required_capacity = math.ceil(target_students * 1.05)

    max_possible_capacity = blocks * floors_per_block * rooms_per_floor * max(capacity_choices)
    if required_capacity > max_possible_capacity:
        raise ValueError(
            "Configuration cannot satisfy the 5% buffer capacity requirement. Increase blocks, floors, or rooms per floor."
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

    while total_capacity < required_capacity and len(used_blocks) < blocks:
        block_name = next(block_iter)
        used_blocks.append(block_name)
        for floor in range(1, floors_per_block + 1):
            for room_index in range(1, rooms_per_floor + 1):
                if total_capacity >= required_capacity:
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
            if total_capacity >= required_capacity:
                break

    db.commit()

    total_rooms = db.query(models.Room).count()
    summary = RoomGenerationSummary(
        rooms_created=rooms_created,
        total_rooms=total_rooms,
        total_capacity=sum(room.capacity for room in db.query(models.Room).all()),
        target_capacity=required_capacity,
    )
    return summary.as_dict()
