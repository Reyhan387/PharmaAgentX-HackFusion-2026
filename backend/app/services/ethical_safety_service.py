# backend/app/services/ethical_safety_service.py
# STEP 47 — Ethical Safety Enforcement Layer
# Deterministic rule-based healthcare safeguard.
# Reduces system autonomy when reliability decreases.
# Escalates governance mode based on confidence score and drift flags.

from sqlalchemy.orm import Session
from datetime import datetime

from backend.app.models.audit_log import AuditLog
from backend.app.models.system_config import SystemConfig


# =====================================================
# HARDCODED DETERMINISTIC THRESHOLDS — NOT CONFIGURABLE
# =====================================================

ETHICAL_CONFIDENCE_CRITICAL = 40
ETHICAL_CONFIDENCE_WARNING = 60
ETHICAL_DRIFT_CRITICAL_COUNT = 2


# =====================================================
# PRIVATE HELPERS
# =====================================================

def _escalate_governance_mode(db: Session, new_mode: str):
    """
    Updates the system_config table (row id=1) to the new governance mode.
    System-initiated — updated_by is set to None.
    """
    config = db.query(SystemConfig).filter(SystemConfig.id == 1).first()

    if not config:
        config = SystemConfig(
            id=1,
            current_mode=new_mode,
            updated_by=None,
            updated_at=datetime.utcnow()
        )
        db.add(config)
    else:
        config.current_mode = new_mode
        config.updated_by = None
        config.updated_at = datetime.utcnow()

    db.commit()


def _log_ethical_override(db: Session, previous_mode: str, new_mode: str):
    """
    Appends an immutable audit log entry recording the ethical mode override.
    Append-only — single commit.
    """
    log = AuditLog(
        event_type="ETHICAL_OVERRIDE",
        actor="system",
        risk_score=None,
        mode_at_time=previous_mode,
        decision=f"{previous_mode} -> {new_mode}",
        reference_id=None,
        reference_table=None,
    )
    db.add(log)
    db.commit()


# =====================================================
# ETHICAL SAFETY SERVICE
# =====================================================

class EthicalSafetyService:

    @staticmethod
    def evaluate(
        db: Session,
        confidence_score: float,
        drift_flags: list,
        current_mode: str
    ) -> str:
        """
        Evaluates ethical safety rules in priority order and returns the
        final governance mode. If the mode is escalated, updates system_config
        and writes an immutable audit log entry.

        Returns: "SAFE", "REVIEW", or "AUTO"
        """

        # -----------------------------------------------
        # RULE A — Critical Confidence Override (highest priority)
        # If confidence is critically low, force SAFE mode immediately,
        # regardless of current mode.
        # -----------------------------------------------
        if confidence_score < ETHICAL_CONFIDENCE_CRITICAL:
            new_mode = "SAFE"

        # -----------------------------------------------
        # RULE B — Drift Escalation
        # If too many drift flags are active, escalate one level:
        #   AUTO  → REVIEW
        #   REVIEW → SAFE
        #   SAFE  → SAFE (cannot escalate further)
        # -----------------------------------------------
        elif len(drift_flags) >= ETHICAL_DRIFT_CRITICAL_COUNT:
            if current_mode == "AUTO":
                new_mode = "REVIEW"
            elif current_mode == "REVIEW":
                new_mode = "SAFE"
            else:
                # SAFE stays SAFE
                new_mode = "SAFE"

        # -----------------------------------------------
        # RULE C — Warning Level Confidence
        # Moderate confidence drop while in AUTO mode escalates to REVIEW.
        # -----------------------------------------------
        elif ETHICAL_CONFIDENCE_CRITICAL <= confidence_score < ETHICAL_CONFIDENCE_WARNING and current_mode == "AUTO":
            new_mode = "REVIEW"

        # -----------------------------------------------
        # RULE D — No ethical concern detected
        # Return original mode unchanged.
        # -----------------------------------------------
        else:
            new_mode = current_mode

        # -----------------------------------------------
        # GOVERNANCE ESCALATION — only if mode actually changed
        # -----------------------------------------------
        if new_mode != current_mode:
            _escalate_governance_mode(db=db, new_mode=new_mode)
            _log_ethical_override(db=db, previous_mode=current_mode, new_mode=new_mode)

        return new_mode
