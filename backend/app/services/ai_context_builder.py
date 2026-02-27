from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from backend.app.models import Patient, MedicalHistory, Order

from backend.app.schemas.ai_context_schema import (
    AIContext,
    DemographicsContext,
    MedicalHistoryContext,
    OrderContext,
    OrderItem,
)


def build_ai_context(db: Session, patient_id: int) -> AIContext:

    # Fetch patient
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise ValueError("Patient not found")

    # Fetch medical history
    medical_history = (
        db.query(MedicalHistory)
        .filter(MedicalHistory.patient_id == patient_id)
        .first()
    )

    # Fetch recent orders (last 90 days)
    cutoff = datetime.utcnow().date() - timedelta(days=90)

    orders = (
        db.query(Order)
        .filter(
            Order.patient_id == patient_id,
            Order.order_date >= cutoff,   # ✅ FIXED (NOT created_at)
        )
        .all()
    )

    demographics = DemographicsContext(
        patient_id=patient.id,
        age=patient.age,
        gender=patient.gender,
    )

    medical_context = MedicalHistoryContext(
        chronic_conditions=(
            medical_history.chronic_conditions.split(",")
            if medical_history and medical_history.chronic_conditions
            else []
        ),
        allergies=(
            medical_history.allergies.split(",")
            if medical_history and medical_history.allergies
            else []
        ),
        current_medications=(
            medical_history.current_medications.split(",")
            if medical_history and medical_history.current_medications
            else []
        ),
        risk_score=medical_history.risk_score if medical_history else None,
    )

    order_context = OrderContext(
        recent_orders=[
            OrderItem(
                order_id=o.id,
                medicine_id=o.medicine_id,
                quantity=o.quantity,
                date=str(o.order_date),   # ✅ FIXED
                status="recorded",
            )
            for o in orders
        ]
    )

    return AIContext(
        demographics=demographics,
        medical_history=medical_context,
        orders=order_context,
    )