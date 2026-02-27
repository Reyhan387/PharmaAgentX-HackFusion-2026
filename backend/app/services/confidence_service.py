# backend/app/services/confidence_service.py
# STEP 46 — Deterministic Confidence Scoring Layer (explainability only)

from sqlalchemy.orm import Session
from backend.app.models.audit_log import AuditLog


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

        # A) Risk penalty: each risk point reduces confidence by 0.5
        risk_penalty = risk_score * 0.5

        # B) Drift penalty: each drift flag reduces confidence by 15 points
        drift_penalty = len(drift_flags) * 15

        # C) Governance mode penalty
        if governance_mode == "REVIEW":
            governance_penalty = 10
        elif governance_mode == "SAFE":
            governance_penalty = 20
        else:
            # AUTO
            governance_penalty = 0

        # D) Multiplier stability penalty: unstable multiplier above 1.5 reduces confidence
        multiplier_penalty = 10 if adaptive_multiplier > 1.5 else 0

        # Final deterministic confidence score, clamped between 0 and 100
        confidence = BASE_CONFIDENCE
        confidence -= risk_penalty
        confidence -= drift_penalty
        confidence -= governance_penalty
        confidence -= multiplier_penalty
        confidence = max(0, min(100, confidence))

        # Immutable audit log entry — append-only, no reads
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
