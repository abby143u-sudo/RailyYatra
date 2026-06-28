from backend.services.fare_source_adapter import lookup_best_fare


def calculate_fare_coverage(item_type, data, source, destination, class_code="SL"):
    segments = build_expected_segments(
        item_type=item_type,
        data=data or {},
        source=source,
        destination=destination,
    )

    if not segments:
        return {
            "verified_segments": 0,
            "total_segments": 0,
            "coverage_percent": 0,
            "status": "unknown",
            "label": "Fare coverage unknown",
            "segments": [],
        }

    checked_segments = []
    verified_count = 0

    for segment in segments:
        result = lookup_best_fare(
            train_no=segment["train_no"],
            source=segment["source"],
            destination=segment["destination"],
            class_code=class_code,
        )

        is_verified = bool(result.get("found"))

        if is_verified:
            verified_count += 1

        checked_segments.append({
            **segment,
            "verified": is_verified,
            "fare": result.get("fare"),
            "provider": result.get("provider"),
        })

    total = len(segments)
    percent = round((verified_count / total) * 100)

    if percent == 100:
        status = "full"
        label = "100% verified fare"
    elif percent > 0:
        status = "partial"
        label = f"{verified_count}/{total} fare segments verified"
    else:
        status = "none"
        label = "Fare estimate only"

    return {
        "verified_segments": verified_count,
        "total_segments": total,
        "coverage_percent": percent,
        "status": status,
        "label": label,
        "segments": checked_segments,
    }


def build_expected_segments(item_type, data, source, destination):
    if item_type == "direct":
        return [{
            "train_no": data.get("train_no"),
            "source": source,
            "destination": destination,
        }]

    if item_type == "one_transfer":
        transfer = data.get("transfer_station")

        return [
            {
                "train_no": data.get("first_train"),
                "source": source,
                "destination": transfer,
            },
            {
                "train_no": data.get("second_train"),
                "source": transfer,
                "destination": destination,
            },
        ]

    if item_type == "multi_transfer":
        legs = data.get("train_legs", [])

        return [
            {
                "train_no": leg.get("train_no"),
                "source": leg.get("from"),
                "destination": leg.get("to"),
            }
            for leg in legs
        ]

    return []
