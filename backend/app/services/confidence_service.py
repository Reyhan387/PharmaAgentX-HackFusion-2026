# backend/app/services/confidence_service.py
# STEP 46 — Deterministic Confidence Scoring Layer
# Explainability layer — does NOT alter execution behavior.

from sqlalchemy.orm import Session
from datetime import datetime

from backend.app.models.audit_log import AuditLog


# =====================================================
# HARDCODED DETERMINISTIC CONSTANT
# =====================================================

BASE_CONFIDENCE = 100


# =====================================================
# CONFIDENCE SCORING SERVICE
# =====================================================

class ConfidenceScoringService:

    @staticmethod
    def calculate(
        db: Session,
        risk_score: float,
        drift_flags: list,
        governance_mode: str,
        adaptive_multiplier: float
    ) -> float:
        """
        Produces a deterministic confidence score from 0 to 100.
        Uses risk, drift flags, governance mode, and multiplier stability.
        Logs the result immutably into audit_logs.
        Purely observational — does NOT change execution behavior.
        """

        confidence = float(BASE_CONFIDENCE)

        # -----------------------------------------------
        # A) RISK PENALTY — higher risk reduces confidence
        # -----------------------------------------------
        risk_penalty = risk_score * 0.5
        confidence -= risk_penalty

        # -----------------------------------------------
        # B) DRIFT PENALTY — each drift flag costs 15 points
        # -----------------------------------------------
        drift_penalty = len(drift_flags) * 15
        confidence -= drift_penalty

        # -----------------------------------------------
        # C) GOVERNANCE MODE PENALTY
        # SAFE = most restrictive = highest penalty
        # REVIEW = moderate penalty
        # AUTO = no penalty
        # -----------------------------------------------
        if governance_mode == "SAFE":
            governance_penalty = 20
        elif governance_mode == "REVIEW":
            governance_penalty = 10
        else:
            governance_penalty = 0
        confidence -= governance_penalty

        # -----------------------------------------------
        # D) MULTIPLIER STABILITY PENALTY
        # High multiplier indicates instability
        # -----------------------------------------------
        if adaptive_multiplier > 1.5:
            multiplier_penalty = 10
        else:
            multiplier_penalty = 0
        confidence -= multiplier_penalty

        # -----------------------------------------------
        # CLAMP — confidence must stay within [0, 100]
        # -----------------------------------------------
        confidence = max(0.0, min(100.0, confidence))

        # -----------------------------------------------
        # IMMUTABLE AUDIT LOG — append-only, single commit
        # -----------------------------------------------
        log = AuditLog(
            event_type="CONFIDENCE_SCORE",
            actor="system",
            risk_score=int(risk_score) if risk_score is not None else None,
            mode_at_time=governance_mode,
            decision=str(confidence),
            reference_id=None,
            reference_table=None,
        )
        db.add(log)
        db.commit()

        return confidence
