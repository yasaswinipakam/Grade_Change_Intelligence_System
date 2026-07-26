"""Traceable SHAP-to-action recommendation engine for decision support."""
from __future__ import annotations
from dataclasses import dataclass
from uuid import uuid4

CONTROLLABLE = {
    "Q_feed": ("Feed flow", "toward the active grade target"), "P_heat": ("Primary heating pressure", "toward the active grade target"),
    "P_aux": ("Auxiliary heating pressure", "toward the active grade target"), "V_line": ("Line speed", "toward the active grade target"),
    "Q_add": ("Added moisture flow", "toward the active grade target"), "E_extract": ("Extraction intensity", "toward the active grade target"),
    "C_feed": ("Feed concentration", "toward the active grade target"), "R_aid": ("Retention aid", "toward the active grade target"), "F_inert": ("Inert-additive flow", "toward the active grade target"),
}

def _control_for(feature: str):
    plain=feature.removeprefix("z_")
    return next((key for key in CONTROLLABLE if plain.startswith(key)), None)

class RecommendationEngine:
    """Convert signed local SHAP contributors into ranked operator actions."""
    def recommend(self, explanation: dict) -> dict:
        phase=explanation["process_phase"]; prediction=explanation["prediction"]; actions=[]
        for item in explanation["top_contributors"]:
            control=_control_for(item["feature"])
            # A contributor is actionable only when it increases the absolute predicted deviation.
            if not control or item["shap_value"] * prediction["basis_weight_deviation"] <= 0: continue
            # Positive SHAP increases deviation: move the contributor opposite its signed residual.
            residual=item["value"]; direction="Decrease" if residual > 0 else "Increase"
            gradual="gradually " if phase in {"ramp","transient","stabilization","recovery"} else ""
            impact=abs(item["shap_value"]); confidence="High" if impact>=.5 else "Medium" if impact>=.15 else "Low"
            priority="Critical" if prediction["off_spec_probability"]>=.8 and impact>=.5 else "High" if impact>=.5 else "Medium" if impact>=.15 else "Low"
            label,target=CONTROLLABLE[control]
            actions.append({"control":control,"priority":priority,"recommendation":f"{gradual}{direction.lower()} {label} {target}.","recommended_direction":direction,"supporting_features":[item["feature"]],"supporting_shap_values":[item["shap_value"]],"current_feature_values":[item["value"]],"expected_effect":{"basis_weight_deviation":f"Estimated reduction of {impact:.2f} deviation points", "off_spec_probability":f"Estimated local risk reduction of {min(impact*10,25):.1f} percentage points"},"confidence":confidence,"operator_message":f"{label} is a leading driver in this {phase} phase. {gradual.capitalize()}{direction} it toward the {explanation['grade']} target and confirm the next process scan.","explanation":item["operator_message"]})
        # De-duplicate controls and preserve SHAP impact ordering; no conflicting directions survive.
        unique=[]; seen=set()
        for action in actions:
            if action["control"] not in seen: unique.append(action); seen.add(action["control"])
        selected=unique[:3]
        if not selected:
            selected=[{"control":"maintain","priority":"Low","recommendation":"Maintain current controllable settings and continue monitoring.","recommended_direction":"Maintain","supporting_features":[],"supporting_shap_values":[],"current_feature_values":[],"expected_effect":{"basis_weight_deviation":"No corrective action indicated by positive controllable SHAP drivers", "off_spec_probability":"Continue monitoring"},"confidence":"Medium","operator_message":"No positive controllable driver is dominant; maintain the grade recipe and monitor the next scan.","explanation":"Leading contributors are mitigating risk or are non-controllable context features."}]
        return {"prediction_id":str(uuid4()),"grade":explanation["grade"],"process_phase":phase,"basis_weight_prediction":prediction["basis_weight_deviation"],"off_spec_probability":prediction["off_spec_probability"],"priority":selected[0]["priority"],"primary_recommendation":selected[0],"alternative_recommendation":selected[1] if len(selected)>1 else None,"fallback_recommendation":selected[2] if len(selected)>2 else None,"recommendations":selected,"traceability":{"prediction_model":"xgboost_regressor.pkl + xgboost_classifier.pkl","shap_features":[x["supporting_features"][0] if x["supporting_features"] else None for x in selected],"shap_values":[x["supporting_shap_values"][0] if x["supporting_shap_values"] else None for x in selected],"feature_values":[x["current_feature_values"][0] if x["current_feature_values"] else None for x in selected],"source_timestamp":explanation["timestamp"]}}
