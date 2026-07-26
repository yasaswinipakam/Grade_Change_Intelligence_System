"""Verification of deterministic mock XGBoost prediction behavior."""

import pytest

from ml.prediction_engine import PredictionEngine
from ml.prediction_feature_processor import PredictionFeatureProcessor


def engineered_vector(basis_weight: float) -> list[float]:
    processor = PredictionFeatureProcessor()
    features = processor.process({
        "stock_flow": 150.0, "steam_pressure": 8.5, "machine_speed": 900.0,
        "moisture": 5.2, "basis_weight": basis_weight,
    })
    return list(features.values())


def engine_for(processor: PredictionFeatureProcessor) -> PredictionEngine:
    return PredictionEngine(processor.get_feature_names(), processor.get_feature_count())


@pytest.mark.parametrize(
    ("basis_weight", "risk", "deviation", "lead_time", "top_driver"),
    [
        (20.2, 68.0, 3.1, 12, "stock_flow"),
        (18.8, 84.0, -4.8, 15, "machine_speed"),
        (19.5, 22.0, 0.3, 2, "stock_flow"),
    ],
)
def test_demo_predictions_and_importance(basis_weight, risk, deviation, lead_time, top_driver) -> None:
    processor = PredictionFeatureProcessor()
    engine = engine_for(processor)
    prediction = engine.predict(engineered_vector(basis_weight))
    assert prediction["risk_score"] == risk
    assert prediction["predicted_deviation"] == deviation
    assert prediction["lead_time_minutes"] == lead_time
    assert prediction["scenario"] in {"A", "B", "C"}
    assert prediction == engine.predict(engineered_vector(basis_weight))
    importance = prediction["feature_importance"]
    assert importance[0][0] == top_driver
    assert [item[1] for item in importance] == sorted((item[1] for item in importance), reverse=True)
    assert sum(item[1] for item in importance) == 100.0


def test_processor_vector_integration_and_metadata() -> None:
    processor = PredictionFeatureProcessor()
    features = processor.process({
        "stock_flow": 150, "steam_pressure": 8.5, "machine_speed": 900,
        "moisture": 5.2, "basis_weight": 20.2,
    })
    engine = engine_for(processor)
    assert engine.get_feature_names() == processor.get_feature_names()
    assert engine.predict(features.values())["risk_score"] == 68.0
    assert engine.get_model_info()["feature_count"] == processor.feature_count() == 15


def test_invalid_vectors_raise_clear_errors() -> None:
    engine = engine_for(PredictionFeatureProcessor())
    with pytest.raises(ValueError):
        engine.predict([])
    with pytest.raises(ValueError):
        engine.predict([1.0, 2.0])
    with pytest.raises(ValueError):
        engine.predict([0.0] * 14)
    with pytest.raises(ValueError):
        engine.predict([0.0, 0.0, 0.0, 0.0, 501.0] + [0.0] * 10)
    with pytest.raises(ValueError):
        engine.predict([0.0] * 14 + ["not-a-number"])
