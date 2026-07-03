from backend.database.connection import fetch_all
from backend.scoring.journey_score import calculate_journey_score


def find_direct_trains(source, destination):
    rows = fetch_all(
        """
        SELECT
            a.train_no,
            t.train_name,
            a.departure_time,
            b.arrival_time,
            CAST(b.stop_sequence AS INTEGER) - CAST(a.stop_sequence AS INTEGER) AS stops
        FROM train_stops a
        JOIN train_stops b ON a.train_no = b.train_no
        LEFT JOIN trains t ON a.train_no = t.train_no
        WHERE a.station_code = ?
          AND b.station_code = ?
          AND CAST(a.stop_sequence AS INTEGER) < CAST(b.stop_sequence AS INTEGER)
          AND b.arrival_time IS NOT NULL
          AND b.arrival_time != 'None'
        """,
        (source, destination),
    )

    results = []

    for row in rows:
        train = {
            "train_no": row["train_no"],
            "train_name": row["train_name"] or "Unknown Train",
            "departure": row["departure_time"],
            "arrival": row["arrival_time"],
            "stops": int(row["stops"] or 0),
        }
        results.append(calculate_journey_score(train))

    results.sort(key=lambda x: x["journey_score"], reverse=True)
    return results
