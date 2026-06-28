MAJOR_SPLIT_HUBS = {
    ("PNBE", "NDLS"): ["MGS", "DDU", "BSB", "PRYJ", "CNB"],
    ("NDLS", "PNBE"): ["CNB", "PRYJ", "BSB", "DDU", "MGS"],
    ("PNBE", "DLI"): ["MGS", "DDU", "BSB", "PRYJ", "CNB"],
    ("DLI", "PNBE"): ["CNB", "PRYJ", "BSB", "DDU", "MGS"],
    ("PNBE", "ANVT"): ["MGS", "DDU", "BSB", "PRYJ", "CNB"],
    ("ANVT", "PNBE"): ["CNB", "PRYJ", "BSB", "DDU", "MGS"],
}


def build_split_ticket_plan(item_type, data, fare, source, destination):
    estimated_fare = int(fare.get("estimated_fare") or 0)
    saving = int(fare.get("split_saving_estimate") or 0)
    after_split = int(fare.get("estimated_after_split") or 0)

    if estimated_fare <= 0 or saving <= 0:
        return no_split_plan("Fare saving not strong enough yet")

    if item_type == "direct":
        return build_direct_split_plan(
            data=data,
            source=source,
            destination=destination,
            estimated_fare=estimated_fare,
            after_split=after_split,
            saving=saving,
        )

    if item_type == "one_transfer":
        return build_one_transfer_split_plan(
            data=data,
            source=source,
            destination=destination,
            estimated_fare=estimated_fare,
            after_split=after_split,
            saving=saving,
        )

    if item_type == "multi_transfer":
        return build_multi_transfer_split_plan(
            data=data,
            source=source,
            destination=destination,
            estimated_fare=estimated_fare,
            after_split=after_split,
            saving=saving,
        )

    return no_split_plan("Split plan not available for this route type")


def build_direct_split_plan(data, source, destination, estimated_fare, after_split, saving):
    split_station = choose_split_station(source, destination)

    if not split_station:
        return no_split_plan("No reliable split station found for this direct route")

    train_no = data.get("train_no")
    train_name = data.get("train_name")

    first_fare = round_to_nearest_10(after_split * 0.45)
    second_fare = max(after_split - first_fare, 0)

    segments = [
        {
            "from": source,
            "to": split_station,
            "train_no": train_no,
            "train_name": train_name,
            "estimated_fare": first_fare,
        },
        {
            "from": split_station,
            "to": destination,
            "train_no": train_no,
            "train_name": train_name,
            "estimated_fare": second_fare,
        },
    ]

    return {
        "recommended": True,
        "strategy": "Split same train into two tickets",
        "split_points": [split_station],
        "ticket_count": len(segments),
        "estimated_original_fare": estimated_fare,
        "estimated_split_fare": after_split,
        "estimated_saving": saving,
        "confidence": "medium",
        "reason": f"Try splitting the same train ticket at {split_station} to compare fare.",
        "segments": segments,
        "note": "Estimated split-ticket logic. Official fare should be checked later.",
    }


def build_one_transfer_split_plan(data, source, destination, estimated_fare, after_split, saving):
    transfer_station = data.get("transfer_station")

    if not transfer_station:
        return no_split_plan("Transfer station not available")

    first_fare = round_to_nearest_10(after_split * 0.48)
    second_fare = max(after_split - first_fare, 0)

    segments = [
        {
            "from": source,
            "to": transfer_station,
            "train_no": data.get("first_train"),
            "train_name": data.get("first_train_name"),
            "estimated_fare": first_fare,
        },
        {
            "from": transfer_station,
            "to": destination,
            "train_no": data.get("second_train"),
            "train_name": data.get("second_train_name"),
            "estimated_fare": second_fare,
        },
    ]

    return {
        "recommended": True,
        "strategy": "Natural split at transfer station",
        "split_points": [transfer_station],
        "ticket_count": len(segments),
        "estimated_original_fare": estimated_fare,
        "estimated_split_fare": after_split,
        "estimated_saving": saving,
        "confidence": "high",
        "reason": f"This route already changes train at {transfer_station}, so split-ticket comparison is useful.",
        "segments": segments,
        "note": "Estimated split-ticket logic. Official fare should be checked later.",
    }


def build_multi_transfer_split_plan(data, source, destination, estimated_fare, after_split, saving):
    legs = data.get("train_legs", [])

    if not legs:
        return no_split_plan("Train legs not available")

    segments = []
    split_points = []

    segment_fares = distribute_fare(after_split, len(legs))

    for index, leg in enumerate(legs):
        from_station = leg.get("from") or source
        to_station = leg.get("to") or destination

        if index < len(legs) - 1:
            split_points.append(to_station)

        segments.append({
            "from": from_station,
            "to": to_station,
            "train_no": leg.get("train_no"),
            "train_name": leg.get("train_name"),
            "estimated_fare": segment_fares[index],
        })

    return {
        "recommended": True,
        "strategy": "Split by train legs",
        "split_points": split_points,
        "ticket_count": len(segments),
        "estimated_original_fare": estimated_fare,
        "estimated_split_fare": after_split,
        "estimated_saving": saving,
        "confidence": "high" if len(segments) > 1 else "medium",
        "reason": "This journey has clear train-leg segments, so separate ticket comparison is useful.",
        "segments": segments,
        "note": "Estimated split-ticket logic. Official fare should be checked later.",
    }


def choose_split_station(source, destination):
    source = str(source or "").upper()
    destination = str(destination or "").upper()

    candidates = MAJOR_SPLIT_HUBS.get((source, destination), [])

    if candidates:
        return candidates[0]

    return None


def distribute_fare(total_fare, count):
    if count <= 0:
        return []

    base = round_to_nearest_10(total_fare / count)
    fares = [base for _ in range(count)]

    difference = total_fare - sum(fares)
    fares[-1] += difference

    return fares


def no_split_plan(reason):
    return {
        "recommended": False,
        "strategy": "No split recommended",
        "split_points": [],
        "ticket_count": 1,
        "estimated_original_fare": None,
        "estimated_split_fare": None,
        "estimated_saving": 0,
        "confidence": "low",
        "reason": reason,
        "segments": [],
        "note": "Split-ticket estimate not available.",
    }


def round_to_nearest_10(value):
    return int(round(float(value) / 10.0) * 10)
