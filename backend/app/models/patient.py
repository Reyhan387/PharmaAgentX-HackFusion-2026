from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class Patient(Base):
    __tablename__ = "patients"

    # Internal Primary Key (System ID)
    id = Column(Integer, primary_key=True, index=True)

    # External Business ID (from Excel like PAT004 etc.)
    external_patient_id = Column(String, unique=True, index=True)

    # Basic Info
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String, nullable=False)

    # Foreign Key → Users table
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationship with User (One User → Many Patients)
    owner = relationship("User", back_populates="patients")

    # Relationship with Orders
    orders = relationship(
        "Order",
        back_populates="patient",
        cascade="all, delete-orphan"
    )

    # One-to-One relationship with MedicalHistory
    medical_history = relationship(
        "MedicalHistory",
        back_populates="patient",
        uselist=False,
        cascade="all, delete-orphan"
    )