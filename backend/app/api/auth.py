from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.app.services.auth_service import authenticate_user
from backend.app.core.database import SessionLocal
from backend.app.models import User, Patient
from backend.app.core.security import (
    hash_password,
    create_access_token
)

router = APIRouter(tags=["Authentication"])


# ==========================
# Request Schemas
# ==========================

class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


# ==========================
# Register Endpoint
# ==========================

@router.post("/register")
def register(data: RegisterRequest):
    db = SessionLocal()

    try:
        # Check if email already exists
        existing_user = db.query(User).filter(User.email == data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )

        # Create User
        new_user = User(
            email=data.email,
            hashed_password=hash_password(data.password),
            role="patient"
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # 🔥 Automatically create linked Patient profile
        patient_profile = Patient(
            name="New Patient",
            age=0,
            gender="Not Specified",
            user_id=new_user.id
        )

        db.add(patient_profile)
        db.commit()

        return {
            "message": "User and Patient profile created successfully"
        }

    finally:
        db.close()


# ==========================
# Login Endpoint
# ==========================

@router.post("/login")
def login(data: LoginRequest):
    user = authenticate_user(data.email, data.password)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    access_token = create_access_token(
        data={
            "sub": user.email,
            "role": user.role
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }