from sqlalchemy import Column, Integer, String, DateTime, Boolean
from datetime import datetime
from ..core.database import Base


class InventoryEscalation(Base):
    __tablename__ = "inventory_escalations"

    id = Column(Integer, primary_key=True, index=True)
    medicine_id = Column(Integer, nullable=False)
    medicine_name = Column(String, nullable=False)
    current_stock = Column(Integer, nullable=False)
    threshold = Column(Integer, nullable=False)
    restock_triggered = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)