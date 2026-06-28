from collections import defaultdict, deque
from backend.database.connection import fetch_all


_data_cache = None


def load_train_data():
    global _data_cache

    if _data_cache is not None:
        return _data_cache

    rows = fetch_all("""
        SELECT train_no, station_code, stop_order, arrival_time, departure_time, day
        FROM train_stops
        ORDER BY train_no, CAST(stop_order AS INTEGER)
    """)

    train_routes = defaultdict(list)

    for row in rows:
        train_routes[row["train_no"]].append({
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
    }

    return _data_cache


def find_multi_transfer_routes(source, destination, max_transfers=3, limit=10):
    source = source.upper().strip()
    destination = destination.upper().strip()

    data = load_train_data()
    train_routes = data["train_routes"]
    station_to_positions = data["station_to_positions"]
    station_train_count = data["station_train_count"]

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
    used_trains,
    visited_stations,
):
    positions = station_to_positions.get(current_station, [])
    options = []

    major_hubs = {
        "PNBE", "DNR", "ARA", "BXR", "MGS", "DDU", "BSB",
        "PRYJ", "CNB", "LKO", "GZB", "NDLS", "ANVT", "DLI"
    }

    for pos in positions[:80]:
        train_no = pos["train_no"]

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
            ))

    options.sort(
        key=lambda leg: (
            leg["is_destination"],
            leg["transfer_strength"],
            leg["stop_count"]
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
):
    return {
        "train_no": train_no,
        "from": from_station,
        "to": to_station,
        "start_time": from_stop.get("departure_time"),
        "end_time": to_stop.get("arrival_time"),
        "start_day": from_stop.get("day"),
        "end_day": to_stop.get("day"),
        "stop_count": stop_count,
        "is_destination": is_destination,
        "transfer_strength": transfer_strength,
    }


def build_route(source, destination, legs):
    transfers = max(len(legs) - 1, 0)
    total_stops = sum(leg["stop_count"] for leg in legs)

    route_preview = [source]
    for leg in legs:
        route_preview.append(leg["to"])

    return {
        "type": "multi_transfer",
        "source": source,
        "destination": destination,
        "transfers": transfers,
        "leg_count": len(legs),
        "total_stops": total_stops,
        "score": calculate_score(legs),
        "summary": build_summary(legs),
        "route_preview": route_preview,
        "train_legs": clean_legs(legs),
    }


def calculate_score(legs):
    transfers = max(len(legs) - 1, 0)
    total_stops = sum(leg["stop_count"] for leg in legs)

    score = 1200
    score -= transfers * 250
    score -= total_stops * 2

    if transfers == 0:
        score += 300

    return max(score, 0)


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
            "from": leg["from"],
            "to": leg["to"],
            "start_time": leg["start_time"],
            "end_time": leg["end_time"],
            "start_day": leg["start_day"],
            "end_day": leg["end_day"],
            "stop_count": leg["stop_count"],
        })

    return cleaned
