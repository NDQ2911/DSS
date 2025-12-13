from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

from .. import models
from .cost import calculate_state_cost


@dataclass(frozen=True)
class StudentProfile:
    id: int
    gender: str
    introversion_score: int
    sleep_schedule_score: int
    cleanliness_score: int
    noise_tolerance: int
    smoking: bool


@dataclass(frozen=True)
class RoomProfile:
    id: int
    capacity: int
    gender_restriction: str | None
    noise_level: float


State = List[Tuple[RoomProfile, List[StudentProfile]]]


class SimulatedAnnealingOptimizer:
    def __init__(
        self,
        students: Sequence[models.Student],
        rooms: Sequence[models.Room],
        *,
        initial_temperature: float = 1000.0,
        cooling_rate: float = 0.95,
        min_temperature: float = 0.1,
    ) -> None:
        if not students:
            raise ValueError("At least one student is required for optimization")
        if not rooms:
            raise ValueError("At least one room is required for optimization")
        if sum(room.capacity for room in rooms) < len(students):
            raise ValueError("Not enough total room capacity for all students")

        self.students = [self._to_student_profile(student) for student in students]
        self.rooms = [self._to_room_profile(room) for room in rooms]
        self.initial_temperature = initial_temperature
        self.cooling_rate = cooling_rate
        self.min_temperature = min_temperature

    def _to_student_profile(self, student: models.Student) -> StudentProfile:
        return StudentProfile(
            id=student.id,
            gender=student.gender,
            introversion_score=student.introversion_score,
            sleep_schedule_score=student.sleep_schedule_score,
            cleanliness_score=student.cleanliness_score,
            noise_tolerance=student.noise_tolerance,
            smoking=student.smoking,
        )

    def _to_room_profile(self, room: models.Room) -> RoomProfile:
        return RoomProfile(
            id=room.id,
            capacity=room.capacity,
            gender_restriction=room.gender_restriction,
            noise_level=room.noise_level,
        )

    def _initial_state(self) -> State:
        shuffled_students = self.students[:]
        random.shuffle(shuffled_students)

        state: State = []
        student_idx = 0
        for room in self.rooms:
            remaining = len(shuffled_students) - student_idx
            if remaining <= 0:
                state.append((room, []))
                continue
            take = min(room.capacity, remaining)
            chunk = shuffled_students[student_idx : student_idx + take]
            state.append((room, list(chunk)))
            student_idx += take

        return state

    @staticmethod
    def _clone_state(state: State) -> State:
        return [(room, occupants[:]) for room, occupants in state]

    def _neighbor(self, state: State) -> State:
        new_state = self._clone_state(state)

        movable_rooms = [idx for idx, (_, occupants) in enumerate(new_state) if occupants]
        if not movable_rooms:
            return new_state

        action = random.random()
        if action < 0.4:
            dest_candidates = [idx for idx, (room, occupants) in enumerate(new_state) if len(occupants) < room.capacity]
            source_idx = random.choice(movable_rooms)
            if dest_candidates:
                dest_idx = random.choice(dest_candidates)
                if source_idx != dest_idx:
                    student_list = new_state[source_idx][1]
                    student = student_list.pop(random.randrange(len(student_list)))
                    new_state[dest_idx][1].append(student)
                    return new_state

        if len(movable_rooms) >= 2:
            idx1, idx2 = random.sample(movable_rooms, 2)
            occ1 = new_state[idx1][1]
            occ2 = new_state[idx2][1]
            s_idx1 = random.randrange(len(occ1))
            s_idx2 = random.randrange(len(occ2))
            occ1[s_idx1], occ2[s_idx2] = occ2[s_idx2], occ1[s_idx1]

        return new_state

    def optimize(self, iterations: int) -> Dict[str, object]:
        current_state = self._initial_state()
        current_cost = calculate_state_cost(current_state)
        best_state = current_state
        best_cost = current_cost
        temperature = self.initial_temperature

        start_time = time.perf_counter()

        for _ in range(iterations):
            candidate_state = self._neighbor(current_state)
            candidate_cost = calculate_state_cost(candidate_state)
            delta = candidate_cost - current_cost

            accept = False
            if delta < 0:
                accept = True
            else:
                acceptance_prob = math.exp(-delta / max(temperature, 1e-6))
                if random.random() < acceptance_prob:
                    accept = True

            if accept:
                current_state = candidate_state
                current_cost = candidate_cost
                if current_cost < best_cost:
                    best_cost = current_cost
                    best_state = current_state

            temperature = max(temperature * self.cooling_rate, self.min_temperature)

        runtime_ms = (time.perf_counter() - start_time) * 1000

        return {
            "best_cost": best_cost,
            "assignments": self._state_to_assignments(best_state),
            "iterations": iterations,
            "runtime_ms": runtime_ms,
        }

    def _state_to_assignments(self, state: State) -> Dict[str, List[int]]:
        assignments: Dict[str, List[int]] = {}
        for room, occupants in state:
            if not occupants:
                continue
            assignments[str(room.id)] = [student.id for student in occupants]
        return assignments
