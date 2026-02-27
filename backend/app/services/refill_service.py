from datetime import timedelta, date
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.models.order import Order
from backend.app.models.patient import Patient
from backend.app.models.medicine import Medicine
from backend.app.models.refill_alert import RefillAlert


# -------------------------------
# Calculate refill date
# -------------------------------
def calculate_refill_date(order: Order):
    if not order.daily_dosage or order.daily_dosage <= 0:
        return None

    days_covered = order.quantity / order.daily_dosage
    return order.order_date + timedelta(days=int(days_covered))


# -------------------------------
# Determine status ONLY
# (Used by scheduler)
# -------------------------------
def get_status(refill_date):
    if not refill_date:
        return "unknown"

    today = date.today()

    if refill_date < today:
        return "overdue"
    elif (refill_date - today).days <= 3:
        return "due_soon"
    else:
        return "ok"


# -------------------------------
# Determine status + risk level
# (Used by existing API)
# -------------------------------
def get_status_and_risk(refill_date):
    if not refill_date:
        return "unknown", "Low"

    today = date.today()

    if refill_date < today:
        return "overdue", "High"
    elif (refill_date - today).days <= 3:
        return "due_soon", "Medium"
    else:
        return "ok", "Low"


# -------------------------------
# Get latest order per patient per medicine
# -------------------------------
def get_latest_orders(db: Session, patient_id: int):

    subquery = (
        db.query(
            Order.medicine_id,
            func.max(Order.order_date).label("latest_date")
        )
        .filter(Order.patient_id == patient_id)
        .group_by(Order.medicine_id)
        .subquery()
    )

    latest_orders = (
        db.query(Order)
        .join(
            subquery,
            (Order.medicine_id == subquery.c.medicine_id)
            & (Order.order_date == subquery.c.latest_date)
        )
        .filter(Order.patient_id == patient_id)
        .all()
    )

    return latest_orders


# ======================================================
# STEP 31 – Scheduled Refill Scan Engine
# ======================================================

def scan_and_create_refill_alerts(db: Session):

    patients = db.query(Patient).all()

    for patient in patients:
        latest_orders = get_latest_orders(db, patient.id)

        for order in latest_orders:

            refill_date = calculate_refill_date(order)
            status = get_status(refill_date)

            if status in ["overdue", "due_soon"]:

                medicine = db.query(Medicine).filter(
                    Medicine.id == order.medicine_id
                ).first()

                if not medicine:
                    continue

                existing_alert = (
                    db.query(RefillAlert)
                    .filter(
                        RefillAlert.patient_id == patient.id,
                        RefillAlert.medicine_name == medicine.name,
                        RefillAlert.status == status
                    )
                    .first()
                )

                if not existing_alert:
                    new_alert = RefillAlert(
                        patient_id=patient.id,
                        medicine_name=medicine.name,
                        expected_refill_date=str(refill_date),
                        status=status
                    )
                    db.add(new_alert)

    db.commit()