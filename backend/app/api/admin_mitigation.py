from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import json

from ..core.database import get_db
from ..models.mitigation_review import MitigationReview
from ..services.mitigation_execution_service import execute_mitigation_from_payload
from ..models.fulfillment_log import FulfillmentLog
from ..core.security import admin_required

# ✅ STEP 44
from backend.app.services.audit_service import create_audit_log


router = APIRouter(
    prefix="/admin/mitigations",
    tags=["Admin Mitigations"]
)


# =====================================================
# GET PENDING REVIEWS
# =====================================================

@router.get("/pending")
def get_pending_reviews(
    admin=Depends(admin_required),
    db: Session = Depends(get_db)
):
    reviews = db.query(MitigationReview).filter(
        MitigationReview.status == "pending"
    ).all()

    return reviews


# =====================================================
# APPROVE REVIEW
# =====================================================

@router.post("/{review_id}/approve")
def approve_review(
    review_id: int,
    admin=Depends(admin_required),
    db: Session = Depends(get_db)
):

    review = db.query(MitigationReview).filter(
        MitigationReview.id == review_id
    ).first()

    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    if review.status != "pending":
        raise HTTPException(status_code=400, detail="Review already processed")

    # Update review state
    review.status = "approved"
    review.reviewed_by = admin.id
    review.reviewed_at = datetime.utcnow()
    db.commit()

    # ✅ STEP 44 — AUDIT LOG (APPROVED)
    create_audit_log(
        db=db,
        event_type="REVIEW_APPROVED",
        actor="admin",
        mode_at_time="REVIEW",
        decision="approved",
        risk_score=review.risk_score,
        reference_id=review.id,
        reference_table="mitigation_reviews",
    )

    # Execute mitigation from stored payload
    payload = json.loads(review.payload)
    execute_mitigation_from_payload(payload)

    # Log approval
    log = FulfillmentLog(
        order_id=None,
        status="APPROVED_BY_ADMIN",
        message=f"Review {review_id} approved and executed"
    )

    db.add(log)
    db.commit()

    return {"status": "approved_and_executed"}


# =====================================================
# REJECT REVIEW
# =====================================================

@router.post("/{review_id}/reject")
def reject_review(
    review_id: int,
    admin=Depends(admin_required),
    db: Session = Depends(get_db)
):

    review = db.query(MitigationReview).filter(
        MitigationReview.id == review_id
    ).first()

    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    if review.status != "pending":
        raise HTTPException(status_code=400, detail="Review already processed")

    review.status = "rejected"
    review.reviewed_by = admin.id
    review.reviewed_at = datetime.utcnow()
    db.commit()

    # ✅ STEP 44 — AUDIT LOG (REJECTED)
    create_audit_log(
        db=db,
        event_type="REVIEW_REJECTED",
        actor="admin",
        mode_at_time="REVIEW",
        decision="rejected",
        risk_score=review.risk_score,
        reference_id=review.id,
        reference_table="mitigation_reviews",
    )

    # Log rejection
    log = FulfillmentLog(
        order_id=None,
        status="REJECTED_BY_ADMIN",
        message=f"Review {review_id} rejected"
    )

    db.add(log)
    db.commit()

    return {"status": "rejected"}