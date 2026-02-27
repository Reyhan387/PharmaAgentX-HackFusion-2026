from fastapi import APIRouter, Depends, HTTPException
from backend.app.agent.agent import agent
from backend.app.core.security import get_current_user
from backend.app.core.database import SessionLocal
from backend.app.models.patient import Patient
import json

router = APIRouter()


@router.post("/agent/chat")
def agent_chat(message: str, user=Depends(get_current_user)):
    db = SessionLocal()

    try:
        # Get patient linked to logged-in user
        patient = db.query(Patient).filter(
            Patient.user_id == user.id
        ).first()

        if not patient:
            raise HTTPException(
                status_code=404,
                detail="Patient profile not found for this user."
            )

        # Inject patient ID context automatically
        full_prompt = (
            f"Patient ID: {patient.id}. "
            f"User says: {message}"
        )

        result = agent.invoke({"input": full_prompt})
        output = result["output"]

        # 🔥 Clean structured agent JSON if returned
        try:
            parsed = json.loads(output)
            if isinstance(parsed, dict) and "action_input" in parsed:
                return {"response": parsed["action_input"]}
        except Exception:
            pass

        return {"response": output}

    finally:
        db.close()