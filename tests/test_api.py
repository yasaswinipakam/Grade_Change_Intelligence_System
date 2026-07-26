"""End-to-end API tests for all deterministic demo scenarios."""

from uuid import UUID

from fastapi.testclient import TestClient

from main import app
from prediction_feature_processor import PredictionFeatureProcessor


client = TestClient(app)


def _predict_recommend_explain_feedback(basis_weight: float, risk: int, action: str) -> None:
    predict = client.post("/api/v1/predict", json={
        "stock_flow": 150, "steam_pressure": 8.5, "machine_speed": 900,
        "moisture": 5.2, "basis_weight": basis_weight,
    })
    assert predict.status_code == 200
    prediction = predict.json()
    assert prediction["risk_score"] == risk

    recommend = client.post("/api/v1/recommend", json={
        "risk_score": risk, "predicted_deviation": prediction["predicted_deviation"],
    })
    assert recommend.status_code == 200
    recommendation = recommend.json()
    UUID(recommendation["recommendation_id"])
    assert recommendation["action"] == action

    processor = PredictionFeatureProcessor()
    features = processor.process({
        "stock_flow": 150, "steam_pressure": 8.5, "machine_speed": 900,
        "moisture": 5.2, "basis_weight": basis_weight,
    })
    explain = client.post("/api/v1/explain", json={
        "feature_vector": list(features.values()),
        "feature_names": processor.get_feature_names(),
        "recommendation_id": recommendation["recommendation_id"],
    })
    assert explain.status_code == 200
    explanation = explain.json()
    assert explanation["features"] == sorted(explanation["features"], key=lambda item: item["importance"], reverse=True)

    feedback = client.post("/api/v1/feedback", json={
        "recommendation_id": recommendation["recommendation_id"],
        "operator_response": "accept", "timestamp": "2026-07-25T14:30:00Z",
    })
    assert feedback.status_code == 200
    assert feedback.json()["status"] == "success"


def test_health() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_scenario_a_yellow_risk() -> None:
    _predict_recommend_explain_feedback(20.2, 68, "Reduce Stock Flow: 2%")


def test_scenario_b_red_risk() -> None:
    _predict_recommend_explain_feedback(18.8, 84, "Increase Steam: 3% + Reduce Speed: 1%")


def test_scenario_c_green_safe() -> None:
    _predict_recommend_explain_feedback(19.5, 22, "Maintain current parameters")


def test_errors_use_documented_statuses() -> None:
    invalid = client.post("/api/v1/predict", json={"basis_weight": 20})
    assert invalid.status_code == 400
    assert invalid.json()["error"] == "ValidationError"
    missing = client.post("/api/v1/feedback", json={
        "recommendation_id": "550e8400-e29b-41d4-a716-446655440000",
        "operator_response": "reject", "timestamp": "2026-07-25T14:30:00Z",
    })
    assert missing.status_code == 404
    assert missing.json()["error"] == "NotFoundError"
    invalid_response = client.post("/api/v1/feedback", json={
        "recommendation_id": "550e8400-e29b-41d4-a716-446655440000",
        "operator_response": "defer", "timestamp": "2026-07-25T14:30:00Z",
    })
    assert invalid_response.status_code == 400
    assert invalid_response.json()["error"] == "ValidationError"
