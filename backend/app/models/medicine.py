from sqlalchemy import Column, Integer, String, Float, Boolean
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class Medicine(Base):
    __tablename__ = "medicines"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    stock = Column(Integer, nullable=False)
    prescription_required = Column(Boolean, default=False)

    orders = relationship("Order", back_populates="medicine")