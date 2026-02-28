# backend/app/services/mitigation_execution_service.py

from sqlalchemy.orm import Session
from datetime import datetime
import json

from ..core.database import SessionLocal
from ..models.fulfillment_log import FulfillmentLog
from ..models.mitigation_review import MitigationReview

from .mitigation_service import MitigationRecommendationService
from .explainability_service import get_medicine_risk_snapshot
from .warehouse_service import trigger_fulfillment
from .self_healing_service import calculate_instability_multiplier
from .system_governor_service import is_execution_allowed

# STEP 44 — Structured Audit
from backend.app.services.audit_service import create_audit_log

SAFE_AUTO_THRESHOLD = 80


# =====================================================
# MAIN ENTRY — EXECUTE IF SAFE
# =====================================================

def execute_mitigation_if_safe(medicine_id: int):

    db: Session = SessionLocal()

    try:
        risk_snapshot = get_medicine_risk_snapshot(db, medicine_id)

        if not risk_snapshot or "error" in risk_snapshot:
            return risk_snapshot

        risk_score = risk_snapshot.get("risk_score", 0)

        allowed, reason = is_execution_allowed(
            db=db,
            risk_score=risk_score,
            safe_threshold=SAFE_AUTO_THRESHOLD
        )

        # ---------------- SAFE MODE ----------------
        if not allowed:

            create_audit_log(
                db=db,
                event_type="SAFE_BLOCKED",
                actor="system",
                mode_at_time="SAFE",
                decision="blocked",
                risk_score=risk_score,
                reference_id=medicine_id,
                reference_table="medicines",
            )

            _log_execution(
                db,
                status="BLOCKED_BY_GOVERNOR",
                message=reason
            )

            return {
                "status": "blocked",
                "reason": reason
            }

        # ---------------- RECOMMENDATION ----------------
        mitigation_service = MitigationRecommendationService(db)
        mitigation = mitigation_service.get_mitigation_recommendation(medicine_id)

        action = mitigation.get("recommendation")

        base_quantity = risk_snapshot.get("recommended_restock_quantity", 0)
        adaptive_data = calculate_instability_multiplier(db, medicine_id)
        multiplier = adaptive_data.get("multiplier", 1.0)
        final_quantity = int(base_quantity * multiplier)

        # -----------------------------------------------
        # STEP 45 — Deterministic Drift Detection (observational only)
        # Inline import required to prevent circular import risk.
        # -----------------------------------------------
        from backend.app.services.drift_detection_service import DriftDetectionService

        drift_flags = DriftDetectionService.evaluate(
            db=db,
            current_risk=risk_score,
            current_multiplier=multiplier
        )

        # -----------------------------------------------
        # STEP 46 — Deterministic Confidence Scoring (observational only)
        # -----------------------------------------------
        from backend.app.services.confidence_service import ConfidenceScoringService

        current_mode = "REVIEW" if reason == "REVIEW_MODE_ACTIVE" else "AUTO"

        confidence_score = ConfidenceScoringService.calculate(
            db=db,
            risk_score=risk_score,
            drift_flags=drift_flags,
            governance_mode=current_mode,
            adaptive_multiplier=multiplier
        )

        # -----------------------------------------------
        # STEP 47 — Ethical Safety Enforcement Layer
        # Escalates governance mode if confidence or drift
        # thresholds are breached. Deterministic rule-based.
        # -----------------------------------------------
        from backend.app.services.ethical_safety_service import EthicalSafetyService

        final_mode = EthicalSafetyService.evaluate(
            db=db,
            confidence_score=confidence_score,
            drift_flags=drift_flags,
            current_mode=current_mode
        )

        # -----------------------------------------------
        # ETHICAL ENFORCEMENT: if mode was escalated to SAFE,
        # block execution immediately
        # -----------------------------------------------
        if final_mode == "SAFE" and current_mode != "SAFE":

            create_audit_log(
                db=db,
                event_type="SAFE_BLOCKED",
                actor="system",
                mode_at_time="SAFE",
                decision="blocked",
                risk_score=risk_score,
                reference_id=medicine_id,
                reference_table="medicines",
            )

            _log_execution(
                db,
                status="BLOCKED_BY_ETHICS",
                message="Ethical safety enforcement escalated mode to SAFE"
            )

            return {
                "status": "blocked",
                "reason": "Ethical safety enforcement — mode escalated to SAFE"
            }

        # -----------------------------------------------
        # REVIEW MODE (original or ethically escalated)
        # -----------------------------------------------
        if final_mode == "REVIEW" or reason == "REVIEW_MODE_ACTIVE":

            review_id = _create_review_record(
                db=db,
                medicine_id=medicine_id,
                risk_score=risk_score,
                action=action,
                quantity=final_quantity
            )

            create_audit_log(
                db=db,
                event_type="REVIEW_CREATED",
                actor="system",
                mode_at_time=final_mode,
                decision="pending",
                risk_score=risk_score,
                reference_id=review_id,
                reference_table="mitigation_reviews",
            )

            _log_execution(
                db,
                status="PENDING_REVIEW_CREATED",
                message=f"Mitigation queued for review. Review ID: {review_id}"
            )

            return {
                "status": "pending_review",
                "review_id": review_id
            }

        # ---------------- AUTO MODE ----------------
        result = _execute_action(
            db=db,
            medicine_id=medicine_id,
            action=action,
            risk_snapshot=risk_snapshot,
            final_quantity=final_quantity,
            risk_score=risk_score
        )

        if result.get("status") == "executed":

            create_audit_log(
                db=db,
                event_type="MITIGATION_EXECUTED",
                actor="system",
                mode_at_time="AUTO",
                decision="executed",
                risk_score=risk_score,
                reference_id=medicine_id,
                reference_table="medicines",
            )

        return result

    finally:
        db.close()


# =====================================================
# REVIEW RECORD CREATION
# =====================================================

def _create_review_record(db: Session, medicine_id: int, risk_score: int, action: str, quantity: int):

    payload = {
        "medicine_id": medicine_id,
        "action": action,
        "quantity": quantity,
        "risk_score": risk_score
    }

    review = MitigationReview(
        mitigation_id=medicine_id,
        risk_score=risk_score,
        action_type=action,
        payload=json.dumps(payload),
        status="pending",
        created_at=datetime.utcnow()
    )

    db.add(review)
    db.commit()
    db.refresh(review)

    return review.id


# =====================================================
# EXECUTE FROM STORED PAYLOAD (ADMIN APPROVAL PATH)
# =====================================================

def execute_mitigation_from_payload(payload: dict):
    """
    Used ONLY after admin approval.
    Deterministic execution from stored snapshot.
    """

    db: Session = SessionLocal()

    try:
        result = _execute_action(
            db=db,
            medicine_id=payload["medicine_id"],
            action=payload["action"],
            risk_snapshot={},
            final_quantity=payload["quantity"],
            risk_score=payload.get("risk_score", 0)
        )

        if result.get("status") == "executed":
            create_audit_log(
                db=db,
                event_type="MITIGATION_EXECUTED",
                actor="system",
                mode_at_time="REVIEW",
                decision="executed",
                risk_score=payload.get("risk_score", 0),
                reference_id=payload["medicine_id"],
                reference_table="medicines",
            )

        return result

    finally:
        db.close()


# =====================================================
# INTERNAL EXECUTION ENGINE
# =====================================================

def _execute_action(db: Session, medicine_id: int, action: str,
                    risk_snapshot: dict, final_quantity: int, risk_score: int):

    if action == "RESTOCK_IMMEDIATE":

        if risk_score >= SAFE_AUTO_THRESHOLD:

            trigger_fulfillment(
                medicine_id=medicine_id,
                quantity=final_quantity
            )

            _log_execution(
                db,
                status="AUTO_EXECUTED",
                message=f"RESTOCK_IMMEDIATE executed with adaptive qty {final_quantity}"
            )

            return {
                "status": "executed",
                "action": action,
                "quantity": final_quantity
            }

        return {"status": "blocked", "reason": "Risk below threshold"}

    elif action == "SAFETY_STOCK_INCREASE":

        if risk_snapshot.get("acceleration_factor", 0) > 0.3:

            trigger_fulfillment(
                medicine_id=medicine_id,
                quantity=final_quantity
            )

            _log_execution(
                db,
                status="AUTO_EXECUTED",
                message=f"SAFETY_STOCK_INCREASE executed with adaptive qty {final_quantity}"
            )

            return {
                "status": "executed",
                "action": action,
                "quantity": final_quantity
            }

        return {"status": "blocked", "reason": "No demand acceleration"}

    elif action in ["SUPPLIER_ESCALATION", "MONITOR"]:
        return {"status": "manual_required", "action": action}

    return {"status": "no_action"}


# =====================================================
# FULFILLMENT LOG
# =====================================================

def _log_execution(db: Session, status: str, message: str):
    log = FulfillmentLog(
        order_id=None,
        status=status,
        message=message
    )

    db.add(log)
    db.commit()