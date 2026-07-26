"""Tests for framework-agnostic SHAPExplanationEngine behavior."""

import re

import pytest

from ml.prediction_engine import PredictionEngine
from ml.prediction_feature_processor import PredictionFeatureProcessor
from ml.shap_explanation_engine import SHAPExplanationEngine


def prediction_inputs(basis_weight: float = 20.2):
    processor = PredictionFeatureProcessor()
    features = processor.process({
        "stock_flow": 150.0, "steam_pressure": 8.5, "machine_speed": 900.0,
        "moisture": 5.2, "basis_weight": basis_weight,
    })
    engine = PredictionEngine(processor.get_feature_names(), processor.get_feature_count())
    prediction = engine.predict(list(features.values()))
    return prediction, engine


def test_prediction_engine_integration_preserves_importance() -> None:
    prediction, engine = prediction_inputs()
    explainer = SHAPExplanationEngine()
    explanation = explainer.explain(prediction)
    assert [item["importance"] for item in explanation["features"]] == [60.0, 25.0, 15.0]
    assert [item["contribution"] for item in explanation["features"]] == ["positive", "negative", "neutral"]
    assert explanation["top_3_drivers"] == ["stock_flow", "steam_pressure", "moisture"]
    assert len(re.findall(r"(?<!\d)\.(?:\s|$)", explanation["decision_trace"])) == 3
    assert "+3.1%" in explanation["decision_trace"]
    assert "12 minutes" in explanation["decision_trace"]


def test_explanation_is_deterministic_and_sorted() -> None:
    prediction, engine = prediction_inputs(18.8)
    explainer = SHAPExplanationEngine()
    first = explainer.explain(prediction)
    second = explainer.explain(prediction)
    assert first == second
    assert first["features"] == sorted(first["features"], key=lambda item: item["importance"], reverse=True)
    assert sum(item["importance"] for item in first["features"]) == 100.0


@pytest.mark.parametrize(
    "prediction",
    [
        {"risk_score": 68, "predicted_deviation": 3.1, "lead_time_minutes": 12, "scenario": "A"},
        {"risk_score": 68, "predicted_deviation": 3.1, "lead_time_minutes": 12, "scenario": "A", "feature_importance": []},
        {"risk_score": 68, "predicted_deviation": 3.1, "lead_time_minutes": 12, "scenario": "A", "feature_importance": [("stock_flow", 50), ("steam", 25), ("moisture", 15)]},
    ],
)
def test_invalid_inputs_raise_value_error(prediction) -> None:
    explainer = SHAPExplanationEngine()
    with pytest.raises(ValueError):
        explainer.explain(prediction)
