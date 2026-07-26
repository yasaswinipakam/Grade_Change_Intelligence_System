"""Recommendation generation and in-memory trace storage."""

from datetime import datetime, timezone
import logging
from typing import Dict, MutableMapping
from uuid import uuid4

from models import RecommendRequest, RecommendResponse


class RecommendationService:
    """Map a risk score to a deterministic recommendation and save its trace."""

    def __init__(self, recommendation_store: MutableMapping[str, Dict[str, object]] | None = None) -> None:
        self.recommendation_store = recommendation_store if recommendation_store is not None else {}
        self.logger = logging.getLogger(__name__)

    def recommend(self, request: RecommendRequest) -> RecommendResponse:
        """Create a UUID4 recommendation and keep it available for feedback."""
        recommendation_id = str(uuid4())
        if request.risk_score >= 75:
            details = ("Increase Steam: 3% + Reduce Speed: 1%", 76, 5, 60, 15, 15, [
                {"parameter": "steam_pressure", "operation": "increase", "change_percent": 3},
                {"parameter": "machine_speed", "operation": "decrease", "change_percent": 1},
            ])
        elif request.risk_score >= 40:
            details = ("Reduce Stock Flow: 2%", 91, 18, 89, 8, 12, [
                {"parameter": "stock_flow", "operation": "decrease", "change_percent": 2},
            ])
        else:
            details = ("Maintain current parameters", 97, 42, 98, 2, 2, [
                {"parameter": "stock_flow", "operation": "maintain", "change_percent": 0},
            ])
        action, confidence, similar_cases, success_rate, stabilization, lead_time, structured_actions = details
        self.recommendation_store[recommendation_id] = {
            "action": action,
            "risk_score": request.risk_score,
            "predicted_deviation": request.predicted_deviation,
            "lead_time_minutes": lead_time,
            "structured_actions": structured_actions,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.logger.info("Created recommendation %s", recommendation_id)
        return RecommendResponse(
            recommendation_id=recommendation_id, action=action, confidence=confidence,
            similar_cases=similar_cases, success_rate=success_rate,
            avg_stabilization_minutes=stabilization, structured_actions=structured_actions,
        )
