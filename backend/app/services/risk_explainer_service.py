def generate_risk_explanation(risk_data: dict) -> str:
    """
    Deterministic clinical explanation generator.
    No external API required.
    Hackathon-safe version.
    """

    level = risk_data.get("risk_level")
    trace = risk_data.get("decision_trace", {})

    reasons = []

    # Age
    if trace.get("age", {}).get("score", 0) >= 10:
        reasons.append("advanced age")

    # Chronic conditions
    if trace.get("chronic_conditions", {}).get("count", 0) > 0:
        reasons.append("chronic conditions")

    # Polypharmacy
    if trace.get("polypharmacy", {}).get("medication_count", 0) >= 3:
        reasons.append("polypharmacy")

    # Overdue meds
    if trace.get("overdue_medicines", {}).get("count", 0) > 0:
        reasons.append("overdue medications")

    # Adherence
    if trace.get("adherence", {}).get("average_delay_days", 0) > 7:
        reasons.append("poor refill adherence")

    if not reasons:
        return (
            "Patient currently presents low clinical risk with no significant "
            "contributing health or adherence concerns."
        )

    return (
        f"This patient is categorized as {level} risk due to "
        + ", ".join(reasons)
        + ". Clinical monitoring and follow-up are recommended."
    )