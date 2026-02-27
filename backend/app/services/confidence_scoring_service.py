# backend/app/services/confidence_scoring_service.py
# Deterministic Confidence Scoring Engine


def calculate_confidence_score(metrics: dict) -> float:
    """
    Compute a deterministic confidence score between 0.0 and 1.0 based on
    system health metrics.

    This function applies a series of hardcoded, rule-based penalties to a
    base score of 1.0. Because every rule is explicit and stateless, the
    result is fully reproducible given the same inputs — a requirement for
    healthcare-grade reliability.

    Parameters
    ----------
    metrics : dict
        Dictionary with the following keys:
            - risk_score (float)        : Normalized risk value in [0.0, 1.0]
            - drift_detected (bool)     : True when model/data drift is observed
            - multiplier_anomaly (bool) : True when the instability multiplier
                                         is outside its expected variance band
            - review_spike (bool)       : True when review volume has spiked
                                         beyond the alert threshold

    Returns
    -------
    float
        Confidence score rounded to 2 decimal places, always in [0.0, 1.0].
    """

    required_keys = {"risk_score", "drift_detected", "multiplier_anomaly", "review_spike"}
    missing = required_keys - metrics.keys()
    if missing:
        raise ValueError(f"Missing required metric keys: {missing}")

    risk_score = metrics["risk_score"]
    drift_detected = metrics["drift_detected"]
    multiplier_anomaly = metrics["multiplier_anomaly"]
    review_spike = metrics["review_spike"]

    if not (0.0 <= risk_score <= 1.0):
        raise ValueError(f"risk_score must be in [0.0, 1.0], got {risk_score}")

    # Start from a perfect confidence baseline
    score = 1.0

    # Penalty: detected data or model drift reduces trust in current outputs
    if drift_detected:
        score -= 0.2

    # Penalty: an anomalous instability multiplier signals unpredictable behaviour
    if multiplier_anomaly:
        score -= 0.2

    # Penalty: a review spike suggests elevated uncertainty in recent decisions
    if review_spike:
        score -= 0.1

    # Penalty: when risk exceeds the high-risk threshold (0.7), reduce the
    # score proportionally by the amount it overshoots that threshold.
    # This creates a graduated reduction rather than a hard cutoff.
    if risk_score > 0.7:
        score -= (risk_score - 0.7)

    # Clamp the result to [0.0, 1.0] so that stacked penalties never produce
    # an invalid score outside the defined confidence range.
    score = max(0.0, min(1.0, score))

    return round(score, 2)


if __name__ == "__main__":
    sample_metrics = {
        "risk_score": 0.8,
        "drift_detected": True,
        "multiplier_anomaly": False,
        "review_spike": True
    }
    print(calculate_confidence_score(sample_metrics))
