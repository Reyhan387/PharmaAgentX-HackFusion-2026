# backend/app/services/observability_service.py
# STEP 48 — Observability Hardening Layer
# Read-only metrics aggregation — does NOT change system behavior.

from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.models.audit_log import AuditLog
from backend.app.models.system_config import SystemConfig


# =====================================================
# OBSERVABILITY SERVICE
# =====================================================

class ObservabilityService:

    @staticmethod
    def system_metrics(db: Session) -> dict:
        """
        Aggregates system health metrics from existing audit_logs
        and system_config. Read-only. Deterministic.
        No new tables. No heavy scans. Performance bounded.
        """

        # -----------------------------------------------
        # A) CURRENT GOVERNANCE MODE
        # -----------------------------------------------
        config = db.query(SystemConfig).filter(SystemConfig.id == 1).first()
        current_mode = config.current_mode if config else "SAFE"

        # -----------------------------------------------
        # B) TOTAL AUDIT EVENTS
        # -----------------------------------------------
        total_audit_events = db.query(AuditLog).count()

        # -----------------------------------------------
        # C) TOTAL ETHICAL OVERRIDES
        # -----------------------------------------------
        total_ethical_overrides = db.query(AuditLog).filter(
            AuditLog.event_type == "ETHICAL_OVERRIDE"
        ).count()

        # -----------------------------------------------
        # D) TOTAL DRIFT ALERTS
        # -----------------------------------------------
        total_drift_alerts = db.query(AuditLog).filter(
            AuditLog.event_type == "DRIFT_ALERT"
        ).count()

        # -----------------------------------------------
        # FETCH RECENT 100 LOGS FOR BOUNDED CALCULATIONS
        # -----------------------------------------------
        recent_logs = (
            db.query(AuditLog)
            .order_by(AuditLog.created_at.desc())
            .limit(100)
            .all()
        )

        # -----------------------------------------------
        # E) AVERAGE RISK SCORE (from recent 100 logs)
        # -----------------------------------------------
        risk_scores = []
        for log in recent_logs:
            if log.risk_score is not None:
                risk_scores.append(log.risk_score)

        if risk_scores:
            average_risk_score = round(sum(risk_scores) / len(risk_scores), 2)
        else:
            average_risk_score = 0.0

        # -----------------------------------------------
        # F) AVERAGE CONFIDENCE SCORE (from recent 100 logs)
        # Parse from decision field where event_type == CONFIDENCE_SCORE
        # -----------------------------------------------
        confidence_values = []
        for log in recent_logs:
            if log.event_type == "CONFIDENCE_SCORE":
                try:
                    val = float(log.decision)
                    confidence_values.append(val)
                except (TypeError, ValueError):
                    continue

        if confidence_values:
            average_confidence_score = round(sum(confidence_values) / len(confidence_values), 2)
        else:
            average_confidence_score = 0.0

        # -----------------------------------------------
        # G) REVIEW MODE FREQUENCY (from recent 100 logs)
        # -----------------------------------------------
        review_mode_frequency = 0
        for log in recent_logs:
            if log.mode_at_time == "REVIEW":
                review_mode_frequency += 1

        # -----------------------------------------------
        # RETURN STRUCTURED METRICS
        # -----------------------------------------------
        return {
            "current_mode": current_mode,
            "total_audit_events": total_audit_events,
            "total_ethical_overrides": total_ethical_overrides,
            "total_drift_alerts": total_drift_alerts,
            "average_risk_score": average_risk_score,
            "average_confidence_score": average_confidence_score,
            "review_mode_frequency": review_mode_frequency
        }
