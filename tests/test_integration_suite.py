"""End-to-end interaction tests for the predictive decision-support pipeline."""

import pytest

from constraint_validation_engine import ConstraintValidationEngine
from historical_evidence_engine import HistoricalEvidenceEngine
from prediction_engine import PredictionEngine
from prediction_feature_processor import PredictionFeatureProcessor
from shap_explanation_engine import SHAPExplanationEngine
from test_utils import SCENARIOS, api_client, assert_response_fields, current_state, engineered_payload


def _direct_pipeline(scenario_key: str):
    scenario = SCENARIOS[scenario_key]
    processor = PredictionFeatureProcessor()
    engine = PredictionEngine(processor.get_feature_names(), processor.get_feature_count())
    features = processor.process(scenario["raw"])
    prediction = engine.predict(processor.to_array(features))
    evidence = HistoricalEvidenceEngine().get_evidence(prediction)
    explanation = SHAPExplanationEngine().explain(prediction)
    return scenario, features, prediction, evidence, explanation


def test_component_compatibility_and_data_flow() -> None:
    """Processor, prediction, evidence, and explanation outputs interoperate."""
    _, features, prediction, evidence, explanation = _direct_pipeline("A")
    assert len(features) == 15
    assert_response_fields(prediction, {"risk_score", "predicted_deviation", "lead_time_minutes", "scenario", "feature_importance"})
    assert evidence["scenario"] == prediction["scenario"]
    assert explanation["top_3_drivers"] == [item[0] for item in prediction["feature_importance"]]
    assert [item["importance"] for item in explanation["features"]] == [item[1] for item in prediction["feature_importance"]]


@pytest.mark.parametrize("scenario_key", ["A", "B", "C"])
def test_scenario_full_pipeline_api_and_validation(scenario_key: str) -> None:
    """Run predict → recommend → explain and validate returned structured actions."""
    scenario = SCENARIOS[scenario_key]
    client = api_client()
    predict = client.post("/api/v1/predict", json=scenario["raw"])
    assert predict.status_code == 200
    prediction = predict.json()
    assert prediction["risk_score"] == scenario["risk"]
    assert_response_fields(prediction, {"scenario", "feature_importance"})

    recommend = client.post("/api/v1/recommend", json={"risk_score": prediction["risk_score"], "predicted_deviation": prediction["predicted_deviation"]})
    assert recommend.status_code == 200
    recommendation = recommend.json()
    assert recommendation["action"] == scenario["action"]
    assert recommendation["structured_actions"]

    validator = ConstraintValidationEngine()
    for action in recommendation["structured_actions"]:
        validation = validator.validate(action, current_state(scenario), prediction)
        assert validation["validation_status"] == "pass"

    explain = client.post("/api/v1/explain", json={**engineered_payload(scenario["raw"]), "recommendation_id": recommendation["recommendation_id"]})
    assert explain.status_code == 200
    explanation = explain.json()
    assert_response_fields(explanation, {"features", "top_3_drivers", "decision_trace"})
    assert len(explanation["top_3_drivers"]) == 3


def test_constraint_boundary_workflows() -> None:
    """Recipe failures block while historical-only range violations remain warnings."""
    validator = ConstraintValidationEngine()
    recipe_failure = validator.validate({"parameter": "stock_flow", "operation": "decrease", "change_percent": 40}, current_state(SCENARIOS["A"]), {"scenario": "A"})
    assert recipe_failure["validation_status"] == "fail"
    assert recipe_failure["severity"] == "error"

    historical_warning = validator.validate({"parameter": "steam_pressure", "operation": "increase", "change_percent": 16}, current_state(SCENARIOS["B"]), {"scenario": "B"})
    assert historical_warning["validation_status"] == "pass"
    assert historical_warning["severity"] == "warning"


@pytest.mark.parametrize("operator_response", ["accept", "reject"])
def test_operator_feedback_workflows(operator_response: str) -> None:
    """A generated recommendation remains traceable through either feedback outcome."""
    client = api_client()
    scenario = SCENARIOS["A"]
    prediction = client.post("/api/v1/predict", json=scenario["raw"]).json()
    recommendation = client.post("/api/v1/recommend", json={"risk_score": prediction["risk_score"], "predicted_deviation": prediction["predicted_deviation"]}).json()
    response = client.post("/api/v1/feedback", json={"recommendation_id": recommendation["recommendation_id"], "operator_response": operator_response, "timestamp": "2026-07-25T15:00:00Z"})
    assert response.status_code == 200
    assert response.json()["recommendation_id"] == recommendation["recommendation_id"]
    assert response.json()["status"] == "success"


def test_api_error_recovery_and_missing_recommendation() -> None:
    """An invalid request does not prevent subsequent valid pipeline work."""
    client = api_client()
    invalid = client.post("/api/v1/predict", json={"basis_weight": -1})
    assert invalid.status_code == 400 and invalid.json()["error"] == "ValidationError"
    valid = client.post("/api/v1/predict", json=SCENARIOS["C"]["raw"])
    assert valid.status_code == 200 and valid.json()["risk_score"] == 22
    missing = client.post("/api/v1/feedback", json={"recommendation_id": "550e8400-e29b-41d4-a716-446655440000", "operator_response": "accept", "timestamp": "2026-07-25T15:00:00Z"})
    assert missing.status_code == 404 and missing.json()["error"] == "NotFoundError"


@pytest.mark.parametrize("scenario_key", ["A", "B", "C"])
def test_pipeline_determinism(scenario_key: str) -> None:
    """Fresh compositions give identical end-to-end component outputs."""
    first = _direct_pipeline(scenario_key)[2:]
    second = _direct_pipeline(scenario_key)[2:]
    assert first == second
