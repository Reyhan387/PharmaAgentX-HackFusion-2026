# backend/app/services/confidence_service.py
# STEP 46 — Deterministic Confidence Scoring Engine

from sqlalchemy.orm import Session
from datetime import datetime
from backend.app.models.audit_log import AuditLog


# Hardcoded deterministic base — never changes
BASE_CONFIDENCE = 100


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
        Computes a deterministic confidence score (0–100) based on:
        - Risk score magnitude
        - Number of active drift flags
        - Current governance mode
        - Adaptive multiplier stability

        Purely observational — does NOT alter execution behavior.
        """

        # A) RISK PENALTY: higher risk reduces confidence
        # Each point of risk contributes 0.5 penalty points
        risk_penalty = risk_score * 0.5

        # B) DRIFT PENALTY: each drift flag reduces confidence by 15 points
        drift_penalty = len(drift_flags) * 15

        # C) GOVERNANCE MODE PENALTY:
        # SAFE mode signals maximum constraint — highest penalty
        # REVIEW mode signals elevated caution — moderate penalty
        # AUTO mode is nominal — no penalty
        if governance_mode == "SAFE":
            governance_penalty = 20
        elif governance_mode == "REVIEW":
            governance_penalty = 10
        else:  # AUTO
            governance_penalty = 0

        # D) MULTIPLIER STABILITY PENALTY:
        # Multiplier above 1.5 indicates instability — apply penalty
        if adaptive_multiplier > 1.5:
            multiplier_penalty = 10
        else:
            multiplier_penalty = 0

        # FINAL FORMULA — subtract all penalties from base, then clamp to [0, 100]
        confidence = BASE_CONFIDENCE
        confidence -= risk_penalty
        confidence -= drift_penalty
        confidence -= governance_penalty
        confidence -= multiplier_penalty
        confidence = max(0.0, min(100.0, confidence))

        # IMMUTABLE AUDIT LOGGING — append-only, never overwritten
        log_entry = AuditLog(
            event_type="CONFIDENCE_SCORE",
            actor="system",
            risk_score=int(risk_score),
            mode_at_time=governance_mode,
            decision=str(confidence),
            reference_id=None,
            reference_table=None,
        )
        db.add(log_entry)
        db.commit()

        return confidence
