from sqlalchemy import Column, Integer, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class MedicalHistory(Base):
    __tablename__ = "medical_history"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))

    chronic_conditions = Column(Text)
    allergies = Column(Text)
    current_medications = Column(Text)
    risk_score = Column(Float, default=0)

    patient = relationship("Patient")