from __future__ import annotations

import math
import random
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

from .. import models
from ..models import Room
from ..services.generation import FACULTIES
from .weights import get_weights

MAJOR_MAPPING: Dict[str, int] = {major: idx for idx, major in enumerate(FACULTIES)}
NUM_MAJORS = len(FACULTIES)
NUM_YEARS = 4
YEAR_IDX, MAJOR_IDX = 4, 5
DISCRETE_INDICES = [YEAR_IDX, MAJOR_IDX]


def _create_discrete_proportions(values: List[int], size: int) -> List[float]:
    proportions = [0.0] * size
    if values:
        for val in values:
            if 0 <= val < size:
                proportions[val] += 1.0 / len(values)
    return proportions


def _create_centroid_from_point(point: Tuple[float, ...], n_features: int) -> List:
    centroid = []
    for i in range(n_features):
        if i in DISCRETE_INDICES:
            size = NUM_YEARS if i == YEAR_IDX else NUM_MAJORS
            proportions = [0.0] * size
            val = int(point[i])
            if 0 <= val < size:
                proportions[val] = 1.0
            centroid.append(proportions)
        else:
            centroid.append(point[i])
    return centroid


def _compute_centroid_from_members(members: List[Tuple[float, ...]], n_features: int) -> List:
    centroid = []
    n_members = len(members)
    for i in range(n_features):
        if i in DISCRETE_INDICES:
            values = [int(p[i]) for p in members]
            size = NUM_YEARS if i == YEAR_IDX else NUM_MAJORS
            centroid.append(_create_discrete_proportions(values, size))
        else:
            centroid.append(sum(p[i] for p in members) / n_members)
    return centroid


def _get_room_signature(room_id: int, assignments: Dict[int, List[int]],
                        student_index: Dict[int, '_StudentPoint']) -> Tuple[str, bool] | None:
    occ = assignments.get(room_id, [])
    if not occ:
        return None
    first_occ = student_index.get(occ[0])
    return (first_occ.gender, first_occ.smoking) if first_occ else None


def _is_room_compatible(room: models.Room, bucket_sig: Tuple[str, bool],
                        room_restriction: Dict[int, str | None],
                        assignments: Dict[int, List[int]],
                        student_index: Dict[int, '_StudentPoint']) -> bool:
    restriction = room_restriction.get(room.id)
    if restriction and restriction != bucket_sig[0]:
        return False
    sig = _get_room_signature(room.id, assignments, student_index)
    return sig is None or sig == bucket_sig


@dataclass(frozen=True)
class _StudentPoint:
    id: int
    gender: str
    smoking: bool
    year: int
    major: str
    introversion_score: int
    sleep_schedule_score: int
    cleanliness_score: int
    noise_tolerance: int

    def vector(self) -> Tuple[float, float, float, float, int, int]:
        normalize = lambda x: max(0.0, min(1.0, (float(x) - 1.0) / 4.0))
        major_code = MAJOR_MAPPING.get((self.major or "").strip(), 0)
        return (
            normalize(self.introversion_score),
            normalize(self.sleep_schedule_score),
            normalize(self.cleanliness_score),
            normalize(self.noise_tolerance),
            (self.year - 1) if self.year and 1 <= self.year <= 4 else 1,
            major_code,
        )


def _weighted_euclidean(a: Tuple[float, ...], b: Tuple[float, ...] | List,
                        weights: Sequence[float], discrete_indices: Sequence[int] | None = None) -> float:
    if discrete_indices is None:
        discrete_indices = []

    distance_sum = 0.0
    for i in range(len(a)):
        if i in discrete_indices:
            if isinstance(b[i], (list, tuple)) and len(b[i]) > 0:
                proportions = b[i]
                value = int(a[i])
                if 0 <= value < len(proportions):
                    distance_sum += weights[i] * ((1.0 - proportions[value]) ** 2)
                else:
                    distance_sum += weights[i]
            else:
                distance_sum += weights[i] * (0.0 if int(a[i]) == int(b[i]) else 1.0)
        else:
            distance_sum += weights[i] * ((a[i] - b[i]) ** 2)
    return math.sqrt(distance_sum) if distance_sum > 0 else 0.0


def _mean_squared_distance(cluster_student_ids: List[int], student_index: Dict[int, _StudentPoint],
                           weights: Sequence[float]) -> float:
    if len(cluster_student_ids) < 2:
        return 0.0
    points = [student_index[sid].vector() for sid in cluster_student_ids if sid in student_index]
    if len(points) < 2:
        return 0.0
    centroid = _compute_centroid_from_members(points, len(points[0]))
    return sum(_weighted_euclidean(p, centroid, weights, DISCRETE_INDICES) ** 2 for p in points) / len(points)


def _calculate_room_diversity(room_student_ids: List[int], student_index: Dict[int, _StudentPoint],
                              weights: Sequence[float]) -> float:
    if len(room_student_ids) < 2:
        return 0.0
    points = [student_index[sid].vector() for sid in room_student_ids if sid in student_index]
    if len(points) < 2:
        return 0.0
    distances = [_weighted_euclidean(points[i], points[j], weights, DISCRETE_INDICES)
                 for i in range(len(points)) for j in range(i + 1, len(points))]
    return sum(distances) / len(distances) if distances else 0.0


def _optimize_assignments_by_swapping(assignments: Dict[int, List[int]], student_index: Dict[int, _StudentPoint],
                                      room_capacity: Dict[int, int], room_restriction: Dict[int, str | None],
                                      weights: Sequence[float], max_iterations: int = 10) -> Dict[int, List[int]]:
    assignments = {room_id: students.copy() for room_id, students in assignments.items()}

    for _ in range(max_iterations):
        improved = False
        room_ids = list(assignments.keys())
        for i, room1_id in enumerate(room_ids):
            room1_students = assignments.get(room1_id, [])
            if not room1_students:
                continue
            sig1 = _get_room_signature(room1_id, assignments, student_index)
            if not sig1:
                continue
            for room2_id in room_ids[i + 1:]:
                room2_students = assignments.get(room2_id, [])
                if not room2_students:
                    continue
                sig2 = _get_room_signature(room2_id, assignments, student_index)
                if sig1 != sig2 or not sig2:
                    continue
                if (room_restriction.get(room1_id) and room_restriction[room1_id] != sig1[0]) or \
                        (room_restriction.get(room2_id) and room_restriction[room2_id] != sig2[0]):
                    continue
                current_total = (_calculate_room_diversity(room1_students, student_index, weights) +
                                 _calculate_room_diversity(room2_students, student_index, weights))
                best_swap, best_improvement = None, 0.0
                for sid1 in room1_students:
                    for sid2 in room2_students:
                        new_room1 = [sid if sid != sid1 else sid2 for sid in room1_students]
                        new_room2 = [sid if sid != sid2 else sid1 for sid in room2_students]
                        if (len(new_room1) > room_capacity[room1_id] or
                                len(new_room2) > room_capacity[room2_id]):
                            continue
                        new_total = (_calculate_room_diversity(new_room1, student_index, weights) +
                                     _calculate_room_diversity(new_room2, student_index, weights))
                        improvement = current_total - new_total
                        if improvement > best_improvement:
                            best_improvement, best_swap = improvement, (new_room1, new_room2)
                if best_swap and best_improvement > 0.001:
                    assignments[room1_id], assignments[room2_id] = best_swap
                    improved = True
                    break
            if improved:
                break
        if not improved:
            break
    return assignments


def _kmeans_cluster(students: Sequence[_StudentPoint], k: int, *, max_iter: int = 50,
                    weights: Sequence[float] | None = None) -> Tuple[List[List[int]], List[float]]:
    if not students:
        return [], []
    if weights is None:
        weights = get_weights()
    k = max(1, min(k, len(students)))
    points = [s.vector() for s in students]
    n_features = len(points[0])
    initial_indices = random.sample(range(len(points)), k)
    centroids = [_create_centroid_from_point(points[idx], n_features) for idx in initial_indices]
    assignments = [0] * len(points)
    for _ in range(max_iter):
        changed = False
        # assign step
        for idx, p in enumerate(points):
            distances = [_weighted_euclidean(p, c, weights, DISCRETE_INDICES) for c in centroids]
            if not distances:
                continue
            cluster_idx = min(range(len(centroids)), key=lambda j: distances[j])
            if assignments[idx] != cluster_idx:
                assignments[idx] = cluster_idx
                changed = True
        new_centroids: List[List] = []
        empty_clusters: List[int] = []

        for cluster in range(k):
            members = [points[i] for i, a in enumerate(assignments) if a == cluster]
            if not members:
                empty_clusters.append(cluster)
                continue
            new_centroids.append(_compute_centroid_from_members(members, n_features))
        for empty_cluster_idx in empty_clusters:
            all_centroids = [c for c in new_centroids if c] + \
                            [centroids[i] for i in range(k) if i != empty_cluster_idx and i < len(centroids)]
            best_point_idx = max(
                range(len(points)),
                key=lambda idx: min(
                    (_weighted_euclidean(points[idx], c, weights, DISCRETE_INDICES) for c in all_centroids),
                    default=float('inf')
                ),
                default=-1
            )

            point = points[best_point_idx] if best_point_idx >= 0 else random.choice(points)
            while len(new_centroids) <= empty_cluster_idx:
                new_centroids.append([])
            new_centroids[empty_cluster_idx] = _create_centroid_from_point(point, n_features)

            if best_point_idx >= 0 and assignments[best_point_idx] != empty_cluster_idx:
                assignments[best_point_idx] = empty_cluster_idx
                changed = True

        centroids = new_centroids
        if not changed:
            break

    clustered_ids: Dict[int, List[int]] = defaultdict(list)
    for idx, cluster_idx in enumerate(assignments):
        clustered_ids[cluster_idx].append(students[idx].id)
    student_index = {s.id: s for s in students}
    clusters = [clustered_ids[i] for i in sorted(clustered_ids.keys())]
    msds = [_mean_squared_distance(cluster, student_index, weights) for cluster in clusters]
    return clusters, msds

def _calculate_bucket_k(buckets: Dict[Tuple[str, bool], List[_StudentPoint]],
                        total_rooms: int, total_students: int) -> Dict[Tuple[str, bool], int]:
    """calculate K for each bucket based on student ratio."""
    total_clusters = int(total_rooms * 1.2)
    bucket_k: Dict[Tuple[str, bool], int] = {}
    for (gender, smoking), group in buckets.items():
        if not group:
            continue
        ratio = len(group) / total_students if total_students > 0 else 0
        k = max(1, min(int(total_clusters * ratio), len(group)))
        bucket_k[(gender, smoking)] = k

    return bucket_k
def _group_rooms_by_capacity(compatible_rooms: List[models.Room], room_capacity: Dict[int, int],
                             assignments: Dict[int, List[int]]) -> tuple[dict[int, list[Room]], list[int]]:
    """Group compatible rooms by capacity."""
    distinct_capacities = sorted(set(room_capacity[room.id] for room in compatible_rooms))
    room_groups: Dict[int, List[models.Room]] = {}

    for capacity in distinct_capacities:
        room_groups[capacity] = [
            room for room in compatible_rooms
            if room_capacity[room.id] == capacity
               and len(assignments.get(room.id, [])) < capacity
        ]

    return room_groups, distinct_capacities

def _find_room_group(n: int, distinct_capacities: List[int],
                     room_groups: Dict[int, List[models.Room]]) -> int | None:
    """Find room group with smallest capacity >= n."""
    if not distinct_capacities or n < distinct_capacities[0]:
        return None
    left, right, result = 0, len(distinct_capacities) - 1, None
    while left <= right:
        mid = (left + right) // 2
        cap = distinct_capacities[mid]
        if cap >= n:
            if room_groups.get(cap):
                result = cap
            right = mid - 1
        else:
            left = mid + 1
    return result
def _assign_cluster_to_room(cluster_students: List[int], bucket_sig: Tuple[str, bool],
                            room_groups: Dict[int, List[models.Room]], distinct_capacities: List[int],
                            room_capacity: Dict[int, int], room_restriction: Dict[int, str | None],
                            assignments: Dict[int, List[int]], global_student_index: Dict[int, _StudentPoint]) -> List[
    int]:
    remaining = cluster_students.copy()
    while remaining:
        cluster_size = len(remaining)
        target_capacity = _find_room_group(cluster_size, distinct_capacities, room_groups)
        if target_capacity is None or not room_groups.get(target_capacity):
            break
        room = None
        room_idx = -1
        for idx, r in enumerate(room_groups[target_capacity]):
            if _is_room_compatible(r, bucket_sig, room_restriction, assignments, global_student_index):
                room = r
                room_idx = idx
                break
        if room is None:
            break
        room_groups[target_capacity].pop(room_idx)
        available_slots = room_capacity[room.id] - len(assignments.get(room.id, []))
        num_to_assign = min(cluster_size, available_slots)
        if num_to_assign <= 0:
            break
        assigned_students = remaining[-num_to_assign:]
        remaining = remaining[:-num_to_assign]
        assignments[room.id].extend(assigned_students)
        if len(assignments[room.id]) < room_capacity[room.id]:
            original_capacity = room_capacity[room.id]
            room_groups.setdefault(original_capacity, []).append(room)

    return remaining
def _assign_remaining_students(remaining_students: List[int], bucket_sig: Tuple[str, bool],
                               room_groups: Dict[int, List[models.Room]], distinct_capacities: List[int],
                               room_capacity: Dict[int, int], room_restriction: Dict[int, str | None],
                               assignments: Dict[int, List[int]], global_student_index: Dict[int, _StudentPoint]):
    """assign remaining students to compatible rooms."""
    for sid in remaining_students[:]:
        for capacity in distinct_capacities:
            for room in room_groups.get(capacity, []):
                if (len(assignments.get(room.id, [])) < room_capacity[room.id] and
                        _is_room_compatible(room, bucket_sig, room_restriction, assignments, global_student_index)):
                    assignments[room.id].append(sid)
                    remaining_students.remove(sid)
                    if len(assignments[room.id]) >= room_capacity[room.id]:
                        for cap in room_groups:
                            room_groups[cap] = [r for r in room_groups[cap] if r.id != room.id]
                    break
            if sid not in remaining_students:
                break

def kmeans_room_assignment(students: Sequence[models.Student], rooms: Sequence[models.Room]) -> Dict[int, List[int]]:
    if not students or not rooms:
        return {}
    # pre-bucket students by hard constraints
    buckets: Dict[Tuple[str, bool], List[_StudentPoint]] = defaultdict(list)
    for s in students:
        key = ((s.gender or "").strip().lower(), bool(s.smoking))
        buckets[key].append(_StudentPoint(
            id=s.id, gender=key[0], smoking=key[1], year=s.year or 2,
            major=(s.major or "").strip(), introversion_score=s.introversion_score,
            sleep_schedule_score=s.sleep_schedule_score, cleanliness_score=s.cleanliness_score,
            noise_tolerance=s.noise_tolerance,
        ))

    room_capacity = {room.id: room.capacity for room in rooms}
    room_restriction = {room.id: (room.gender_restriction or "").strip().lower() or None for room in rooms}
    assignments: Dict[int, List[int]] = defaultdict(list)
    global_student_index: Dict[int, _StudentPoint] = {}
    for bucket_group in buckets.values():
        for sp in bucket_group:
            global_student_index[sp.id] = sp
    # Calculate K for each bucket
    bucket_k = _calculate_bucket_k(buckets, len(rooms), len(students))
    for (gender, smoking) in sorted(buckets.keys()):
        group = buckets[(gender, smoking)]
        if not group:
            continue
        bucket_sig = (gender, smoking)
        compatible_rooms = [
            room for room in rooms
            if len(assignments.get(room.id, [])) < room_capacity[room.id]
               and _is_room_compatible(room, bucket_sig, room_restriction, assignments, global_student_index)
        ]
        # KMeans clustering
        k = bucket_k.get((gender, smoking), min(len(compatible_rooms), len(group)))
        clusters, msds = _kmeans_cluster(group, k=k, weights=get_weights())
        # sort clusters by MSD (best first)
        clusters = [c[0] for c in sorted(zip(clusters, msds), key=lambda x: x[1])]
        room_groups, distinct_capacities = _group_rooms_by_capacity(compatible_rooms, room_capacity, assignments)
        # assign clusters to rooms
        remaining_students_in_bucket: List[int] = []
        for cluster in clusters:
            remaining = _assign_cluster_to_room(
                cluster, bucket_sig, room_groups, distinct_capacities,
                room_capacity, room_restriction, assignments, global_student_index
            )
            remaining_students_in_bucket.extend(remaining)
        # handle remaining students
        _assign_remaining_students(
            remaining_students_in_bucket, bucket_sig, room_groups, distinct_capacities,
            room_capacity, room_restriction, assignments, global_student_index
        )
    # assign any remaining unassigned students
    all_student_ids = {s.id for s in students}
    assigned_ids = {sid for room_ids in assignments.values() for sid in room_ids}
    for sid in all_student_ids - assigned_ids:
        sp = global_student_index[sid]
        desired_sig = (sp.gender, sp.smoking)
        for room in rooms:
            if (len(assignments.get(room.id, [])) < room_capacity[room.id] and
                    _is_room_compatible(room, desired_sig, room_restriction, assignments, global_student_index)):
                assignments[room.id].append(sid)
                break
        else:
            raise ValueError(
                f"Not enough compatible room capacity for student {sid} "
                f"(gender={sp.gender}, smoking={sp.smoking})"
            )
    # optimize by swapping
    assignments = _optimize_assignments_by_swapping(
        assignments, global_student_index, room_capacity, room_restriction,
        get_weights(), max_iterations=15
    )
    return assignments