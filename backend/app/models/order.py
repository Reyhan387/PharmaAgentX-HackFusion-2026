from sqlalchemy import Column, Integer, ForeignKey, Date, Float, String
from sqlalchemy.orm import relationship

from backend.app.core.database import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)

    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    medicine_id = Column(Integer, ForeignKey("medicines.id"), nullable=False)

    quantity = Column(Integer, nullable=False)

    order_date = Column(Date, nullable=False)
    daily_dosage = Column(Float, nullable=False)
    dosage_frequency = Column(String, nullable=True)

    patient = relationship("Patient", back_populates="orders")
    medicine = relationship("Medicine", back_populates="orders")