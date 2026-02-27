from datetime import date, timedelta
from sqlalchemy.orm import Session
from backend.app.models.order import Order


def predict_refills(db: Session, patient_id: int):
    """
    Predict refill dates based on:
    - order quantity
    - daily dosage
    - last order date
    """

    orders = (
        db.query(Order)
        .filter(Order.patient_id == patient_id)
        .order_by(Order.order_date.desc())
        .all()
    )

    predictions = []
    today = date.today()

    for order in orders:

        # Skip invalid dosage
        if not order.daily_dosage or order.daily_dosage <= 0:
            continue

        # Calculate supply duration (rounded)
        days_supply = round(order.quantity / order.daily_dosage)

        expected_refill_date = order.order_date + timedelta(days=days_supply)

        is_overdue = today > expected_refill_date

        days_remaining = (expected_refill_date - today).days

        predictions.append({
            "medicine_id": order.medicine.id,
            "medicine_name": order.medicine.name,
            "last_order_date": order.order_date.isoformat(),
            "quantity_bought": order.quantity,
            "daily_dosage": order.daily_dosage,
            "days_supply": days_supply,
            "expected_refill_date": expected_refill_date.isoformat(),
            "days_remaining": max(days_remaining, 0),
            "overdue": is_overdue
        })

    return predictions