from backend.database.connection import fetch_all


PRACTICAL_TRANSFER_HUBS = [
    "DNR", "ARA", "BXR", "MGS", "DDU", "BSB",
    "PRYJ", "ALD", "CNB", "LKO", "GZB",
    "DLI", "ANVT", "NDLS"
]


def find_one_transfer_routes(source, destination, limit=10):
    source = source.upper().strip()
    destination = destination.upper().strip()

    hubs = [
        hub for hub in PRACTICAL_TRANSFER_HUBS
        if hub not in {source, destination}
    ]

    placeholders = ",".join(["?"] * len(hubs))

    query = f"""
        WITH source_trains AS (
            SELECT train_no, station_code, stop_sequence, departure_time, day
            FROM train_stops
            WHERE station_code = ?
        ),
        destination_trains AS (
            SELECT train_no, station_code, stop_sequence, arrival_time, day
            FROM train_stops
            WHERE station_code = ?
        )
        SELECT
            s.train_no AS first_train,
            t1.train_name AS first_train_name,

            x.station_code AS transfer_station,
            st.station_name AS transfer_station_name,

            d.train_no AS second_train,
            t2.train_name AS second_train_name,

            s.departure_time AS source_departure,
            s.day AS source_day,

            x.arrival_time AS transfer_arrival,
            x.day AS transfer_arrival_day,

            y.departure_time AS transfer_departure,
            y.day AS transfer_departure_day,

            d.arrival_time AS destination_arrival,
            d.day AS destination_day,

            CAST(x.stop_sequence AS INTEGER) - CAST(s.stop_sequence AS INTEGER) AS first_leg_stops,
            CAST(d.stop_sequence AS INTEGER) - CAST(y.stop_sequence AS INTEGER) AS second_leg_stops
        FROM source_trains s
        JOIN train_stops x
            ON s.train_no = x.train_no
           AND CAST(x.stop_sequence AS INTEGER) > CAST(s.stop_sequence AS INTEGER)

        JOIN train_stops y
            ON x.station_code = y.station_code

        JOIN destination_trains d
            ON y.train_no = d.train_no
           AND CAST(d.stop_sequence AS INTEGER) > CAST(y.stop_sequence AS INTEGER)

        LEFT JOIN trains t1 ON s.train_no = t1.train_no
        LEFT JOIN trains t2 ON d.train_no = t2.train_no
        LEFT JOIN stations st ON x.station_code = st.station_code

        WHERE s.train_no != d.train_no
          AND x.station_code IN ({placeholders})
          AND s.departure_time IS NOT NULL
          AND x.arrival_time IS NOT NULL
          AND y.departure_time IS NOT NULL
          AND d.arrival_time IS NOT NULL
          AND s.departure_time != 'None'
          AND x.arrival_time != 'None'
          AND y.departure_time != 'None'
          AND d.arrival_time != 'None'
        LIMIT ?
    """

    params = [source, destination] + hubs + [limit * 100]

    rows = fetch_all(query, tuple(params))
    routes = []

    for row in rows:
        first_leg_stops = int(row["first_leg_stops"] or 0)
        second_leg_stops = int(row["second_leg_stops"] or 0)

        if first_leg_stops < 3 or second_leg_stops < 3:
            continue

        first_duration = duration_between(
            row["source_departure"],
            row["source_day"],
            row["transfer_arrival"],
            row["transfer_arrival_day"],
        )

        wait_hours = duration_between(
            row["transfer_arrival"],
            row["transfer_arrival_day"],
            row["transfer_departure"],
            row["transfer_departure_day"],
        )

        second_duration = duration_between(
            row["transfer_departure"],
            row["transfer_departure_day"],
            row["destination_arrival"],
            row["destination_day"],
        )

        if first_duration is None or wait_hours is None or second_duration is None:
            continue

        if wait_hours < 0.5 or wait_hours > 8:
            continue

        total_duration_hours = round(first_duration + wait_hours + second_duration, 2)
        total_stops = first_leg_stops + second_leg_stops

        if total_duration_hours < 5 or total_duration_hours > 72:
            continue

        score = calculate_transfer_score(
            transfer_station=row["transfer_station"],
            total_duration_hours=total_duration_hours,
            wait_hours=wait_hours,
            total_stops=total_stops,
        )

        routes.append({
            "type": "one_transfer",
            "source": source,
            "destination": destination,

            "first_train": row["first_train"],
            "first_train_name": row["first_train_name"],

            "transfer_station": row["transfer_station"],
            "transfer_station_name": row["transfer_station_name"],

            "second_train": row["second_train"],
            "second_train_name": row["second_train_name"],

            "source_departure": row["source_departure"],
            "transfer_arrival": row["transfer_arrival"],
            "transfer_departure": row["transfer_departure"],
            "destination_arrival": row["destination_arrival"],

            "transfer_wait_hours": round(wait_hours, 2),
            "first_leg_duration_hours": round(first_duration, 2),
            "second_leg_duration_hours": round(second_duration, 2),
            "total_duration_hours": total_duration_hours,

            "first_leg_stops": first_leg_stops,
            "second_leg_stops": second_leg_stops,
            "total_stops": total_stops,

            "score": score,
        })

    routes.sort(key=lambda x: x["score"], reverse=True)
    return routes[:limit]


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


def calculate_transfer_score(
    transfer_station,
    total_duration_hours,
    wait_hours,
    total_stops,
):
    score = 1000

    score -= int(total_duration_hours * 8)
    score -= int(wait_hours * 15)
    score -= int(total_stops * 0.7)

    premium_hubs = {"MGS", "DDU", "BSB", "PRYJ", "CNB", "GZB", "LKO"}

    if transfer_station in premium_hubs:
        score += 80

    return max(score, 0)
