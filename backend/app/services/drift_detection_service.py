# backend/app/services/drift_detection_service.py
# STEP 45 — Deterministic Drift Detection Engine

from sqlalchemy.orm import Session
from datetime import datetime
from backend.app.models.audit_log import AuditLog
from backend.app.services.system_governor_service import get_current_mode


DRIFT_LOOKBACK_LIMIT = 10
DRIFT_RISK_ESCALATION_COUNT = 3
DRIFT_REVIEW_SPIKE_THRESHOLD = 5
DRIFT_MULTIPLIER_VARIANCE_THRESHOLD = 0.30


class DriftDetectionService:

    @staticmethod
    def evaluate(
        db: Session,
        current_risk: float,
        current_multiplier: float
    ) -> list:

        recent_logs = (
            db.query(AuditLog)
            .order_by(AuditLog.created_at.desc())
            .limit(DRIFT_LOOKBACK_LIMIT)
            .all()
        )

        drift_flags = []

        # RULE A — RISK ESCALATION DRIFT
        risk_values = []
        for log in recent_logs:
            if log.risk_score is not None:
                risk_values.append(log.risk_score)
            if len(risk_values) == DRIFT_RISK_ESCALATION_COUNT:
                break

        if len(risk_values) == DRIFT_RISK_ESCALATION_COUNT:
            r1, r2, r3 = risk_values[::-1]
            if r1 < r2 < r3:
                drift_flags.append("RISK_ESCALATION")

        # RULE B — REVIEW SPIKE DRIFT
        review_count = sum(
            1 for log in recent_logs if log.mode_at_time == "REVIEW"
        )
        if review_count >= DRIFT_REVIEW_SPIKE_THRESHOLD:
            drift_flags.append("REVIEW_SPIKE")

        # RULE C — MULTIPLIER ANOMALY DRIFT
        multiplier_values = []
        for log in recent_logs:
            if log.event_type == "MULTIPLIER_UPDATE" and log.reference_id is not None:
                try:
                    multiplier_values.append(float(log.reference_id))
                except (ValueError, TypeError):
                    pass

        if multiplier_values:
            mean = sum(multiplier_values) / len(multiplier_values)
            if mean != 0 and abs(current_multiplier - mean) / mean > DRIFT_MULTIPLIER_VARIANCE_THRESHOLD:
                drift_flags.append("MULTIPLIER_ANOMALY")

        # IMMUTABLE DRIFT LOGGING
        if drift_flags:
            current_mode = get_current_mode(db)
            for flag in drift_flags:
                log_entry = AuditLog(
                    event_type="DRIFT_ALERT",
                    actor="system",
                    risk_score=int(current_risk),
                    mode_at_time=current_mode,
                    decision=flag,
                    reference_id=None,
                    reference_table=None,
                )
                db.add(log_entry)
            db.commit()

        return drift_flags
