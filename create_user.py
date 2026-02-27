from backend.app.core.database import SessionLocal
from backend.app.models import User, Patient
from backend.app.core.security import hash_password

db = SessionLocal()

patient = db.query(Patient).first()

if not patient:
    print("No patient found")
else:
    user = User(
        email="test@pharma.com",
        password_hash=hash_password("123456"),
        role="patient",
        patient_id=patient.patient_id
    )

    db.add(user)
    db.commit()
    print("User created successfully")

db.close()