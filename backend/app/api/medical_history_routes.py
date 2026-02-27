import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.database import SessionLocal
from backend.app.models import Patient, MedicalHistory
from backend.app.api.medical_history_schema import MedicalHistoryCreate
from backend.app.core.security import get_current_user


router = APIRouter(prefix="/medical-history", tags=["Medical History"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/")
def create_medical_history(
    data: MedicalHistoryCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if not current_user.patient_id:
        raise HTTPException(status_code=400, detail="User not linked to patient")

    patient = db.query(Patient).filter(
        Patient.patient_id == current_user.patient_id
    ).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    existing = db.query(MedicalHistory).filter(
        MedicalHistory.patient_id == patient.patient_id
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Medical history already exists")

    history = MedicalHistory(
        patient_id=patient.patient_id,
        chronic_conditions=json.dumps(data.chronic_conditions),
        allergies=json.dumps(data.allergies),
        current_medications=json.dumps(data.current_medications),
    )

    db.add(history)
    db.commit()
    db.refresh(history)

    return {"message": "Medical history created successfully"}