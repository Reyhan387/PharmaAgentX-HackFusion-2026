from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.core.database import SessionLocal
from backend.app.core.security import get_current_user
from backend.app.services.refill_service import (
    calculate_refill_date,
    get_status_and_risk,
    get_latest_orders
)

router = APIRouter(prefix="/patients", tags=["Patient Dashboard"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/summary")
def patient_summary(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):

    # 🔐 If not admin, block access
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    latest_orders = get_latest_orders(db)

    patient_data = {}

    for order in latest_orders:

        refill_date = calculate_refill_date(order)
        if not refill_date:
            continue

        status, risk = get_status_and_risk(refill_date)

        pid = order.patient_id

        if pid not in patient_data:
            patient_data[pid] = {
                "total_medicines": 0,
                "overdue": 0,
                "due_soon": 0,
                "ok": 0
            }

        patient_data[pid]["total_medicines"] += 1
        patient_data[pid][status] += 1

    results = []

    for pid, data in patient_data.items():

        if data["overdue"] > 0:
            overall_risk = "High"
        elif data["due_soon"] > 0:
            overall_risk = "Medium"
        else:
            overall_risk = "Low"

        results.append({
            "patient_id": pid,
            "total_medicines": data["total_medicines"],
            "overdue": data["overdue"],
            "due_soon": data["due_soon"],
            "ok": data["ok"],
            "overall_risk": overall_risk
        })

    return {
        "total_patients": len(results),
        "data": results
    }