"""Final contract checks for the 15-feature prediction processor."""

from collections import OrderedDict

import numpy as np
import pytest

from ml.prediction_feature_processor import PredictionFeatureProcessor


def reading(basis_weight: float, stock_flow: float = 150.0) -> dict[str, float]:
    return {
        "stock_flow": stock_flow, "steam_pressure": 8.5, "machine_speed": 900.0,
        "moisture": 5.2, "basis_weight": basis_weight,
    }


def test_all_scenarios_emit_canonical_numeric_features() -> None:
    for basis_weight in (20.2, 18.8, 19.5):
        processor = PredictionFeatureProcessor()
        features = processor.process(reading(basis_weight))
        assert isinstance(features, OrderedDict)
        assert len(features) == processor.get_feature_count() == 15
        assert list(features) == processor.get_feature_names()
        assert all(isinstance(value, float) for value in features.values())
        assert features["stock_flow_velocity"] == 0.0
        assert features["basis_weight_direction"] == 0.0
        assert features["stock_flow_x_steam_pressure"] == 1275.0


def test_velocity_trajectory_history_and_direction() -> None:
    processor = PredictionFeatureProcessor(history_size=3)
    first = processor.process(reading(20.0, 150.0))
    second = processor.process(reading(20.1, 152.0))
    third = processor.process(reading(20.3, 154.0))
    assert first["basis_weight_velocity"] == 0.0
    assert second["stock_flow_velocity"] == 2.0
    assert second["basis_weight_trend"] == 0.0  # Requires three samples.
    assert third["basis_weight_trend"] > 0.05
    assert third["basis_weight_direction"] == 1.0
    assert len(processor.get_history()) == 3
    processor.process(reading(20.5, 156.0))
    assert len(processor.get_history()) == 3


def test_stateless_array_conversion_and_metadata() -> None:
    processor = PredictionFeatureProcessor()
    features = processor.process(reading(19.5))
    first = processor.to_array(features)
    second = processor.to_array(features)
    assert first.shape == (15,)
    assert first.dtype == float
    assert np.array_equal(first, second)
    assert first.tolist() == list(features.values())
    info = processor.get_feature_info()
    assert info["feature_categories"] == {"raw": 5, "velocity": 4, "interaction": 3, "trajectory": 3}
    assert info["output_features"] == 15


@pytest.mark.parametrize(
    "bad_input",
    [
        {"stock_flow": -1, "steam_pressure": 8.5, "machine_speed": 900, "moisture": 5.2, "basis_weight": 20.2},
        {"stock_flow": 150, "steam_pressure": 8.5, "machine_speed": 900, "moisture": 150, "basis_weight": 20.2},
        {"stock_flow": "150", "steam_pressure": 8.5, "machine_speed": 900, "moisture": 5.2, "basis_weight": 20.2},
        {"stock_flow": 150, "steam_pressure": 8.5, "machine_speed": 900, "basis_weight": 20.2},
    ],
)
def test_validation_errors_are_clear(bad_input) -> None:
    with pytest.raises(ValueError):
        PredictionFeatureProcessor().process(bad_input)


def test_array_requires_canonical_order() -> None:
    processor = PredictionFeatureProcessor()
    features = processor.process(reading(20.2))
    reordered = OrderedDict(reversed(list(features.items())))
    with pytest.raises(ValueError):
        processor.to_array(reordered)
