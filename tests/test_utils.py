"""Reusable fixtures and workflow helpers for pipeline integration tests."""

from typing import Any

from fastapi.testclient import TestClient

from main import app
from prediction_feature_processor import PredictionFeatureProcessor


SCENARIOS: dict[str, dict[str, Any]] = {
    "A": {"raw": {"stock_flow": 150.0, "steam_pressure": 8.5, "machine_speed": 900.0, "moisture": 5.2, "basis_weight": 20.2}, "grade": "Copy Paper 20lb", "risk": 68, "action": "Reduce Stock Flow: 2%"},
    "B": {"raw": {"stock_flow": 140.0, "steam_pressure": 7.8, "machine_speed": 850.0, "moisture": 4.9, "basis_weight": 18.8}, "grade": "Copy Paper 18lb", "risk": 84, "action": "Increase Steam: 3% + Reduce Speed: 1%"},
    "C": {"raw": {"stock_flow": 145.0, "steam_pressure": 8.0, "machine_speed": 875.0, "moisture": 5.0, "basis_weight": 19.5}, "grade": "Newsprint 24lb", "risk": 22, "action": "Maintain current parameters"},
}


def api_client() -> TestClient:
    """Return the application client used by realistic API workflows."""
    return TestClient(app)


def engineered_payload(raw: dict[str, float]) -> dict[str, list[Any]]:
    """Generate the canonical vector/name payload required by `/explain`."""
    processor = PredictionFeatureProcessor()
    features = processor.process(raw)
    return {"feature_vector": list(processor.to_array(features)), "feature_names": processor.get_feature_names()}


def current_state(scenario: dict[str, Any]) -> dict[str, Any]:
    """Build validator state by combining raw process values with grade."""
    return {**scenario["raw"], "grade": scenario["grade"]}


def assert_response_fields(payload: dict[str, Any], fields: set[str]) -> None:
    """Assert an API response contains its boundary-contract keys."""
    assert fields.issubset(payload), f"Missing fields: {fields - set(payload)}"
