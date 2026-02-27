from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from backend.app.core.database import Base


class User(Base):
    __tablename__ = "users"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Authentication Fields
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    # Role-Based Access Control
    role = Column(String, nullable=False, default="patient")

    # Relationships
    # One User → Many Patients
    patients = relationship(
        "Patient",
        back_populates="owner",
        cascade="all, delete"
    )