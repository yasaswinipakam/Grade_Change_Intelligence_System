"""Tests for structured-action, decoupled safety validation."""

import pytest

from ml.constraint_validation_engine import ConstraintValidationEngine


def state(stock_flow=150.0, grade="Copy Paper 20lb"):
    return {"grade": grade, "stock_flow": stock_flow, "steam_pressure": 8.5, "machine_speed": 900.0, "moisture": 5.2, "basis_weight": 20.2}


def action(parameter="stock_flow", operation="decrease", change_percent=2.0):
    return {"parameter": parameter, "operation": operation, "change_percent": change_percent}


def test_valid_action_passes_all_layers() -> None:
    result = ConstraintValidationEngine().validate(action(), state(), {"scenario": "A", "risk_score": 68})
    assert result["validation_status"] == "pass"
    assert result["passed_layers"] == ["recipe", "machine", "historical"]
    assert result["severity"] == "none"
    assert result["proposed_value"] == 147.0


def test_recipe_machine_and_historical_outcomes() -> None:
    engine = ConstraintValidationEngine()
    recipe_fail = engine.validate(action(change_percent=40), state(), {"scenario": "A"})
    assert recipe_fail["validation_status"] == "fail" and recipe_fail["severity"] == "error"
    machine_fail = engine.validate(action(operation="increase", change_percent=100), state(stock_flow=400), {"scenario": "A"})
    assert machine_fail["validation_status"] == "fail" and "machine" in machine_fail["failed_layers"]
    warning = engine.validate(action(parameter="steam_pressure", operation="increase", change_percent=15), state(), {"scenario": "B"})
    assert warning["validation_status"] == "pass" and warning["severity"] == "warning"


def test_structured_input_metadata_and_validation() -> None:
    engine = ConstraintValidationEngine()
    single = engine.validate_parameter("stock_flow", 150, "Copy Paper 20lb", "A")
    assert all(result["passed"] for result in single.values())
    assert engine.get_recipe_constraints("Copy Paper 20lb")["stock_flow"] == (100.0, 200.0)
    assert engine.get_machine_limits()["machine_speed"] == (0.0, 2000.0)
    assert engine.get_historical_safe_ranges("C")["stock_flow"] == (130.0, 160.0)
    assert engine.get_engine_info()["constraint_layers"] == 3
    with pytest.raises(ValueError):
        engine.validate("Reduce Stock Flow: 2%", state(), {"scenario": "A"})
    with pytest.raises(ValueError):
        engine.validate({"parameter": "stock_flow", "operation": "decrease"}, state(), {"scenario": "A"})
    with pytest.raises(ValueError):
        engine.validate(action(), state(), {"scenario": "Z"})
