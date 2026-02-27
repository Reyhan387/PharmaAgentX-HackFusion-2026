from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func

from backend.app.core.database import Base


class FulfillmentLog(Base):
    __tablename__ = "fulfillment_logs"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    status = Column(String, default="PROCESSING")
    message = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())