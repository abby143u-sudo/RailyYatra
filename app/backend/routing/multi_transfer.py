from collections import defaultdict, deque
from backend.database.connection import fetch_all


_data_cache = None


def load_train_data():
    global _data_cache

    if _data_cache is not None:
        return _data_cache

    stop_rows = fetch_all("""
        SELECT train_no, station_code, stop_order, arrival_time, departure_time, day
        FROM train_stops
        ORDER BY train_no, CAST(stop_order AS INTEGER)
    """)

    train_rows = fetch_all("""
        SELECT train_no, train_name, train_type
        FROM trains
    """)

    train_info = {}

    for row in train_rows:
        train_no = str(row["train_no"])
        train_info[train_no] = {
            "train_name": row.get("train_name"),
            "train_type": row.get("train_type"),
        }

    train_routes = defaultdict(list)

    for row in stop_rows:
        train_no = str(row["train_no"])

        train_routes[train_no].append({
            "station_code": row["station_code"],
            "stop_order": int(row["stop_order"]),
            "arrival_time": row.get("arrival_time"),
            "departure_time": row.get("departure_time"),
            "day": row.get("day"),
        })

    station_to_positions = defaultdict(list)

    for train_no, stops in train_routes.items():
        for index, stop in enumerate(stops):
            station_to_positions[stop["station_code"]].append({
                "train_no": train_no,
                "index": index,
            })

    station_train_count = {
        station: len(items)
        for station, items in station_to_positions.items()
    }

    _data_cache = {
        "train_routes": dict(train_routes),
        "station_to_positions": dict(station_to_positions),
        "station_train_count": station_train_count,
        "train_info": train_info,
    }

    return _data_cache


def find_multi_transfer_routes(source, destination, max_transfers=3, limit=10):
    source = source.upper().strip()
    destination = destination.upper().strip()

    data = load_train_data()
    train_routes = data["train_routes"]
    station_to_positions = data["station_to_positions"]
    station_train_count = data["station_train_count"]
    train_info = data["train_info"]

    if source not in station_to_positions or destination not in station_to_positions:
        return []

    routes = []
    queue = deque()

    queue.append({
        "current_station": source,
        "legs": [],
        "used_trains": set(),
        "visited_stations": {source},
    })

    max_legs = max_transfers + 1
    expansions = 0
    max_expansions = 25000

    while queue and len(routes) < limit and expansions < max_expansions:
        state = queue.popleft()
        expansions += 1

        current_station = state["current_station"]
        legs = state["legs"]
        used_trains = state["used_trains"]
        visited_stations = state["visited_stations"]

        if len(legs) >= max_legs:
            continue

        leg_options = find_forward_train_legs(
            current_station=current_station,
            destination=destination,
            train_routes=train_routes,
            station_to_positions=station_to_positions,
            station_train_count=station_train_count,
            train_info=train_info,
            used_trains=used_trains,
            visited_stations=visited_stations,
        )

        for leg in leg_options:
            new_legs = legs + [leg]

            if leg["to"] == destination:
                routes.append(build_route(source, destination, new_legs))
                continue

            if len(new_legs) >= max_legs:
                continue

            queue.append({
                "current_station": leg["to"],
                "legs": new_legs,
                "used_trains": used_trains | {leg["train_no"]},
                "visited_stations": visited_stations | {leg["to"]},
            })

    routes.sort(key=lambda route: route["score"], reverse=True)
    return routes[:limit]


def find_forward_train_legs(
    current_station,
    destination,
    train_routes,
    station_to_positions,
    station_train_count,
    train_info,
    used_trains,
    visited_stations,
):
    positions = station_to_positions.get(current_station, [])
    options = []

    major_hubs = {
        "PNBE", "DNR", "ARA", "BXR", "MGS", "DDU", "BSB",
        "PRYJ", "CNB", "LKO", "GZB", "NDLS", "ANVT", "DLI"
    }

    for pos in positions[:100]:
        train_no = str(pos["train_no"])

        if train_no in used_trains:
            continue

        route = train_routes.get(train_no, [])
        start_index = pos["index"]

        downstream = route[start_index + 1:]

        destination_stop = None

        for stop in downstream:
            if stop["station_code"] == destination:
                destination_stop = stop
                break

        if destination_stop:
            options.append(make_leg(
                train_no=train_no,
                from_station=current_station,
                to_station=destination,
                from_stop=route[start_index],
                to_stop=destination_stop,
                stop_count=destination_stop["stop_order"] - route[start_index]["stop_order"] + 1,
                is_destination=True,
                transfer_strength=9999,
                train_info=train_info,
            ))
            continue

        transfer_candidates = []

        for stop in downstream:
            station = stop["station_code"]

            if station in visited_stations:
                continue

            transfer_strength = station_train_count.get(station, 0)

            if station in major_hubs or transfer_strength >= 20:
                transfer_candidates.append({
                    "stop": stop,
                    "transfer_strength": transfer_strength,
                })

        transfer_candidates.sort(
            key=lambda item: item["transfer_strength"],
            reverse=True
        )

        for candidate in transfer_candidates[:8]:
            stop = candidate["stop"]

            options.append(make_leg(
                train_no=train_no,
                from_station=current_station,
                to_station=stop["station_code"],
                from_stop=route[start_index],
                to_stop=stop,
                stop_count=stop["stop_order"] - route[start_index]["stop_order"] + 1,
                is_destination=False,
                transfer_strength=candidate["transfer_strength"],
                train_info=train_info,
            ))

    options.sort(
        key=lambda leg: (
            leg["is_destination"],
            leg["leg_score"],
            leg["transfer_strength"],
            -leg["stop_count"],
        ),
        reverse=True
    )

    return options[:60]


def make_leg(
    train_no,
    from_station,
    to_station,
    from_stop,
    to_stop,
    stop_count,
    is_destination,
    transfer_strength,
    train_info,
):
    info = train_info.get(str(train_no), {})

    train_name = info.get("train_name")
    train_type = info.get("train_type")

    duration_hours = duration_between(
        from_stop.get("departure_time"),
        from_stop.get("day"),
        to_stop.get("arrival_time"),
        to_stop.get("day"),
    )

    leg = {
        "train_no": str(train_no),
        "train_name": train_name,
        "train_type": train_type,
        "from": from_station,
        "to": to_station,
        "start_time": from_stop.get("departure_time"),
        "end_time": to_stop.get("arrival_time"),
        "start_day": from_stop.get("day"),
        "end_day": to_stop.get("day"),
        "duration_hours": duration_hours,
        "stop_count": stop_count,
        "is_destination": is_destination,
        "transfer_strength": transfer_strength,
    }

    leg["leg_score"] = calculate_leg_score(leg)

    return leg


def build_route(source, destination, legs):
    transfers = max(len(legs) - 1, 0)
    total_stops = sum(leg["stop_count"] for leg in legs)
    total_duration_hours = calculate_total_duration(legs)

    route_preview = [source]
    for leg in legs:
        route_preview.append(leg["to"])

    score = calculate_score(legs)

    return {
        "type": "multi_transfer",
        "source": source,
        "destination": destination,
        "transfers": transfers,
        "leg_count": len(legs),
        "total_stops": total_stops,
        "total_duration_hours": total_duration_hours,
        "score": score,
        "summary": build_summary(legs),
        "route_preview": route_preview,
        "train_legs": clean_legs(legs),
    }


def calculate_total_duration(legs):
    total = 0

    for leg in legs:
        duration = leg.get("duration_hours")
        if duration is not None:
            total += duration

    return round(total, 2)


def calculate_score(legs):
    transfers = max(len(legs) - 1, 0)
    total_stops = sum(leg["stop_count"] for leg in legs)
    total_duration = calculate_total_duration(legs)

    score = 1000

    score -= transfers * 250
    score -= int(total_stops * 0.6)

    if total_duration:
        score -= int(total_duration * 14)

    score += sum(train_quality_bonus(leg) for leg in legs)

    if transfers == 0:
        score += 120

    return max(score, 0)


def calculate_leg_score(leg):
    score = 500

    duration = leg.get("duration_hours")
    if duration:
        score -= int(duration * 10)

    score -= int(leg.get("stop_count", 0) * 0.5)
    score += train_quality_bonus(leg)

    if leg.get("is_destination"):
        score += 200

    return max(score, 0)


def train_quality_bonus(leg):
    name = str(leg.get("train_name") or "").upper()
    train_type = str(leg.get("train_type") or "").upper()
    text = name + " " + train_type

    bonus = 0

    if "VANDE" in text or "TEJAS" in text:
        bonus += 260

    if "RAJDHANI" in text:
        bonus += 250

    if "DURONTO" in text:
        bonus += 220

    if "SHATABDI" in text:
        bonus += 220

    if "GARIB RATH" in text:
        bonus += 120

    if "SUPERFAST" in text or " SF " in f" {text} ":
        bonus += 100

    if "EXPRESS" in text:
        bonus += 40

    if "PASSENGER" in text:
        bonus -= 80

    if "MEMU" in text or "DEMU" in text:
        bonus -= 60

    return bonus


def parse_day(day_value):
    try:
        if day_value is None:
            return 1
        return int(day_value)
    except Exception:
        return 1


def parse_time_to_hours(time_value):
    if not time_value or time_value == "None":
        return None

    try:
        parts = str(time_value).split(":")
        hour = int(parts[0])
        minute = int(parts[1])
        second = int(parts[2]) if len(parts) > 2 else 0
        return hour + minute / 60 + second / 3600
    except Exception:
        return None


def absolute_hours(time_value, day_value):
    time_hours = parse_time_to_hours(time_value)

    if time_hours is None:
        return None

    day = parse_day(day_value)
    return (day - 1) * 24 + time_hours


def duration_between(start_time, start_day, end_time, end_day):
    start = absolute_hours(start_time, start_day)
    end = absolute_hours(end_time, end_day)

    if start is None or end is None:
        return None

    duration = end - start

    while duration < 0:
        duration += 24

    return round(duration, 2)


def build_summary(legs):
    return " | ".join(
        f"{leg['from']} → {leg['to']} by {leg['train_no']}"
        for leg in legs
    )


def clean_legs(legs):
    cleaned = []

    for leg in legs:
        cleaned.append({
            "train_no": leg["train_no"],
            "train_name": leg["train_name"],
            "train_type": leg["train_type"],
            "from": leg["from"],
            "to": leg["to"],
            "start_time": leg["start_time"],
            "end_time": leg["end_time"],
            "start_day": leg["start_day"],
            "end_day": leg["end_day"],
            "duration_hours": leg["duration_hours"],
            "stop_count": leg["stop_count"],
            "quality_bonus": train_quality_bonus(leg),
        })

    return cleaned
