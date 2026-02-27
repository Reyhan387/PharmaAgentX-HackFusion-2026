from backend.app.core.database import SessionLocal
from backend.app.models import User
from backend.app.core.security import verify_password


def authenticate_user(email: str, password: str):
    db = SessionLocal()

    try:
        user = db.query(User).filter(User.email == email).first()

        if not user:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        return user  # ✅ RETURN USER OBJECT

    finally:
        db.close()