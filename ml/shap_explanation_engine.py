"""Stateless, SHAP-compatible presentation of self-contained predictions.

The engine translates prediction output into UI-ready contribution objects. It
does not receive feature vectors, make predictions, detect scenarios, or encode
scenario-specific operating logic.
"""

from __future__ import annotations

from math import isfinite
from typing import Any, Mapping, Sequence


class SHAPExplanationEngine:
    """Convert prediction dictionaries into deterministic local explanations."""

    def explain(self, prediction: Mapping[str, Any]) -> dict[str, Any]:
        """Build contribution objects, top drivers, and a concise decision trace.

        ``prediction`` must be the self-contained result returned by
        ``PredictionEngine.predict()``, including risk, deviation, lead time,
        scenario, and ordered feature-importance tuples.
        """
        normalized = self._validate_prediction(prediction)
        contributions = self._generate_feature_contributions(normalized["feature_importance"])
        return {
            "features": contributions,
            "top_3_drivers": [item["name"] for item in contributions[:3]],
            "decision_trace": self._generate_decision_trace(normalized, contributions),
        }

    @staticmethod
    def get_explanation_config() -> dict[str, object]:
        """Return stable display semantics for dashboards and future SHAP swaps."""
        return {
            "top_drivers_count": 3,
            "contribution_thresholds": {
                "positive": "Highest-ranked local driver",
                "negative": "Supporting stabilizing factor",
                "neutral": "Lower-ranked local factor",
            },
            "decision_trace_style": "business-friendly, operator-focused, 2-3 sentences",
        }

    @staticmethod
    def _validate_prediction(prediction: Mapping[str, Any]) -> dict[str, Any]:
        required = ("risk_score", "predicted_deviation", "lead_time_minutes", "scenario", "feature_importance")
        if not isinstance(prediction, Mapping) or any(key not in prediction for key in required):
            raise ValueError("prediction must include risk_score, predicted_deviation, lead_time_minutes, scenario, and feature_importance")
        try:
            risk_score = float(prediction["risk_score"])
            deviation = float(prediction["predicted_deviation"])
            lead_time = int(prediction["lead_time_minutes"])
        except (TypeError, ValueError) as exc:
            raise ValueError("prediction values must be numeric") from exc
        if not isfinite(risk_score) or not 0 <= risk_score <= 100:
            raise ValueError("prediction risk_score must be between 0 and 100")
        if not isfinite(deviation) or lead_time <= 0:
            raise ValueError("prediction deviation must be finite and lead_time_minutes must be positive")
        if prediction["scenario"] not in {"A", "B", "C"}:
            raise ValueError("prediction scenario must be A, B, or C")
        return {
            "risk_score": risk_score, "predicted_deviation": deviation,
            "lead_time_minutes": lead_time, "scenario": prediction["scenario"],
            "feature_importance": prediction["feature_importance"],
        }

    @staticmethod
    def _generate_feature_contributions(feature_importance: Sequence[tuple[str, float]]) -> list[dict[str, Any]]:
        if not feature_importance or len(feature_importance) < 3:
            raise ValueError("feature_importance must contain at least three model drivers")
        contributions: list[dict[str, Any]] = []
        # This is a generic presentation convention, not scenario knowledge:
        # rank one is the strongest risk driver, rank two is supporting, rank
        # three is lower-impact. A real SHAP implementation can replace it with
        # signed SHAP values without changing the public output shape.
        directions = ("positive", "negative", "neutral")
        for index, item in enumerate(feature_importance):
            if not isinstance(item, (tuple, list)) or len(item) != 2 or not isinstance(item[0], str) or not item[0]:
                raise ValueError("feature_importance entries must be (name, importance) pairs")
            try:
                importance = float(item[1])
            except (TypeError, ValueError) as exc:
                raise ValueError("feature importance values must be numeric") from exc
            if not isfinite(importance) or not 0 <= importance <= 100:
                raise ValueError("feature importance values must be between 0 and 100")
            contributions.append({"name": item[0], "importance": importance, "contribution": directions[index % 3]})
        if abs(sum(item["importance"] for item in contributions) - 100.0) > 1e-9:
            raise ValueError("feature importance percentages must sum to 100")
        return sorted(contributions, key=lambda item: item["importance"], reverse=True)

    @staticmethod
    def _generate_decision_trace(prediction: Mapping[str, Any], contributions: Sequence[Mapping[str, Any]]) -> str:
        primary = contributions[0]["name"].replace("_", " ").title()
        supporting = " and ".join(item["name"].replace("_", " ") for item in contributions[1:3])
        return (
            f"{primary} is the primary contributor to the projected basis weight change, with {supporting} as supporting factors. "
            f"The system forecasts a {float(prediction['predicted_deviation']):+.1f}% deviation within the next {int(prediction['lead_time_minutes'])} minutes. "
            "Use this lead time to review operating settings and maintain stable production."
        )
