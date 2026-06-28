from backend.services.official_fare_service import get_official_fare


class FareSourceAdapter:
    name = "base"
    priority = 999
    enabled = False

    def lookup(self, train_no, source, destination, class_code="SL"):
        raise NotImplementedError


class LocalFareTableAdapter(FareSourceAdapter):
    name = "local_fare_table"
    priority = 1
    enabled = True

    def lookup(self, train_no, source, destination, class_code="SL"):
        row = get_official_fare(
            train_no=train_no,
            source=source,
            destination=destination,
            class_code=class_code,
        )

        if not row:
            return {
                "found": False,
                "provider": self.name,
                "message": "Fare not found in local fare table",
            }

        return {
            "found": True,
            "provider": self.name,
            "train_no": row["train_no"],
            "source": row["source"],
            "destination": row["destination"],
            "class_code": row["class_code"],
            "fare": row["fare"],
            "currency": "INR",
            "confidence": "high",
            "source_type": row["source_type"],
            "updated_at": row["updated_at"],
            "note": "Fare found in local verified fare table",
        }


class LiveFarePlaceholderAdapter(FareSourceAdapter):
    name = "future_live_fare_source"
    priority = 2
    enabled = False

    def lookup(self, train_no, source, destination, class_code="SL"):
        return {
            "found": False,
            "provider": self.name,
            "message": "Live fare source is not connected yet",
        }


FARE_SOURCES = [
    LocalFareTableAdapter(),
    LiveFarePlaceholderAdapter(),
]


def get_fare_sources():
    return [
        {
            "name": source.name,
            "priority": source.priority,
            "enabled": source.enabled,
        }
        for source in sorted(FARE_SOURCES, key=lambda item: item.priority)
    ]


def lookup_best_fare(train_no, source, destination, class_code="SL"):
    for adapter in sorted(FARE_SOURCES, key=lambda item: item.priority):
        if not adapter.enabled:
            continue

        result = adapter.lookup(
            train_no=train_no,
            source=source,
            destination=destination,
            class_code=class_code,
        )

        if result.get("found"):
            return result

    return {
        "found": False,
        "train_no": str(train_no or "").upper(),
        "source": str(source or "").upper(),
        "destination": str(destination or "").upper(),
        "class_code": str(class_code or "SL").upper(),
        "fare": None,
        "currency": "INR",
        "confidence": "none",
        "provider": None,
        "message": "Fare not found in any enabled fare source",
    }


def lookup_route_fare(item_type, data, source, destination, class_code="SL"):
    if item_type == "direct":
        return lookup_direct_route_fare(data, source, destination, class_code)

    if item_type == "one_transfer":
        return lookup_one_transfer_route_fare(data, source, destination, class_code)

    if item_type == "multi_transfer":
        return lookup_multi_transfer_route_fare(data, class_code)

    return {
        "found": False,
        "message": "Unsupported route type for fare lookup",
        "segments": [],
        "total_fare": None,
    }


def lookup_direct_route_fare(data, source, destination, class_code):
    fare = lookup_best_fare(
        train_no=data.get("train_no"),
        source=source,
        destination=destination,
        class_code=class_code,
    )

    if not fare.get("found"):
        return {
            "found": False,
            "message": fare.get("message"),
            "segments": [],
            "total_fare": None,
        }

    return {
        "found": True,
        "total_fare": fare["fare"],
        "currency": "INR",
        "confidence": fare["confidence"],
        "provider": fare["provider"],
        "segments": [fare],
    }


def lookup_one_transfer_route_fare(data, source, destination, class_code):
    transfer_station = data.get("transfer_station")

    first = lookup_best_fare(
        train_no=data.get("first_train"),
        source=source,
        destination=transfer_station,
        class_code=class_code,
    )

    second = lookup_best_fare(
        train_no=data.get("second_train"),
        source=transfer_station,
        destination=destination,
        class_code=class_code,
    )

    if not first.get("found") or not second.get("found"):
        return {
            "found": False,
            "message": "Complete fare not found for both transfer legs",
            "segments": [first, second],
            "total_fare": None,
        }

    return {
        "found": True,
        "total_fare": first["fare"] + second["fare"],
        "currency": "INR",
        "confidence": "high",
        "provider": "route_fare_adapter",
        "segments": [first, second],
    }


def lookup_multi_transfer_route_fare(data, class_code):
    legs = data.get("train_legs", [])

    if not legs:
        return {
            "found": False,
            "message": "No train legs available for fare lookup",
            "segments": [],
            "total_fare": None,
        }

    segments = []
    total = 0

    for leg in legs:
        fare = lookup_best_fare(
            train_no=leg.get("train_no"),
            source=leg.get("from"),
            destination=leg.get("to"),
            class_code=class_code,
        )

        segments.append(fare)

        if not fare.get("found"):
            return {
                "found": False,
                "message": "Complete fare not found for all train legs",
                "segments": segments,
                "total_fare": None,
            }

        total += fare["fare"]

    return {
        "found": True,
        "total_fare": total,
        "currency": "INR",
        "confidence": "high",
        "provider": "route_fare_adapter",
        "segments": segments,
    }
