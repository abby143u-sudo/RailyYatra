from backend.database.connection import fetch_all
from backend.services.time_utils import is_valid_transfer, transfer_wait_hours


def find_one_transfer_routes(source, destination, limit=10):
    rows = fetch_all(
        """
        WITH source_trains AS (
            SELECT train_no, station_code, stop_order, departure_time
            FROM train_stops
            WHERE station_code = ?
        ),
        destination_trains AS (
            SELECT train_no, station_code, stop_order, arrival_time
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
            x.arrival_time AS transfer_arrival,
            y.departure_time AS transfer_departure,
            d.arrival_time AS destination_arrival,
            CAST(x.stop_order AS INTEGER) - CAST(s.stop_order AS INTEGER) AS first_leg_stops,
            CAST(d.stop_order AS INTEGER) - CAST(y.stop_order AS INTEGER) AS second_leg_stops
        FROM source_trains s
        JOIN train_stops x
            ON s.train_no = x.train_no
           AND CAST(x.stop_order AS INTEGER) > CAST(s.stop_order AS INTEGER)
        JOIN train_stops y
            ON x.station_code = y.station_code
        JOIN destination_trains d
            ON y.train_no = d.train_no
           AND CAST(d.stop_order AS INTEGER) > CAST(y.stop_order AS INTEGER)
        LEFT JOIN trains t1 ON s.train_no = t1.train_no
        LEFT JOIN trains t2 ON d.train_no = t2.train_no
        LEFT JOIN stations st ON x.station_code = st.station_code
        WHERE s.train_no != d.train_no
          AND x.station_code NOT IN (?, ?)
          AND d.arrival_time IS NOT NULL
          AND d.arrival_time != 'None'
        LIMIT ?
        """,
        (source, destination, source, destination, limit * 50),
    )

    routes = []

    for row in rows:
        first_leg_stops = int(row["first_leg_stops"] or 0)
        second_leg_stops = int(row["second_leg_stops"] or 0)

        if first_leg_stops < 5 or second_leg_stops < 5:
            continue

        if not is_valid_transfer(
            row["transfer_arrival"],
            row["transfer_departure"],
            min_wait_minutes=30,
            max_wait_hours=8,
        ):
            continue

        wait_hours = transfer_wait_hours(
            row["transfer_arrival"],
            row["transfer_departure"],
        )

        total_stops = first_leg_stops + second_leg_stops
        score = 800 - total_stops - int(wait_hours * 5)

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
            "transfer_wait_hours": wait_hours,
            "first_leg_stops": first_leg_stops,
            "second_leg_stops": second_leg_stops,
            "total_stops": total_stops,
            "score": score,
        })

    routes.sort(key=lambda x: x["score"], reverse=True)
    return routes[:limit]