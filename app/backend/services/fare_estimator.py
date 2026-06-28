def estimate_journey_fare(item_type, data):
    duration = get_duration(item_type, data)
    train_quality = get_train_quality(item_type, data)
    transfers = get_transfers(item_type, data)
    stops = get_stops(item_type, data)

    if duration <= 0:
        duration = estimate_duration_from_stops(stops)

    base_fare = 120
    distance_like_score = max(duration * 55, stops * 8)

    fare = base_fare + distance_like_score

    if train_quality == "premium":
        fare *= 1.75
    elif train_quality == "superfast":
        fare *= 1.35
    elif train_quality == "express":
        fare *= 1.15

    if transfers > 0:
        fare *= 0.92

    estimated_fare = round_to_nearest_10(fare)

    split_saving = estimate_split_saving(
        item_type=item_type,
        estimated_fare=estimated_fare,
        transfers=transfers,
        train_quality=train_quality,
    )

    return {
        "estimated_fare": estimated_fare,
        "currency": "INR",
        "split_saving_estimate": split_saving,
        "estimated_after_split": max(estimated_fare - split_saving, 0),
        "confidence": get_confidence(item_type, duration, stops),
        "note": "Estimated fare, not official railway fare",
    }


def get_duration(item_type, data):
    if item_type == "direct":
        return float(data.get("duration_hours") or 0)

    if item_type == "one_transfer":
        return float(data.get("total_duration_hours") or 0)

    if item_type == "multi_transfer":
        return float(data.get("total_duration_hours") or 0)

    return 0


def get_stops(item_type, data):
    if item_type == "direct":
        return int(data.get("stops") or 0)

    if item_type == "one_transfer":
        return int(data.get("total_stops") or 0)

    if item_type == "multi_transfer":
        return int(data.get("total_stops") or 0)

    return 0


def get_transfers(item_type, data):
    if item_type == "direct":
        return 0

    if item_type == "one_transfer":
        return 1

    if item_type == "multi_transfer":
        return int(data.get("transfers") or 0)

    return 0


def get_train_quality(item_type, data):
    text_parts = []

    if item_type == "direct":
        text_parts.append(data.get("train_name"))

    if item_type == "one_transfer":
        text_parts.append(data.get("first_train_name"))
        text_parts.append(data.get("second_train_name"))

    if item_type == "multi_transfer":
        for leg in data.get("train_legs", []):
            text_parts.append(leg.get("train_name"))
            text_parts.append(leg.get("train_type"))

    text = " ".join(str(part or "") for part in text_parts).upper()

    if "RAJDHANI" in text or "DURONTO" in text or "SHATABDI" in text or "VANDE" in text:
        return "premium"

    if "SUPERFAST" in text or " SF " in f" {text} ":
        return "superfast"

    if "EXPRESS" in text:
        return "express"

    return "standard"


def estimate_duration_from_stops(stops):
    if stops <= 0:
        return 12

    return max(stops * 0.12, 2)


def estimate_split_saving(item_type, estimated_fare, transfers, train_quality):
    if estimated_fare <= 0:
        return 0

    saving_rate = 0.06

    if transfers > 0:
        saving_rate += 0.04

    if train_quality in {"premium", "superfast"}:
        saving_rate += 0.03

    if item_type == "multi_transfer":
        saving_rate += 0.02

    saving = estimated_fare * saving_rate

    return round_to_nearest_10(min(saving, estimated_fare * 0.22))


def get_confidence(item_type, duration, stops):
    if duration > 0 and stops > 0:
        return "medium"

    if item_type == "direct":
        return "medium"

    return "low"


def round_to_nearest_10(value):
    return int(round(value / 10.0) * 10)
