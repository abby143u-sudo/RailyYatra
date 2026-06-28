from datetime import datetime


def time_difference_hours(departure, arrival):
    try:
        dep = datetime.strptime(departure, "%H:%M:%S")
        arr = datetime.strptime(arrival, "%H:%M:%S")
        diff = (arr - dep).total_seconds() / 3600

        if diff < 0:
            diff += 24

        return round(diff, 2)
    except Exception:
        return None


def calculate_journey_score(train):
    score = 1000
    reasons = []

    train_name = (train.get("train_name") or "").upper()
    stops = int(train.get("stops") or 0)

    if "VANDE BHARAT" in train_name:
        score += 140
        reasons.append("Premium Vande Bharat service")
    elif "RAJDHANI" in train_name:
        score += 120
        reasons.append("Premium Rajdhani service")
    elif "SHATABDI" in train_name:
        score += 100
        reasons.append("Premium Shatabdi service")
    elif "DURONTO" in train_name:
        score += 90
        reasons.append("Duronto service")
    elif "SF" in train_name or "SUPERFAST" in train_name:
        score += 50
        reasons.append("Superfast train")
    elif "EXPRESS" in train_name:
        score += 25
        reasons.append("Express train")

    score -= stops

    if stops <= 50:
        reasons.append("Low stop count")
    elif stops <= 100:
        reasons.append("Moderate stop count")
    else:
        reasons.append("High stop count")

    duration = time_difference_hours(train.get("departure"), train.get("arrival"))

    if duration is not None:
        score -= int(duration)
        if duration <= 10:
            reasons.append("Fast journey")
        elif duration <= 15:
            reasons.append("Reasonable travel time")
        else:
            reasons.append("Long travel time")
    else:
        reasons.append("Journey duration unavailable")

    return {
        **train,
        "duration_hours": duration,
        "journey_score": score,
        "score": score,
        "reasons": reasons,
    }
