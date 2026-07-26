"""In-memory operator feedback recording service."""

import logging
from typing import Dict, MutableMapping
from uuid import uuid4

from models import FeedbackRequest, FeedbackResponse


class FeedbackService:
    """Record operator decisions for recommendations created in this process."""

    def __init__(self, recommendation_store: MutableMapping[str, Dict[str, object]] | None = None) -> None:
        self.recommendation_store = recommendation_store if recommendation_store is not None else {}
        self.feedback_log: list[Dict[str, str]] = []
        self.logger = logging.getLogger(__name__)

    def log_feedback(self, request: FeedbackRequest) -> FeedbackResponse:
        """Validate a recommendation ID and append one operator response."""
        recommendation_id = str(request.recommendation_id)
        if recommendation_id not in self.recommendation_store:
            raise KeyError(f"Recommendation {recommendation_id} not found")
        feedback_id = str(uuid4())
        self.feedback_log.append({
            "feedback_id": feedback_id, "recommendation_id": recommendation_id,
            "operator_response": request.operator_response, "timestamp": request.timestamp.isoformat(),
        })
        self.logger.info("Feedback logged: %s", feedback_id)
        return FeedbackResponse(
            status="success", feedback_id=feedback_id, recommendation_id=recommendation_id,
            message=f"Feedback {request.operator_response}ed successfully",
        )
