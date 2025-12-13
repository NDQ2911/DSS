from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, Protocol


class StudentTraitSource(Protocol):
    gender: str
    smoking: bool


class RoomTraitSource(Protocol):
    gender_restriction: str | None


@dataclass(frozen=True)
class TraitDimension:
    name: str
    student_getter: Callable[[StudentTraitSource], str]
    room_getter: Callable[[RoomTraitSource], str | None] | None = None


TRAIT_DIMENSIONS: tuple[TraitDimension, ...] = (
    TraitDimension(
        name="gender",
        student_getter=lambda student: (student.gender or "").strip().lower(),
        room_getter=lambda room: (room.gender_restriction or "").strip().lower() or None,
    ),
    TraitDimension(
        name="smoking",
        student_getter=lambda student: "smoker" if bool(student.smoking) else "non-smoker",
    ),
)


def get_student_traits(student: StudentTraitSource) -> Dict[str, str]:
    return {dim.name: dim.student_getter(student) for dim in TRAIT_DIMENSIONS}


def get_room_locked_traits(room: RoomTraitSource) -> Dict[str, str]:
    locked: Dict[str, str] = {}
    for dim in TRAIT_DIMENSIONS:
        if not dim.room_getter:
            continue
        value = dim.room_getter(room)
        if value:
            locked[dim.name] = value
    return locked


def derive_room_signature(room: RoomTraitSource, occupants: Iterable[StudentTraitSource]) -> Dict[str, str]:
    signature = get_room_locked_traits(room)
    occupant_traits = [get_student_traits(student) for student in occupants]
    for dim in TRAIT_DIMENSIONS:
        if dim.name in signature:
            continue
        values = {traits[dim.name] for traits in occupant_traits}
        if len(values) > 1:
            raise ValueError(f"Room contains conflicting {dim.name} values: {values}")
        if values:
            signature[dim.name] = values.pop()
    return signature


def is_student_compatible(room: RoomTraitSource, occupants: Iterable[StudentTraitSource], student: StudentTraitSource) -> bool:
    signature = derive_room_signature(room, occupants)
    student_traits = get_student_traits(student)
    for dim in TRAIT_DIMENSIONS:
        required = signature.get(dim.name)
        if required is None:
            continue
        if student_traits.get(dim.name) != required:
            return False
    return True
