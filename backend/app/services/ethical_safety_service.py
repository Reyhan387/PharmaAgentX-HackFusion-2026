# backend/app/services/ethical_safety_service.py
# STEP 47 — Ethical Safety Enforcement Layer
# Deterministic, rule-based healthcare safeguard.
# Escalates governance mode when system reliability decreases.
# Core philosophy: "Autonomy is reduced when system reliability decreases."

from sqlalchemy.orm import Session
from datetime import datetime

from backend.app.models.audit_log import AuditLog
from backend.app.models.system_config import SystemConfig


# =====================================================
# HARDCODED DETERMINISTIC THRESHOLDS — NOT CONFIGURABLE
# =====================================================

ETHICAL_CONFIDENCE_CRITICAL = 40   # Below this → force SAFE mode (nuclear option)
ETHICAL_CONFIDENCE_WARNING = 60    # Below this (but >= CRITICAL) → may escalate to REVIEW
ETHICAL_DRIFT_CRITICAL_COUNT = 2   # >= 2 drift flags → escalate governance
SYSTEM_CONFIG_ID = 1               # Primary system configuration record ID


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
        Evaluate deterministic ethical safety rules and escalate governance mode
        if system reliability has decreased.

        Returns the final governance mode after ethical evaluation:
        "SAFE", "REVIEW", or "AUTO".
        """

        new_mode = current_mode  # Default: no change

        # -----------------------------------------------
        # Rule A — Critical Confidence Override (HIGHEST PRIORITY)
        # When confidence drops below 40, the system is too unreliable
        # to operate autonomously. Force SAFE mode unconditionally.
        # -----------------------------------------------
        if confidence_score < ETHICAL_CONFIDENCE_CRITICAL:
            new_mode = "SAFE"

        # -----------------------------------------------
        # Rule B — Drift Escalation
        # When 2 or more drift flags are raised, escalate upward.
        # AUTO → REVIEW, REVIEW → SAFE, SAFE → SAFE (remain).
        # Only evaluated if Rule A did not already trigger.
        # -----------------------------------------------
        elif len(drift_flags) >= ETHICAL_DRIFT_CRITICAL_COUNT:
            if current_mode == "AUTO":
                new_mode = "REVIEW"
            elif current_mode == "REVIEW":
                new_mode = "SAFE"
            else:  # already SAFE
                new_mode = "SAFE"

        # -----------------------------------------------
        # Rule C — Warning Level
        # Confidence between 40 and 60 is a cautionary zone.
        # If AUTO, escalate to REVIEW for human oversight.
        # -----------------------------------------------
        elif ETHICAL_CONFIDENCE_CRITICAL <= confidence_score < ETHICAL_CONFIDENCE_WARNING:
            if current_mode == "AUTO":
                new_mode = "REVIEW"

        # -----------------------------------------------
        # Rule D — Otherwise: no intervention needed
        # -----------------------------------------------
        # new_mode remains equal to current_mode — no change.

        # -----------------------------------------------
        # Governance Escalation — apply mode change if needed
        # -----------------------------------------------
        if new_mode != current_mode:
            # Update SystemConfig (id=1) with the new mode.
            # system_governor_service uses the same SystemConfig model.
            config = db.query(SystemConfig).filter(SystemConfig.id == SYSTEM_CONFIG_ID).first()
            if config:
                config.current_mode = new_mode
                config.updated_at = datetime.utcnow()
            else:
                config = SystemConfig(
                    id=SYSTEM_CONFIG_ID,
                    current_mode=new_mode,
                    updated_at=datetime.utcnow()
                )
                db.add(config)

            # Ethical audit log — immutable, append-only
            log = AuditLog(
                event_type="ETHICAL_OVERRIDE",
                actor="system",
                risk_score=None,
                mode_at_time=current_mode,  # mode BEFORE the change
                decision=f"{current_mode} → {new_mode}",
                reference_id=None,
                reference_table=None,
            )
            db.add(log)

            # Single commit — batches SystemConfig update and audit insert
            db.commit()

        return new_mode
