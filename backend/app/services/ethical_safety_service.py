# backend/app/services/ethical_safety_service.py
# STEP 47 — Ethical Safety Enforcement Layer
# Rule-based healthcare safeguard — NOT AI magic.
# Reduces autonomy when system reliability decreases.
# Deterministic governance escalation only.

from sqlalchemy.orm import Session
from datetime import datetime

from backend.app.models.audit_log import AuditLog
from backend.app.models.system_config import SystemConfig


# =====================================================
# HARDCODED DETERMINISTIC THRESHOLDS
# =====================================================

ETHICAL_CONFIDENCE_CRITICAL = 40
ETHICAL_CONFIDENCE_WARNING = 60
ETHICAL_DRIFT_CRITICAL_COUNT = 2


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
        Evaluates ethical safety thresholds and escalates governance
        mode if system reliability has degraded.

        Returns the final governance mode after ethical enforcement.

        Rules (evaluated in priority order):
          A) Critical confidence (<40) -> force SAFE
          B) Multiple drift flags (>=2) -> escalate one level
          C) Warning confidence (40-59) + AUTO -> escalate to REVIEW
          D) Otherwise -> no change

        This is a deterministic, rule-based healthcare safeguard.
        """

        previous_mode = current_mode
        new_mode = current_mode

        # -----------------------------------------------
        # RULE A — CRITICAL CONFIDENCE OVERRIDE
        # Confidence below 40 = system is unreliable.
        # Force SAFE mode regardless of current mode.
        # This is the strongest ethical override.
        # -----------------------------------------------
        if confidence_score < ETHICAL_CONFIDENCE_CRITICAL:
            new_mode = "SAFE"

        # -----------------------------------------------
        # RULE B — DRIFT ESCALATION
        # Two or more drift flags = persistent instability.
        # Escalate one governance level upward.
        # AUTO -> REVIEW, REVIEW -> SAFE, SAFE -> SAFE.
        # Only applies if Rule A did not already force SAFE.
        # -----------------------------------------------
        elif len(drift_flags) >= ETHICAL_DRIFT_CRITICAL_COUNT:
            if current_mode == "AUTO":
                new_mode = "REVIEW"
            elif current_mode == "REVIEW":
                new_mode = "SAFE"
            # SAFE remains SAFE — cannot escalate further

        # -----------------------------------------------
        # RULE C — WARNING LEVEL CONFIDENCE
        # Confidence between 40 and 59 in AUTO mode.
        # Precautionary escalation to REVIEW.
        # -----------------------------------------------
        elif (ETHICAL_CONFIDENCE_CRITICAL <= confidence_score < ETHICAL_CONFIDENCE_WARNING
              and current_mode == "AUTO"):
            new_mode = "REVIEW"

        # -----------------------------------------------
        # RULE D — NO INTERVENTION NEEDED
        # System is stable. Return original mode unchanged.
        # -----------------------------------------------
        # (new_mode remains equal to current_mode)

        # -----------------------------------------------
        # GOVERNANCE ESCALATION — persist mode change
        # Only update system_config if mode actually changed.
        # -----------------------------------------------
        if new_mode != previous_mode:
            _escalate_governance_mode(db, new_mode)
            _log_ethical_override(db, previous_mode, new_mode)

        return new_mode


# =====================================================
# GOVERNANCE MODE PERSISTENCE
# =====================================================

def _escalate_governance_mode(db: Session, new_mode: str):
    """
    Updates system_config.current_mode to the new escalated mode.
    Uses updated_by = None to indicate system-initiated change.
    Single row update, single commit.
    """
    config = db.query(SystemConfig).filter(SystemConfig.id == 1).first()

    if config:
        config.current_mode = new_mode
        config.updated_by = None
        config.updated_at = datetime.utcnow()
    else:
        config = SystemConfig(
            id=1,
            current_mode=new_mode,
            updated_by=None,
            updated_at=datetime.utcnow()
        )
        db.add(config)

    db.commit()


# =====================================================
# IMMUTABLE ETHICAL AUDIT LOG
# =====================================================

def _log_ethical_override(db: Session, previous_mode: str, new_mode: str):
    """
    Logs the ethical override as an immutable audit trail entry.
    Append-only. Single commit.
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
