"""Deterministic mock prediction service."""

import logging

from models import PredictRequest, PredictResponse
from prediction_engine import PredictionEngine
from processors.prediction_feature_processor import PredictionFeatureProcessor


class PredictionService:
    """Engineer features and return deterministic scenario-aligned predictions."""

    def __init__(self, processor: PredictionFeatureProcessor, engine: PredictionEngine) -> None:
        self.processor = processor
        self.engine = engine
        self.logger = logging.getLogger(__name__)

    def predict(self, request: PredictRequest) -> PredictResponse:
        """Process a reading and select its mock scenario by basis weight."""
        features = self.processor.process(request.model_dump())
        response = PredictResponse(**self.engine.predict(features.values()))
        self.logger.info("Prediction calculated for basis_weight=%s", request.basis_weight)
        return response
