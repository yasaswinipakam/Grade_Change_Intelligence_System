"""Deterministic SHAP-style explanation service for the demo API."""

import logging
from typing import Dict, MutableMapping

from models import ExplainRequest, ExplainResponse, FeatureImportance
from prediction_engine import PredictionEngine
from shap_explanation_engine import SHAPExplanationEngine


class ExplanationService:
    """Return deterministic, sorted feature importance for each risk band."""

    def __init__(
        self,
        recommendation_store: MutableMapping[str, Dict[str, object]],
        engine: PredictionEngine,
    ) -> None:
        self.recommendation_store = recommendation_store
        self.engine = engine
        self.shap_engine = SHAPExplanationEngine()
        self.logger = logging.getLogger(__name__)

    def explain(self, request: ExplainRequest) -> ExplainResponse:
        """Produce an explainable feature ranking using a linked recommendation."""
        prediction = self._resolve_prediction(request)
        if "feature_importance" not in prediction:
            prediction["feature_importance"] = self.engine.get_feature_importance_for_risk(float(prediction["risk_score"]))
            prediction["scenario"] = "B" if float(prediction["risk_score"]) >= 75 else "A" if float(prediction["risk_score"]) >= 40 else "C"
        explanation = self.shap_engine.explain(prediction)
        features = [FeatureImportance(**feature) for feature in explanation["features"]]
        return ExplainResponse(
            recommendation_id=request.recommendation_id,
            features=features,
            top_3_drivers=explanation["top_3_drivers"],
            decision_trace=explanation["decision_trace"],
        )

    def _resolve_prediction(self, request: ExplainRequest) -> Dict[str, object]:
        if request.recommendation_id is not None:
            record = self.recommendation_store.get(str(request.recommendation_id))
            if record is None:
                raise KeyError(f"Recommendation {request.recommendation_id} not found")
            return {
                "risk_score": record["risk_score"],
                "predicted_deviation": record["predicted_deviation"],
                "lead_time_minutes": record["lead_time_minutes"],
            }
        return self.engine.predict(request.feature_vector)
