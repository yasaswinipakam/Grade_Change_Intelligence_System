"""Tests for stateless, scenario-trusting historical evidence lookup."""

import pytest

from ml.historical_evidence_engine import HistoricalEvidenceEngine
from ml.prediction_engine import PredictionEngine
from ml.prediction_feature_processor import PredictionFeatureProcessor


def prediction_for(basis_weight: float) -> dict[str, object]:
    processor = PredictionFeatureProcessor()
    engine = PredictionEngine(processor.get_feature_names(), processor.get_feature_count())
    features = processor.process({"stock_flow": 150, "steam_pressure": 8.5, "machine_speed": 900, "moisture": 5.2, "basis_weight": basis_weight})
    return engine.predict(processor.to_array(features))


@pytest.mark.parametrize(
    ("basis_weight", "scenario", "cases", "success", "minutes"),
    [(20.2, "A", 18, 89.0, 8), (18.8, "B", 5, 60.0, 15), (19.5, "C", 42, 98.0, 2)],
)
def test_prediction_integration_uses_declared_scenario(basis_weight, scenario, cases, success, minutes) -> None:
    evidence = HistoricalEvidenceEngine().get_evidence(prediction_for(basis_weight))
    assert evidence["scenario"] == scenario
    assert (evidence["similar_cases"], evidence["success_rate"], evidence["avg_stabilization_minutes"]) == (cases, success, minutes)


def test_prediction_scenario_is_trusted_not_reclassified() -> None:
    evidence = HistoricalEvidenceEngine().get_evidence({"risk_score": 84, "scenario": "A"})
    assert evidence["scenario"] == "A"
    assert evidence["similar_cases"] == 18


def test_direct_ranges_statistics_metadata_and_validation() -> None:
    engine = HistoricalEvidenceEngine()
    assert engine.get_evidence_for_risk_range(30)["scenario"] == "A"
    assert engine.get_evidence_for_risk_range(75)["scenario"] == "B"
    transitions = engine.get_similar_transitions("A")
    assert transitions["success_cases"] == 16 and transitions["failed_cases"] == 2
    assert engine.get_engine_info()["total_transitions_available"] == 65
    assert engine.get_risk_score_ranges()["C"]["center"] == 22.0
    with pytest.raises(ValueError):
        engine.get_evidence({"risk_score": 68})
    with pytest.raises(ValueError):
        engine.get_evidence({"risk_score": 101, "scenario": "A"})
    with pytest.raises(ValueError):
        engine.get_evidence({"risk_score": 68, "scenario": "Z"})
