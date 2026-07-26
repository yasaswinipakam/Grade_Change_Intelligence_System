"""Deterministic historical-transition evidence for grade-change predictions.

This hackathon implementation uses an in-memory history profile. Its public
interface is intentionally database-agnostic so a real historical query layer
can replace the internal lookup later without changing callers.
"""

from __future__ import annotations

from math import isfinite
from typing import Any, Mapping


class HistoricalEvidenceEngine:
    """Retrieve evidence metrics by trusting the scenario in a prediction."""

    DEFAULT_HISTORY = {
        "A": {"name": "Yellow Risk", "similar_cases": 18, "success_rate": 89.0, "avg_stabilization_minutes": 8,
              "risk_range": (30.0, 75.0), "typical_risk_score": 68.0,
              "description": "Grade ramp with moderate basis weight increase"},
        "B": {"name": "Red Risk", "similar_cases": 5, "success_rate": 60.0, "avg_stabilization_minutes": 15,
              "risk_range": (75.0, 100.0), "typical_risk_score": 84.0,
              "description": "Rapid basis weight decrease requiring critical intervention"},
        "C": {"name": "Green Safe", "similar_cases": 42, "success_rate": 98.0, "avg_stabilization_minutes": 2,
              "risk_range": (0.0, 30.0), "typical_risk_score": 22.0,
              "description": "Stable process with minimal adjustment"},
    }

    def __init__(self, mock_history: Mapping[str, Mapping[str, Any]] | None = None) -> None:
        """Initialize mock historical profiles without feature-processor coupling."""
        source = mock_history if mock_history is not None else self.DEFAULT_HISTORY
        self._mock_history = {scenario: dict(profile) for scenario, profile in source.items()}
        if set(self._mock_history) != {"A", "B", "C"}:
            raise ValueError("mock_history must contain A, B, and C scenario profiles")

    def get_evidence(self, prediction: Mapping[str, Any]) -> dict[str, Any]:
        """Return evidence for the exact scenario already declared by prediction.

        The prediction engine is the sole owner of scenario detection. This
        method validates ``prediction['scenario']`` but never recalculates it
        from ``risk_score``.
        """
        risk_score, scenario = self._validate_prediction(prediction)
        evidence = self._lookup_evidence_by_scenario(scenario)
        return {
            "similar_cases": evidence["similar_cases"], "success_rate": evidence["success_rate"],
            "avg_stabilization_minutes": evidence["avg_stabilization_minutes"],
            "evidence_type": "historical_transitions", "scenario": scenario,
            "risk_score_range": evidence["risk_range"], "data_quality": "verified",
            "risk_score": risk_score,
        }

    def get_evidence_for_risk_range(self, risk_score: float) -> dict[str, Any]:
        """Perform a direct risk-range lookup when no prediction is available."""
        try:
            value = float(risk_score)
        except (TypeError, ValueError) as exc:
            raise ValueError("risk_score must be numeric") from exc
        if not isfinite(value) or not 0 <= value <= 100:
            raise ValueError("risk_score must be between 0 and 100")
        scenario = "B" if value >= 75 else "A" if value >= 30 else "C"
        return self.get_evidence({"risk_score": value, "scenario": scenario})

    def get_similar_transitions(self, scenario: str) -> dict[str, Any]:
        """Return complete comparable-transition statistics for one scenario."""
        evidence = self._lookup_evidence_by_scenario(scenario)
        success_cases = self._calculate_success_cases(evidence["similar_cases"], evidence["success_rate"])
        return {
            "scenario": scenario, "similar_cases": evidence["similar_cases"],
            "success_rate": evidence["success_rate"],
            "avg_stabilization_minutes": evidence["avg_stabilization_minutes"],
            "success_cases": success_cases, "failed_cases": evidence["similar_cases"] - success_cases,
        }

    def get_engine_info(self) -> dict[str, Any]:
        """Return mock-source metadata for diagnostics and future integration."""
        profiles = list(self._mock_history.values())
        return {
            "engine_name": "HistoricalEvidenceEngine", "data_source": "Mock historical transitions (hackathon)",
            "scenarios": sorted(self._mock_history),
            "total_transitions_available": sum(profile["similar_cases"] for profile in profiles),
            "average_success_rate": round(sum(profile["success_rate"] for profile in profiles) / len(profiles), 1),
            "implementation": "Deterministic scenario-based lookup", "version": "1.0",
        }

    def get_risk_score_ranges(self) -> dict[str, dict[str, float]]:
        """Return direct risk-range lookup metadata for all scenarios."""
        return {
            scenario: {"min": profile["risk_range"][0], "max": profile["risk_range"][1], "center": profile["typical_risk_score"]}
            for scenario, profile in self._mock_history.items()
        }

    @staticmethod
    def _validate_prediction(prediction: Mapping[str, Any]) -> tuple[float, str]:
        if not isinstance(prediction, Mapping) or "risk_score" not in prediction or "scenario" not in prediction:
            raise ValueError("prediction must include risk_score and scenario")
        try:
            risk_score = float(prediction["risk_score"])
        except (TypeError, ValueError) as exc:
            raise ValueError("prediction risk_score must be numeric") from exc
        if not isfinite(risk_score) or not 0 <= risk_score <= 100:
            raise ValueError("prediction risk_score must be between 0 and 100")
        scenario = prediction["scenario"]
        if scenario not in {"A", "B", "C"}:
            raise ValueError("prediction scenario must be A, B, or C")
        return risk_score, scenario

    def _lookup_evidence_by_scenario(self, scenario: str) -> dict[str, Any]:
        if scenario not in self._mock_history:
            raise ValueError("scenario must be A, B, or C")
        return self._mock_history[scenario].copy()

    @staticmethod
    def _calculate_success_cases(similar_cases: int, success_rate: float) -> int:
        return round(similar_cases * success_rate / 100)
