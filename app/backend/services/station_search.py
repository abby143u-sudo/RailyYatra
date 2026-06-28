from backend.database.connection import fetch_all


STATION_ALIASES = {
    "DELHI": ["NDLS", "DLI", "ANVT", "NZM", "DEE", "DSB", "DEC"],
    "NEW DELHI": ["NDLS", "DLI", "ANVT", "NZM"],
    "OLD DELHI": ["DLI", "NDLS"],
    "PATNA": ["PNBE", "PNC", "PPTA", "RJPB", "DNR"],
    "KANPUR": ["CNB", "GOY", "CPB"],
    "MUGHAL SARAI": ["MGS", "DDU"],
    "DDU": ["DDU", "MGS"],
    "VARANASI": ["BSB", "BCY"],
    "BANARAS": ["BSB", "BSBS"],
    "PRAYAGRAJ": ["PRYJ", "ALD"],
    "ALLAHABAD": ["PRYJ", "ALD"],
    "LUCKNOW": ["LKO", "LJN"],
    "HOWRAH": ["HWH", "KOAA", "SDAH"],
    "KOLKATA": ["HWH", "KOAA", "SDAH"],
    "MUMBAI": ["CSMT", "LTT", "BDTS", "BCT", "MMCT"],
}


def search_stations(query, limit=10):
    query = query.strip().upper()

    if not query:
        return []

    priority_codes = get_priority_codes(query)

    rows = fetch_candidate_stations(query, priority_codes, limit)

    rows.sort(
        key=lambda row: station_rank(row, query, priority_codes)
    )

    return [
        {
            "code": row["station_code"],
            "name": row["station_name"],
            "city": row.get("city"),
            "state": row.get("state"),
            "display": f"{row['station_code']} - {row['station_name']}",
        }
        for row in rows[:limit]
    ]


def get_priority_codes(query):
    codes = []

    for alias, station_codes in STATION_ALIASES.items():
        if query == alias or query in alias or alias in query:
            codes.extend(station_codes)

    seen = set()
    unique_codes = []

    for code in codes:
        if code not in seen:
            seen.add(code)
            unique_codes.append(code)

    return unique_codes


def fetch_candidate_stations(query, priority_codes, limit):
    params = [
        f"%{query}%",
        f"%{query}%",
    ]

    priority_filter = ""

    if priority_codes:
        placeholders = ",".join(["?"] * len(priority_codes))
        priority_filter = f" OR station_code IN ({placeholders})"
        params.extend(priority_codes)

    params.append(max(limit * 8, 40))

    sql = f"""
        SELECT station_code, station_name, city, state
        FROM stations
        WHERE UPPER(station_code) LIKE ?
           OR UPPER(station_name) LIKE ?
           {priority_filter}
        LIMIT ?
    """

    return fetch_all(sql, tuple(params))


def station_rank(row, query, priority_codes):
    code = str(row["station_code"] or "").upper()
    name = str(row["station_name"] or "").upper()

    if code == query:
        return (0, code)

    if code in priority_codes:
        return (1 + priority_codes.index(code) / 100, code)

    if name == query:
        return (2, code)

    if code.startswith(query):
        return (3, code)

    if name.startswith(query):
        return (4, code)

    if query in name:
        return (5, code)

    return (9, code)
