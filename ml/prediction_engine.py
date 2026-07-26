"""Stateless, XGBoost-compatible mock prediction engine.

The engine receives canonical feature metadata through dependency injection and
never owns a ``PredictionFeatureProcessor`` instance. A future trained XGBoost
implementation can replace only this module while keeping its public interface.
"""

from __future__ import annotations

from typing import Iterable, List, Mapping, Sequence, Tuple

import numpy as np


class PredictionEngine:
    """Return self-contained deterministic predictions from engineered vectors."""

    MODEL_VERSION = "1.0"
    SCENARIOS = {
        "A": {"name": "Yellow Risk", "risk_score": 68.0, "predicted_deviation": 3.1, "lead_time_minutes": 12,
              "feature_importance": (("stock_flow", 60.0), ("steam_pressure", 25.0), ("moisture", 15.0))},
        "B": {"name": "Red Risk", "risk_score": 84.0, "predicted_deviation": -4.8, "lead_time_minutes": 15,
              "feature_importance": (("machine_speed", 55.0), ("steam_pressure", 35.0), ("moisture", 10.0))},
        "C": {"name": "Green Safe", "risk_score": 22.0, "predicted_deviation": 0.3, "lead_time_minutes": 2,
              "feature_importance": (("stock_flow", 40.0), ("steam_pressure", 35.0), ("moisture", 25.0))},
    }

    def __init__(self, feature_names: Sequence[str], feature_count: int) -> None:
        """Inject immutable canonical feature metadata from the processor.

        ``feature_names`` and ``feature_count`` are the only processor details
        required after construction, avoiding a retained processor dependency.
        """
        if not feature_names or len(feature_names) != feature_count:
            raise ValueError("feature_names and feature_count must describe the same non-empty feature vector")
        if "basis_weight" not in feature_names:
            raise ValueError("basis_weight feature not found in feature names")
        self._feature_names = list(feature_names)
        self._feature_count = feature_count

    def predict(self, features: Sequence[float] | np.ndarray) -> dict[str, object]:
        """Return a self-contained deterministic prediction for 15 engineered features."""
        vector = self._validate_features(features)
        scenario = self._detect_scenario(float(vector[self._locate_basis_weight_index()]))
        return self._get_scenario_prediction(scenario)

    def get_feature_names(self) -> List[str]:
        """Return a copy of the injected canonical feature ordering."""
        return self._feature_names.copy()

    def get_feature_count(self) -> int:
        """Return the injected engineered-vector size."""
        return self._feature_count

    def get_feature_importance_for_risk(self, risk_score: float) -> List[Tuple[str, float]]:
        """Return model drivers for persisted recommendation context, statelessly."""
        if not np.isfinite(risk_score) or not 0 <= risk_score <= 100:
            raise ValueError("risk_score must be a finite value between 0 and 100")
        scenario = "B" if risk_score >= 75 else "A" if risk_score >= 40 else "C"
        return list(self.SCENARIOS[scenario]["feature_importance"])

    def get_model_info(self) -> dict[str, object]:
        """Return mock-model metadata for introspection and validation."""
        return {
            "model_name": "PredictionEngine", "model_type": "Mock XGBoost Interface",
            "feature_count": self._feature_count, "scenario_count": len(self.SCENARIOS),
            "implementation": "Deterministic rule-based (hackathon demo)", "version": self.MODEL_VERSION,
            "training_data": "Mock scenarios (Scenario A, B, C)",
            "feature_source": "PredictionFeatureProcessor (canonical ordering)",
        }

    def get_scenario_info(self) -> dict[str, object]:
        """Return scenario thresholds and immutable prediction definitions."""
        return {
            "detection_method": "basis_weight threshold", "basis_weight_feature": "basis_weight",
            "scenarios": {key: {**value, "feature_importance": list(value["feature_importance"])} for key, value in self.SCENARIOS.items()},
        }

    def _validate_features(self, features: Sequence[float] | np.ndarray) -> np.ndarray:
        if features is None or isinstance(features, (str, bytes)):
            raise ValueError("features must be a non-empty numeric vector")
        try:
            values: Iterable[float] = features
            vector = np.asarray(list(values), dtype=float)
        except (TypeError, ValueError) as exc:
            raise ValueError("features must contain only numeric values") from exc
        if vector.ndim != 1 or vector.size == 0 or not np.isfinite(vector).all():
            raise ValueError("features must be a non-empty one-dimensional finite numeric vector")
        if vector.size != self._feature_count:
            raise ValueError(f"feature vector must contain exactly {self._feature_count} engineered values")
        basis_weight = vector[self._locate_basis_weight_index()]
        if not 0.0 <= basis_weight <= 500.0:
            raise ValueError("engineered basis_weight must be between 0 and 500")
        return vector

    def _locate_basis_weight_index(self) -> int:
        """Locate basis weight dynamically rather than hard-coding an index."""
        try:
            return self._feature_names.index("basis_weight")
        except ValueError as exc:
            raise ValueError("basis_weight feature not found in feature names") from exc

    @staticmethod
    def _detect_scenario(basis_weight: float) -> str:
        return "A" if basis_weight >= 20.0 else "B" if basis_weight < 19.0 else "C"

    def _get_scenario_prediction(self, scenario: str) -> dict[str, object]:
        selected = self.SCENARIOS[scenario]
        return {
            "risk_score": selected["risk_score"], "predicted_deviation": selected["predicted_deviation"],
            "lead_time_minutes": selected["lead_time_minutes"], "scenario": scenario,
            "feature_importance": list(selected["feature_importance"]),
        }
