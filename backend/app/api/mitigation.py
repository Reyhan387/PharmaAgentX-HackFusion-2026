from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..services.mitigation_service import MitigationRecommendationService

# DO NOT define prefix here (already defined in main.py)
router = APIRouter(tags=["Mitigation"])

@router.get("/{medicine_id}")
def get_mitigation(medicine_id: int, db: Session = Depends(get_db)):
    service = MitigationRecommendationService(db)
    return service.get_mitigation_recommendation(medicine_id)