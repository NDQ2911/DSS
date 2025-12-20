from __future__ import annotations

from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


# feature order: [introversion_score, sleep_schedule_score, cleanliness_score, noise_tolerance, year, major]
DEFAULT_WEIGHTS: List[float] = [3.0, 2.5, 2.0, 1.5, 0.1, 0.1]

# Normalize weights to sum to number of features (for balanced scaling)
_WEIGHTS_SUM = sum(DEFAULT_WEIGHTS)
NORMALIZED_WEIGHTS: List[float] = [
    w * len(DEFAULT_WEIGHTS) / _WEIGHTS_SUM for w in DEFAULT_WEIGHTS
]


def get_weights() -> List[float]:
    return NORMALIZED_WEIGHTS.copy()

def get_weight_dict() -> dict[str, float]:
    return {
        "introversion_score": NORMALIZED_WEIGHTS[0],
        "sleep_schedule_score": NORMALIZED_WEIGHTS[1],
        "cleanliness_score": NORMALIZED_WEIGHTS[2],
        "noise_tolerance": NORMALIZED_WEIGHTS[3],
        "year": NORMALIZED_WEIGHTS[4] if len(NORMALIZED_WEIGHTS) > 4 else 0.8,
        "major": NORMALIZED_WEIGHTS[5] if len(NORMALIZED_WEIGHTS) > 5 else 1.0,
    }

def calculate_feature_distances(student1, student2) -> List[float]:
    distances = []
    max_likert = 4.0
    distances.append(((student1.introversion_score - student2.introversion_score) / max_likert) ** 2)
    distances.append(((student1.sleep_schedule_score - student2.sleep_schedule_score) / max_likert) ** 2)
    distances.append(((student1.cleanliness_score - student2.cleanliness_score) / max_likert) ** 2)
    distances.append(((student1.noise_tolerance - student2.noise_tolerance) / max_likert) ** 2)
    year1 = student1.year if student1.year and 1 <= student1.year <= 4 else 2
    year2 = student2.year if student2.year and 1 <= student2.year <= 4 else 2
    distances.append(0.0 if year1 == year2 else 1.0)
    major1 = (student1.major or "").strip().lower()
    major2 = (student2.major or "").strip().lower()
    distances.append(0.0 if major1 == major2 else 1.0)
    return distances

