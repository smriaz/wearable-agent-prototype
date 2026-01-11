from __future__ import annotations


def determine_escalation(features: dict) -> dict:
    """
    Conservative, rule-based escalation (NOT LLM).
    Produces: level (low/medium/high) + confidence (low/medium/high) + rationale.
    """
    cov = features["coverage"]
    flags = features["flags"]

    wear_ok = cov["wear_ok_days"]
    days_present = cov["days_present"]
    missing_sleep = cov["missing_sleep_days"]

    # Confidence from coverage
    if days_present < 6 or wear_ok < 4:
        confidence = "low"
    elif missing_sleep >= 2:
        confidence = "medium"
    else:
        confidence = "high"

    # Count severities
    high_flags = [f for f in flags if f["severity"] == "high"]
    mod_flags = [f for f in flags if f["severity"] == "moderate"]

    # Escalation logic (bounded)
    level = "low"
    rationale = []

    # High: multiple high-severity physiological shifts + decent confidence
    high_types = {f["type"] for f in high_flags}
    if ("RHR_ELEVATED" in high_types and "SLEEP_REDUCED" in high_types) and confidence != "low":
        level = "high"
        rationale.append("Sustained RHR elevation plus substantial sleep reduction with usable coverage.")
    elif len(high_flags) >= 2 and confidence != "low":
        level = "high"
        rationale.append("Multiple high-severity flags with usable coverage.")
    elif len(high_flags) >= 1 and len(mod_flags) >= 2 and confidence == "high":
        level = "high"
        rationale.append("Combination of high and multiple moderate flags with good coverage.")
    else:
        # Medium: multiple moderate flags
        if len(mod_flags) >= 2 and confidence != "low":
            level = "medium"
            rationale.append("Multiple moderate changes detected over the last 7 days.")
        elif len(high_flags) == 1 and confidence == "low":
            level = "medium"
            rationale.append("Potentially important change detected, but data coverage is limited.")
        else:
            level = "low"
            rationale.append("No strong sustained changes detected, or changes are within normal variation.")

    return {
        "level": level,
        "confidence": confidence,
        "rationale": rationale,
        "flags": flags,
    }
