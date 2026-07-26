"""Configurable Task 8 safety gate; it validates but never creates recommendations."""
from __future__ import annotations
import json
from pathlib import Path
from simulator.config import RANGES, RECIPES

# Default: data/config/constraints.json relative to project root (parent of ml/)
_DEFAULT_CONSTRAINTS = Path(__file__).resolve().parent.parent / "data" / "config" / "constraints.json"

class ConstraintValidationEngine:
    def __init__(self, config_path=None):
        path = Path(config_path) if config_path is not None else _DEFAULT_CONSTRAINTS
        self.config=json.loads(path.read_text())


    # Compatibility contracts for the original, lightweight API.  This remains
    # intentionally separate from the Task 8 actuator gate below: the former
    # validates structured actions produced by the legacy demo API, while the
    # latter validates a SHAP-traceable recommendation object.
    _legacy_recipe_constraints = {
        "Copy Paper 20lb": {
            "stock_flow": (100.0, 200.0), "steam_pressure": (7.0, 10.0),
            "machine_speed": (700.0, 1100.0), "moisture": (4.0, 6.5),
            "basis_weight": (19.0, 21.0),
        },
        "Copy Paper 18lb": {
            "stock_flow": (90.0, 190.0), "steam_pressure": (6.5, 10.0),
            "machine_speed": (650.0, 1050.0), "moisture": (4.0, 6.5),
            "basis_weight": (17.0, 19.0),
        },
        "Newsprint 24lb": {
            "stock_flow": (120.0, 220.0), "steam_pressure": (6.5, 10.5),
            "machine_speed": (700.0, 1150.0), "moisture": (4.0, 6.5),
            "basis_weight": (23.0, 25.0),
        },
    }
    _legacy_machine_limits = {
        "stock_flow": (0.0, 500.0), "steam_pressure": (0.0, 20.0),
        "machine_speed": (0.0, 2000.0), "moisture": (0.0, 100.0),
        "basis_weight": (0.0, 100.0),
    }
    _legacy_historical_ranges = {
        "A": {"stock_flow": (130.0, 180.0), "steam_pressure": (7.5, 9.5), "machine_speed": (750.0, 1000.0), "moisture": (4.5, 6.0), "basis_weight": (19.2, 20.8)},
        "B": {"stock_flow": (120.0, 170.0), "steam_pressure": (7.0, 9.0), "machine_speed": (700.0, 950.0), "moisture": (4.2, 5.8), "basis_weight": (17.2, 18.8)},
        "C": {"stock_flow": (130.0, 160.0), "steam_pressure": (7.0, 9.5), "machine_speed": (750.0, 1000.0), "moisture": (4.5, 6.0), "basis_weight": (23.0, 25.0)},
    }

    def validate(self, recommendation: dict, current_state: dict | None = None,
                 prediction: dict | None = None) -> dict:
        """Validate either a Task 8 recommendation or a legacy structured action.

        `current_state` and `prediction` select the stable legacy adapter used
        by the existing demo endpoints.  A single recommendation argument
        preserves the Task 8 contract consumed by the FastAPI backend.
        """
        if current_state is not None or prediction is not None:
            return self._validate_legacy_action(recommendation, current_state, prediction)
        return self._validate_task8(recommendation)

    def _validate_task8(self, recommendation: dict) -> dict:
        action=recommendation["primary_recommendation"]; grade=recommendation["grade"]; phase=recommendation["process_phase"]; control=action["control"]
        base={"recommendation_id":recommendation["prediction_id"],"grade":grade,"process_phase":phase,"original_recommendation":action["recommendation"],"traceability":recommendation["traceability"]}
        if control == "maintain": return {**base,"validation_state":"APPROVED","validation_reason":"No positive controllable SHAP driver requires an adjustment.","constraint_triggered":None,"validated_recommendation":action["recommendation"],"modified":False,"approved_step_size":"0%","operator_message":action["operator_message"],"ready_for_execution":True}
        if control not in self.config["controllable_variables"]: return {**base,"validation_state":"REJECTED","validation_reason":"Recommendation does not map to a controllable actuator.","constraint_triggered":"Controllability","validated_recommendation":None,"modified":False,"approved_step_size":"0%","operator_message":"Do not execute; the identified driver is not an actuator.","ready_for_execution":False}
        target=RECIPES[grade][control]; lo,hi=RANGES[control]; requested=min(self.config["step_percent"]["maximum"],max(self.config["step_percent"]["minimum"],abs(action["supporting_shap_values"][0])*2))
        cap=self.config["step_percent"].get(f"{phase}_maximum",self.config["step_percent"]["maximum"]); approved=min(requested,cap)
        direction=action["recommended_direction"]; proposed=target*(1+approved/100 if direction=="Increase" else 1-approved/100)
        if not lo <= proposed <= hi: return {**base,"validation_state":"REJECTED","validation_reason":"The target-bound actuator change would exceed its operating limit.","constraint_triggered":f"{control} operating limit","validated_recommendation":None,"modified":False,"approved_step_size":"0%","operator_message":"Do not execute; the proposed action exceeds the approved operating envelope.","ready_for_execution":False}
        modified=approved < requested; state="MODIFIED" if modified else "APPROVED"; reason=(f"Step limited to {approved:.1f}% for {phase} phase." if modified else "Grade target, actuator limit, direction, and phase constraints passed.")
        text=f"{direction} {control} by {approved:.1f}% toward the {grade} target."
        return {**base,"validation_state":state,"validation_reason":reason,"constraint_triggered":"Phase step-size limit" if modified else None,"validated_recommendation":text,"modified":modified,"approved_step_size":f"{approved:.1f}%","operator_message":f"{text} {action['operator_message']}","ready_for_execution":True}

    def _validate_legacy_action(self, action: dict, current_state: dict | None,
                                prediction: dict | None) -> dict:
        if not isinstance(action, dict):
            raise ValueError("Legacy validation requires a structured action object.")
        required = {"parameter", "operation", "change_percent"}
        if not required.issubset(action):
            raise ValueError("Action must include parameter, operation, and change_percent.")
        if not isinstance(current_state, dict) or not isinstance(prediction, dict):
            raise ValueError("Current state and prediction are required for legacy validation.")
        scenario = prediction.get("scenario")
        if scenario not in self._legacy_historical_ranges:
            raise ValueError(f"Unknown scenario: {scenario}")
        parameter, operation = action["parameter"], action["operation"]
        if parameter not in self._legacy_machine_limits or parameter not in current_state:
            raise ValueError(f"Unsupported or unavailable parameter: {parameter}")
        if operation not in {"increase", "decrease", "maintain"}:
            raise ValueError(f"Unsupported operation: {operation}")
        try:
            percent = float(action["change_percent"])
            value = float(current_state[parameter])
        except (TypeError, ValueError) as exc:
            raise ValueError("Action percentage and process value must be numeric.") from exc
        if percent < 0:
            raise ValueError("Action percentage cannot be negative.")
        sign = 1 if operation == "increase" else -1 if operation == "decrease" else 0
        proposed = value * (1 + sign * percent / 100)
        grade = current_state.get("grade")
        recipe = self._legacy_recipe_constraints.get(grade)
        if recipe is None:
            raise ValueError(f"Unknown grade: {grade}")
        checks = {
            "recipe": self._in_range(proposed, recipe[parameter]),
            "machine": self._in_range(proposed, self._legacy_machine_limits[parameter]),
            "historical": self._in_range(proposed, self._legacy_historical_ranges[scenario][parameter]),
        }
        failed = [layer for layer in ("recipe", "machine") if not checks[layer]]
        warning = not checks["historical"]
        return {
            "validation_status": "fail" if failed else "pass",
            "severity": "error" if failed else "warning" if warning else "none",
            "passed_layers": [layer for layer in ("recipe", "machine", "historical") if checks[layer]],
            "failed_layers": failed,
            "warnings": ["Historical safe range exceeded."] if warning else [],
            "proposed_value": proposed,
            "parameter": parameter,
            "operation": operation,
            "change_percent": percent,
        }

    @staticmethod
    def _in_range(value: float, bounds: tuple[float, float]) -> bool:
        return bounds[0] <= value <= bounds[1]

    def validate_parameter(self, parameter: str, value: float, grade: str, scenario: str) -> dict:
        if parameter not in self._legacy_machine_limits:
            raise ValueError(f"Unsupported parameter: {parameter}")
        if grade not in self._legacy_recipe_constraints or scenario not in self._legacy_historical_ranges:
            raise ValueError("Unknown grade or scenario.")
        return {
            "recipe": {"passed": self._in_range(value, self._legacy_recipe_constraints[grade][parameter])},
            "machine": {"passed": self._in_range(value, self._legacy_machine_limits[parameter])},
            "historical": {"passed": self._in_range(value, self._legacy_historical_ranges[scenario][parameter])},
        }

    def get_recipe_constraints(self, grade: str) -> dict:
        if grade not in self._legacy_recipe_constraints:
            raise ValueError(f"Unknown grade: {grade}")
        return self._legacy_recipe_constraints[grade].copy()

    def get_machine_limits(self) -> dict:
        return self._legacy_machine_limits.copy()

    def get_historical_safe_ranges(self, scenario: str) -> dict:
        if scenario not in self._legacy_historical_ranges:
            raise ValueError(f"Unknown scenario: {scenario}")
        return self._legacy_historical_ranges[scenario].copy()

    def get_engine_info(self) -> dict:
        return {"constraint_layers": 3, "task8_configurable": True}
