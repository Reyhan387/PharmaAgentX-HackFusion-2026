from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import get_current_user
from backend.app.models import Patient
from backend.app.services.ai_context_builder import build_ai_context
from backend.app.services.risk_engine import calculate_risk_score
from backend.app.services.risk_explainer_service import generate_risk_explanation

router = APIRouter(
    prefix="/ai-context",
    tags=["AI Intelligence"],
)


@router.get("/")
def get_ai_context(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Returns:
    - Full structured AI patient context
    - Deterministic risk scoring (0–100)
    - Risk category
    - Explainable decision trace
    - LLM-generated clinical summary
    """

    # =====================================================
    # 1️⃣ Fetch patient mapped to authenticated user
    # =====================================================
    patient = db.query(Patient).filter(
        Patient.user_id == current_user.id
    ).first()

    if not patient:
        raise HTTPException(
            status_code=404,
            detail="Patient profile not found"
        )

    # =====================================================
    # 2️⃣ Build AI Context
    # =====================================================
    context = build_ai_context(db, patient.id)

    # =====================================================
    # 3️⃣ Run Deterministic Risk Engine
    # =====================================================
    risk_data = calculate_risk_score(context)

    # =====================================================
    # 4️⃣ Generate LLM Clinical Explanation
    # =====================================================
    explanation = generate_risk_explanation(risk_data)

    # =====================================================
    # 5️⃣ Structured Response
    # =====================================================
    return {
        "patient_id": patient.id,
        "patient_name": patient.name,
        "ai_context": context.dict(),
        "risk_analysis": risk_data,
        "clinical_summary": explanation
    }