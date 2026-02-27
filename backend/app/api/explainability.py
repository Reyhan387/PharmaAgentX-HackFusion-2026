from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..services.explainability_service import get_medicine_risk_snapshot

router = APIRouter()

@router.get("/risk/{medicine_id}")
def get_risk_snapshot(medicine_id: int, db: Session = Depends(get_db)):
    return get_medicine_risk_snapshot(db, medicine_id)