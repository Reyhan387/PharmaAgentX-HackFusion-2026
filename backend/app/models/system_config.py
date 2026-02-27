from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from backend.app.core.database import Base


class SystemConfig(Base):
    __tablename__ = "system_config"

    id = Column(Integer, primary_key=True, index=True)
    current_mode = Column(String, nullable=False)
    updated_by = Column(Integer, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow)