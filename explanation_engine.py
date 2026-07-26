"""Backward-compatibility shim for shap_explainer.pkl.

The pkl was serialised with 'explanation_engine.SHAPExplanationEngine'.
This module provides a class with the original interface so the pkl can
unpickle correctly and services.py can call explain(scaled, prediction, probability).
"""
from __future__ import annotations
import numpy as np


class SHAPExplanationEngine:
    """Wraps real SHAP TreeExplainers to produce UI-ready local explanations."""

    def __init__(self, regressor=None, classifier=None, feature_names=None):
        self.regressor = regressor
        self.classifier = classifier
        self.feature_names = feature_names or []
        self.regression_explainer = None
        self.classification_explainer = None

    def explain(self, scaled: np.ndarray, prediction: float, probability: float) -> dict:
        """Compute SHAP values and return the explanation dict expected by recommendation_engine."""
        feature_names = self.feature_names

        # Compute regression SHAP values
        reg_shap = np.zeros(len(feature_names))
        cls_shap = np.zeros(len(feature_names))

        if self.regression_explainer is not None:
            try:
                rv = self.regression_explainer.shap_values(
                    np.array(scaled).reshape(1, -1)
                )
                reg_shap = np.array(rv).flatten()
            except Exception:
                pass

        if self.classification_explainer is not None:
            try:
                cv = self.classification_explainer.shap_values(
                    np.array(scaled).flatten().reshape(1, -1)
                )
                arr = np.array(cv)
                # TreeExplainer can return (n_samples, n_features) or (n_classes, n_samples, n_features)
                if arr.ndim == 3:
                    cls_shap = arr[1, 0]   # positive class
                else:
                    cls_shap = arr.flatten()
            except Exception:
                pass

        # Build ranked contributors sorted by |regression shap|
        scaled_arr = np.array(scaled).flatten()
        combined = sorted(
            zip(feature_names, reg_shap.tolist(), cls_shap.tolist(), scaled_arr.tolist()),
            key=lambda x: abs(x[1]),
            reverse=True,
        )

        top_contributors = []
        for feat, rsv, csv, val in combined[:15]:
            plain = feat.removeprefix("z_").replace("_", " ")
            direction = "above" if rsv > 0 else "below"
            top_contributors.append({
                "feature": feat,
                "shap_value": rsv,
                "cls_shap_value": csv,
                "value": val,
                "operator_message": (
                    f"{plain.title()} is {direction} its grade target "
                    f"(SHAP contribution: {rsv:+.3f})."
                ),
            })

        # Overall risk score (0-100) derived from off-spec probability
        risk_score = round(probability * 100, 1)

        return {
            "prediction": {
                "basis_weight_deviation": prediction,
                "off_spec_probability": probability,
            },
            "risk_score": risk_score,
            "top_contributors": top_contributors,
            "shap_values": reg_shap.tolist(),
            "feature_names": feature_names,
        }

