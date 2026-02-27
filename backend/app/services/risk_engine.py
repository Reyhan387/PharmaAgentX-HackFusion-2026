from backend.app.schemas.ai_context_schema import AIContext


def calculate_risk_score(context: AIContext) -> dict:
    """
    Advanced deterministic risk scoring engine (0–100)
    Includes:
    - Age factor
    - Chronic disease burden
    - Polypharmacy
    - Allergy complexity
    - Refill adherence
    - Overdue medicines
    """

    score = 0
    decision_trace = {}

    # =====================================================
    # 1️⃣ Age Risk (0–15)
    # =====================================================
    age_score = 0
    age = context.demographics.age

    if age:
        if age >= 75:
            age_score = 15
        elif age >= 60:
            age_score = 10
        elif age >= 40:
            age_score = 5
        else:
            age_score = 2

    score += age_score

    decision_trace["age"] = {
        "age": age,
        "score": age_score
    }

    # =====================================================
    # 2️⃣ Chronic Conditions (0–20)
    # =====================================================
    chronic_conditions = context.medical_history.chronic_conditions or []

    chronic_score = min(20, len(chronic_conditions) * 7)
    score += chronic_score

    decision_trace["chronic_conditions"] = {
        "count": len(chronic_conditions),
        "conditions": chronic_conditions,
        "score": chronic_score
    }

    # =====================================================
    # 3️⃣ Polypharmacy Risk (0–15)
    # =====================================================
    meds = context.medical_history.current_medications or []

    if len(meds) >= 6:
        med_score = 15
    elif len(meds) >= 4:
        med_score = 10
    elif len(meds) >= 2:
        med_score = 5
    else:
        med_score = 2

    score += med_score

    decision_trace["polypharmacy"] = {
        "medication_count": len(meds),
        "score": med_score
    }

    # =====================================================
    # 4️⃣ Allergy Complexity (0–10)
    # =====================================================
    allergies = context.medical_history.allergies or []

    if len(allergies) >= 3:
        allergy_score = 10
    elif len(allergies) >= 1:
        allergy_score = 5
    else:
        allergy_score = 0

    score += allergy_score

    decision_trace["allergies"] = {
        "count": len(allergies),
        "score": allergy_score
    }

    # =====================================================
    # 5️⃣ Overdue Medicines Risk (0–25)
    # =====================================================
    overdue_meds = context.medical_history.overdue_medicines if hasattr(
        context.medical_history, "overdue_medicines"
    ) else []

    overdue_score = min(25, len(overdue_meds) * 8)
    score += overdue_score

    decision_trace["overdue_medicines"] = {
        "count": len(overdue_meds),
        "score": overdue_score
    }

    # =====================================================
    # 6️⃣ Adherence Risk (0–15)
    # =====================================================
    adherence_score = 0
    avg_delay = getattr(context.medical_history, "average_delay_days", 0)

    if avg_delay > 14:
        adherence_score = 15
    elif avg_delay > 7:
        adherence_score = 10
    elif avg_delay > 2:
        adherence_score = 5
    else:
        adherence_score = 2

    score += adherence_score

    decision_trace["adherence"] = {
        "average_delay_days": avg_delay,
        "score": adherence_score
    }

    # =====================================================
    # Final Risk Category
    # =====================================================
    score = min(100, score)

    if score < 30:
        risk_level = "Low"
    elif score < 55:
        risk_level = "Medium"
    elif score < 75:
        risk_level = "High"
    else:
        risk_level = "Critical"

    return {
        "risk_score": score,
        "risk_level": risk_level,
        "decision_trace": decision_trace
    }