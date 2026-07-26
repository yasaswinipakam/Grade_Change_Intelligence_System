"""Feature engineering for real-time paper-mill grade-change measurements.

``PredictionFeatureProcessor`` owns a bounded observation history and transforms
one raw measurement into a deterministic, fully numeric 15-feature vector. It
performs no normalization, prediction, scenario classification, I/O, or web work.
"""

from __future__ import annotations

from collections import OrderedDict, deque
from datetime import datetime
from typing import Deque, Dict, List, Mapping, Tuple

import numpy as np


class PredictionFeatureProcessor:
    """Turn raw paper-machine observations into canonical model features."""

    RAW_FEATURES = ["stock_flow", "steam_pressure", "machine_speed", "moisture", "basis_weight"]
    VELOCITY_FEATURES = [
        "stock_flow_velocity", "steam_pressure_velocity", "machine_speed_velocity", "basis_weight_velocity"
    ]
    INTERACTION_FEATURES = [
        "stock_flow_x_steam_pressure", "stock_flow_x_machine_speed", "steam_pressure_x_machine_speed"
    ]
    TRAJECTORY_FEATURES = ["basis_weight_trend", "basis_weight_direction", "basis_weight_acceleration"]
    VALIDATION_RANGES: Dict[str, Tuple[float, float]] = {
        "stock_flow": (0.0, 500.0), "steam_pressure": (0.0, 20.0),
        "machine_speed": (0.0, 2000.0), "moisture": (0.0, 100.0),
        "basis_weight": (0.0, 500.0),
    }
    DIRECTION_THRESHOLD = 0.05

    def __init__(self, history_size: int = 10) -> None:
        """Initialize canonical metadata and a rolling observation history."""
        if not isinstance(history_size, int) or history_size <= 0:
            raise ValueError("history_size must be a positive integer")
        self._history: Deque[Dict[str, float]] = deque(maxlen=history_size)
        self._timestamps: Deque[datetime] = deque(maxlen=history_size)
        self._feature_names = (
            self.RAW_FEATURES + self.VELOCITY_FEATURES + self.INTERACTION_FEATURES + self.TRAJECTORY_FEATURES
        )

    def process(self, raw_data: Mapping[str, float]) -> OrderedDict[str, float]:
        """Validate and engineer one raw observation into 15 ordered features."""
        self._validate_input(raw_data)
        current = {name: float(raw_data[name]) for name in self.RAW_FEATURES}
        self._history.append(current)
        self._timestamps.append(datetime.now())

        features: Dict[str, float] = {}
        features.update(current)
        features.update(self._calculate_velocity_features(current))
        features.update(self._calculate_interaction_features(current))
        features.update(self._calculate_trajectory_features())
        return OrderedDict((name, float(features[name])) for name in self._feature_names)

    def to_array(self, features: Mapping[str, float]) -> np.ndarray:
        """Convert a supplied ordered feature mapping into a 15-value float array.

        The method is stateless: callers explicitly supply the vector they want
        converted, making conversion deterministic and straightforward to test.
        """
        if not isinstance(features, Mapping):
            raise ValueError("features must be an OrderedDict or mapping from process()")
        if list(features.keys()) != self._feature_names:
            raise ValueError("features must use the canonical processor feature ordering")
        try:
            values = np.asarray(list(features.values()), dtype=float)
        except (TypeError, ValueError) as exc:
            raise ValueError("features must contain only numeric values") from exc
        if values.shape != (self.get_feature_count(),) or not np.isfinite(values).all():
            raise ValueError("features must contain exactly 15 finite numeric values")
        return values

    def get_feature_names(self) -> List[str]:
        """Return the canonical feature ordering shared by engine and explainer."""
        return self._feature_names.copy()

    def get_feature_count(self) -> int:
        """Return the total engineered feature count (15)."""
        return len(self._feature_names)

    def feature_count(self) -> int:
        """Backward-compatible alias for :meth:`get_feature_count`."""
        return self.get_feature_count()

    def get_feature_info(self) -> dict[str, object]:
        """Return feature metadata useful for diagnostics and model validation."""
        return {
            "input_features": len(self.RAW_FEATURES), "output_features": self.get_feature_count(),
            "history_size": self._history.maxlen, "feature_names": self.get_feature_names(),
            "validation_ranges": self.VALIDATION_RANGES.copy(),
            "feature_categories": {
                "raw": len(self.RAW_FEATURES), "velocity": len(self.VELOCITY_FEATURES),
                "interaction": len(self.INTERACTION_FEATURES), "trajectory": len(self.TRAJECTORY_FEATURES),
            },
        }

    def get_history(self) -> Deque[Dict[str, float]]:
        """Return a copy of the bounded raw-observation history for inspection."""
        return deque((item.copy() for item in self._history), maxlen=self._history.maxlen)

    def reset_history(self) -> None:
        """Clear rolling observations and timestamps between isolated scenarios."""
        self._history.clear()
        self._timestamps.clear()

    def validate_inputs(self, raw_data: Mapping[str, float]) -> bool:
        """Compatibility helper returning ``True`` or ``False`` without mutation."""
        try:
            self._validate_input(raw_data)
        except ValueError:
            return False
        return True

    def _validate_input(self, raw_data: Mapping[str, float]) -> bool:
        """Validate required fields, finite numeric values, and engineering ranges."""
        if not isinstance(raw_data, Mapping):
            raise ValueError("raw_data must be a mapping")
        for name in self.RAW_FEATURES:
            if name not in raw_data:
                raise ValueError(f"missing required field: {name}")
            # Strings are deliberately rejected even when they could be coerced.
            if isinstance(raw_data[name], bool) or not isinstance(raw_data[name], (int, float)):
                raise ValueError(f"{name} must be numeric")
            value = float(raw_data[name])
            lower, upper = self.VALIDATION_RANGES[name]
            if not np.isfinite(value) or not lower <= value <= upper:
                raise ValueError(f"{name} must be between {lower:g} and {upper:g}")
        return True

    def _calculate_velocity_features(self, current: Mapping[str, float]) -> Dict[str, float]:
        """Return current-minus-previous velocities, defaulting to zero initially."""
        previous = self._history[-2] if len(self._history) >= 2 else None
        source_names = ("stock_flow", "steam_pressure", "machine_speed", "basis_weight")
        return {
            f"{name}_velocity": 0.0 if previous is None else float(current[name] - previous[name])
            for name in source_names
        }

    @staticmethod
    def _calculate_interaction_features(current: Mapping[str, float]) -> Dict[str, float]:
        """Return unscaled products representing coupled operating conditions."""
        return {
            "stock_flow_x_steam_pressure": float(current["stock_flow"] * current["steam_pressure"]),
            "stock_flow_x_machine_speed": float(current["stock_flow"] * current["machine_speed"]),
            "steam_pressure_x_machine_speed": float(current["steam_pressure"] * current["machine_speed"]),
        }

    def _calculate_trajectory_features(self) -> Dict[str, float]:
        """Return basis-weight slope, numeric direction, and change in slope."""
        values = deque((item["basis_weight"] for item in self._history), maxlen=self._history.maxlen)
        if len(values) < 3:
            return {"basis_weight_trend": 0.0, "basis_weight_direction": 0.0, "basis_weight_acceleration": 0.0}
        trend = self._fit_trend(values)
        previous_trend = self._fit_trend(deque(list(values)[:-1])) if len(values) > 3 else 0.0
        return {
            "basis_weight_trend": trend,
            "basis_weight_direction": float(self._determine_direction(trend)),
            "basis_weight_acceleration": float(trend - previous_trend),
        }

    @staticmethod
    def _fit_trend(history: Deque[float]) -> float:
        """Estimate least-squares basis-weight slope over a sequence of samples."""
        if len(history) < 2:
            return 0.0
        y = np.asarray(history, dtype=float)
        x = np.arange(y.size, dtype=float)
        centered_x = x - x.mean()
        denominator = float(np.dot(centered_x, centered_x))
        return 0.0 if denominator == 0.0 else float(np.dot(centered_x, y - y.mean()) / denominator)

    def _determine_direction(self, trend: float) -> int:
        """Encode slope direction as 1 (rising), 0 (stable), or -1 (falling)."""
        if trend > self.DIRECTION_THRESHOLD:
            return 1
        if trend < -self.DIRECTION_THRESHOLD:
            return -1
        return 0
