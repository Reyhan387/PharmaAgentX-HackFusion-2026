from typing import Dict
from sqlalchemy.orm import Session
from datetime import datetime

from .explainability_service import get_medicine_risk_snapshot
from .self_healing_service import calculate_instability_multiplier


class MitigationRecommendationService:
    """
    STEP 39 + STEP 41
    Autonomous Mitigation Recommendation Engine
    + Self-Healing Adaptive Intelligence Layer

    Deterministic. No schema changes.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_mitigation_recommendation(self, medicine_id: int) -> Dict:
        """
        Uses Step 38 Smart-Adaptive Risk Snapshot
        Enhanced by Step 41 Self-Healing Instability Multiplier
        """

        risk_data = get_medicine_risk_snapshot(self.db, medicine_id)

        # Safe handling
        if not risk_data or "error" in risk_data:
            return risk_data

        risk_level = risk_data.get("risk_level", "LOW")
        coverage_ratio = risk_data.get("coverage_ratio")
        acceleration_factor = risk_data.get("acceleration_factor", 0)
        recent_escalation_count = risk_data.get("recent_escalation_count", 0)

        recommendation = "MONITOR"
        reason = "System stable"

        # ----------------------------------------
        # STEP 39 — Base Deterministic Logic
        # ----------------------------------------

        if risk_level == "HIGH":

            if coverage_ratio is not None and coverage_ratio < 0.5:
                recommendation = "RESTOCK_IMMEDIATE"
                reason = "Coverage ratio critically low"

            elif acceleration_factor > 0.3 and recent_escalation_count > 0:
                recommendation = "SUPPLIER_ESCALATION"
                reason = "Demand accelerating with repeated escalations"

            else:
                recommendation = "RESTOCK_IMMEDIATE"
                reason = "High risk score"

        elif risk_level == "MEDIUM":

            if coverage_ratio is not None and coverage_ratio < 0.75:
                recommendation = "SAFETY_STOCK_INCREASE"
                reason = "Buffer insufficient for projected demand"

            elif acceleration_factor > 0.3:
                recommendation = "SUPPLIER_ESCALATION"
                reason = "Demand trend increasing"

            else:
                recommendation = "MONITOR"
                reason = "Moderate risk but stable"

        else:
            recommendation = "MONITOR"
            reason = "No mitigation required"

        # =====================================================
        # STEP 41 — Self-Healing Adaptive Intelligence
        # =====================================================

        adaptive_data = calculate_instability_multiplier(
            self.db, medicine_id
        )

        multiplier = adaptive_data.get("multiplier", 1.0)
        instability_score = adaptive_data.get("instability_score", 0)

        # Escalate mitigation aggressiveness if chronic instability
        if multiplier >= 1.3:

            if recommendation == "MONITOR":
                recommendation = "SAFETY_STOCK_INCREASE"
                reason = "Chronic instability detected — proactive buffer increase"

            elif recommendation == "SAFETY_STOCK_INCREASE":
                recommendation = "RESTOCK_IMMEDIATE"
                reason = "Repeated stock instability — aggressive restock triggered"

            elif recommendation == "SUPPLIER_ESCALATION":
                recommendation = "RESTOCK_IMMEDIATE"
                reason = "Escalation history + instability — forcing immediate restock"

        # =====================================================
        # RESPONSE
        # =====================================================

        return {
            "medicine_id": risk_data.get("medicine_id"),
            "medicine_name": risk_data.get("medicine_name"),
            "risk_level": risk_level,
            "risk_score": risk_data.get("risk_score"),
            "coverage_ratio": coverage_ratio,
            "recommendation": recommendation,
            "reason": reason,
            "instability_score": instability_score,
            "adaptive_multiplier": multiplier,
            "generated_at": risk_data.get(
                "generated_at",
                datetime.utcnow().isoformat()
            ),
        }