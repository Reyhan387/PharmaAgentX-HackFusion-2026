from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from ..core.database import Base

class MitigationReview(Base):
    __tablename__ = "mitigation_reviews"

    id = Column(Integer, primary_key=True, index=True)
    mitigation_id = Column(Integer, nullable=False)
    risk_score = Column(Integer, nullable=False)
    action_type = Column(String, nullable=False)
    payload = Column(Text, nullable=False)
    status = Column(String, default="pending")
    reviewed_by = Column(Integer, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)