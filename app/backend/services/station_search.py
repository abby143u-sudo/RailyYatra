from backend.database.connection import fetch_all


def search_stations(query, limit=10):
    query = query.strip().upper()

    if not query:
        return []

    rows = fetch_all(
        """
        SELECT station_code, station_name, city, state
        FROM stations
        WHERE UPPER(station_code) LIKE ?
           OR UPPER(station_name) LIKE ?
        ORDER BY
            CASE
                WHEN UPPER(station_code) = ? THEN 0
                WHEN UPPER(station_code) LIKE ? THEN 1
                WHEN UPPER(station_name) LIKE ? THEN 2
                ELSE 3
            END,
            station_name
        LIMIT ?
        """,
        (
            f"%{query}%",
            f"%{query}%",
            query,
            f"{query}%",
            f"{query}%",
            limit,
        ),
    )

    return [
        {
            "code": row["station_code"],
            "name": row["station_name"],
            "city": row.get("city"),
            "state": row.get("state"),
            "display": f"{row['station_code']} - {row['station_name']}",
        }
        for row in rows
    ]