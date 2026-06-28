def explain_recommendation(train):
    reasons = []

    name = (train.get("train_name") or "").upper()
    stops = train.get("stops", 0)
    duration = train.get("duration_hours")

    if "RAJDHANI" in name:
        reasons.append("Premium Rajdhani service")

    elif "VANDE BHARAT" in name:
        reasons.append("Premium Vande Bharat service")

    elif "SHATABDI" in name:
        reasons.append("Premium Shatabdi service")

    if duration is not None:
        if duration <= 10:
            reasons.append("Fast journey")
        elif duration <= 14:
            reasons.append("Comfortable overnight travel")
        else:
            reasons.append("Long-distance journey")

    if stops <= 20:
        reasons.append("Very few intermediate stops")
    elif stops <= 50:
        reasons.append("Limited intermediate stops")
    else:
        reasons.append("Covers many stations")

    if train.get("type") == "direct":
        reasons.append("No train change required")

    return reasons