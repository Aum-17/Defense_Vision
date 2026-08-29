"""Rule-based Severity Engine with configurable thresholds.

Thresholds are defined here centrally so they are visible and tunable in
code/configuration rather than buried inside the detection logic.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SeverityThresholds:
    """Configurable thresholds for the severity engine.

    Segment proportions are relative to the total image area. "Diff strength"
    is the normalized mean intra-region change intensity in [0, 1].
    """

    large_area_ratio: float = 0.15   # >= => large region
    small_area_ratio: float = 0.02   # <= => small region
    strong_diff: float = 0.35        # >= mean intensity => strong visual difference
    weak_diff: float = 0.12          # <= => weak visual difference


DEFAULT_THRESHOLDS = SeverityThresholds()


def calculate_severity(
    area_ratio: float,
    mean_intensity: float,
    thresholds: SeverityThresholds = DEFAULT_THRESHOLDS,
) -> str:
    """Return 'LOW', 'MEDIUM' or 'HIGH' for a change region.

    Rules:
      HIGH   - large area OR (medium area AND strong diff)
      MEDIUM - moderate area OR strong diff
      LOW    - small area AND weak diff
    """
    large = area_ratio >= thresholds.large_area_ratio
    small = area_ratio <= thresholds.small_area_ratio
    strong = mean_intensity >= thresholds.strong_diff
    weak = mean_intensity <= thresholds.weak_diff

    if large or (not small and strong):
        return "HIGH"
    if strong or not small:
        return "MEDIUM"
    return "LOW"
