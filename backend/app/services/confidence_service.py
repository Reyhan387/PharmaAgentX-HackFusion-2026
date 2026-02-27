# backend/app/services/confidence_service.py
# STEP 46 — Deterministic Confidence Scoring Engine

from sqlalchemy.orm import Session
from datetime import datetime
from backend.app.models.audit_log import AuditLog


# Hardcoded deterministic base confidence value
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

        # A) Risk Penalty — higher risk reduces confidence
        risk_penalty = risk_score * 0.5

        # B) Drift Penalty — each drift flag reduces confidence by 15 points
        drift_penalty = len(drift_flags) * 15

        # C) Governance Mode Penalty — conservative modes signal lower confidence
        if governance_mode == "SAFE":
            governance_penalty = 20
        elif governance_mode == "REVIEW":
            governance_penalty = 10
        else:  # AUTO
            governance_penalty = 0

        # D) Multiplier Stability Penalty — high multiplier signals instability
        if adaptive_multiplier > 1.5:
            multiplier_penalty = 10
        else:
            multiplier_penalty = 0

        # Final deterministic formula
        confidence = BASE_CONFIDENCE
        confidence -= risk_penalty
        confidence -= drift_penalty
        confidence -= governance_penalty
        confidence -= multiplier_penalty

        # Clamp between 0 and 100
        confidence = max(0.0, min(100.0, confidence))

        # Immutable audit log — append-only, never overwrite
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
