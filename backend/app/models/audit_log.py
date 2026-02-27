from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from backend.app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String, nullable=False)
    actor = Column(String, nullable=False)
    risk_score = Column(Integer, nullable=True)
    mode_at_time = Column(String, nullable=False)
    decision = Column(String, nullable=False)
    reference_id = Column(Integer, nullable=True)
    reference_table = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)