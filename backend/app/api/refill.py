from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.database import SessionLocal
from backend.app.services.refill_service import (
    calculate_refill_date,
    get_status_and_risk,
    get_latest_orders
)

router = APIRouter(prefix="/refill", tags=["Refill"])


# Temporary DB dependency (simple and safe)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/predict")
def predict_refills(patient_id: int, db: Session = Depends(get_db)):
    """
    Predict refill status for a given patient.
    Pass patient_id as query parameter.
    Example:
    /refill/predict?patient_id=1
    """

    latest_orders = get_latest_orders(db, patient_id)

    results = []

    for order in latest_orders:

        refill_date = calculate_refill_date(order)

        if not refill_date:
            continue

        status, risk = get_status_and_risk(refill_date)

        results.append({
            "order_id": order.id,
            "patient_id": order.patient_id,
            "medicine_id": order.medicine_id,
            "medicine_name": order.medicine.name,
            "order_date": order.order_date,
            "quantity": order.quantity,
            "daily_dosage": order.daily_dosage,
            "refill_date": refill_date,
            "status": status,
            "risk_level": risk
        })

    return {
        "total_cases": len(results),
        "data": results
    }