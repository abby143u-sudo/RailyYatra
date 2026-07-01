from backend.staging.route_engine import search_staging_routes as phase3_search_staging_routes
from backend.services.official_fare_service import upsert_official_fare
from backend.services.fare_source_adapter import (
    get_fare_sources,
    lookup_best_fare,
)
from backend.services.fare_csv_importer import import_fares_from_csv
from pathlib import Path
from backend.services.official_fare_service import (
    get_official_fare,
    ensure_official_fare_table,
    get_fare_stats,
    search_official_fares,
)
from fastapi import FastAPI, Query, HTTPException
from backend.routing.smart_route import plan_journey
from backend.routing.direct import find_direct_trains
from backend.routing.transfer import find_one_transfer_routes
from backend.database.connection import fetch_all, fetch_one
from backend.services.station_search import search_stations
from fastapi.middleware.cors import CORSMiddleware
from backend.routing.multi_transfer import find_multi_transfer_routes

def infer_train_type(train):
    train_name = str(train.get("train_name", "")).lower()
    train_no = str(train.get("train_no", ""))
    existing_type = str(train.get("train_type", "")).lower()

    if "rajdhani" in existing_type or "rajdhani" in train_name:
        return "Rajdhani"

    if "superfast" in existing_type or "superfast" in train_name:
        return "Superfast"

    if train_no.startswith("12") or train_no.startswith("22"):
        return "Superfast"

    if "express" in existing_type or "express" in train_name:
        return "Express"

    return "Express"


def get_route_data(item):
    """
    Handles both shapes:
    1. {"route": {"route": [...], "trains": [...]}}
    2. {"route": [...], "trains": [...]}
    """
    if isinstance(item, dict) and isinstance(item.get("route"), dict):
        return item["route"]

    return item


def enrich_route_with_train_types(route_data):
    if not isinstance(route_data, dict):
        return route_data

    trains = route_data.get("trains", [])

    for train in trains:
        if isinstance(train, dict):
            train["train_type"] = infer_train_type(train)

    return route_data


def matches_train_type_filter(item, train_type_filter):
    selected = str(train_type_filter).lower().strip()

    if selected == "all":
        return True

    route_data = get_route_data(item)

    if not isinstance(route_data, dict):
        return True

    trains = route_data.get("trains", [])
    stations = route_data.get("route", [])

    hops = route_data.get("hops")
    if hops is None:
        hops = max(len(stations) - 1, 0)

    if selected == "direct only":
        return hops == 1 or len(trains) == 1

    for train in trains:
        if not isinstance(train, dict):
            continue

        train_type = train.get("train_type", infer_train_type(train)).lower()

        if train_type == selected:
            return True

    return False


def apply_train_type_filter_to_list(items, train_type):
    filtered_items = []

    for item in items:
        route_data = get_route_data(item)
        enrich_route_with_train_types(route_data)

        if matches_train_type_filter(item, train_type):
            filtered_items.append(item)

    return filtered_items


def apply_train_type_filter_to_response(response, train_type):
    """
    plan_journey ka response dict bhi ho sakta hai.
    Isliye common keys: recommendations/routes/trains ko safely filter karta hai.
    """
    if isinstance(response, list):
        return apply_train_type_filter_to_list(response, train_type)

    if not isinstance(response, dict):
        return response

    response["selected_filter"] = train_type

    for key in ["recommendations", "routes", "trains"]:
        if key in response and isinstance(response[key], list):
            response[key] = apply_train_type_filter_to_list(response[key], train_type)
            response[f"{key}_count"] = len(response[key])

    if "count" in response:
        for key in ["recommendations", "routes", "trains"]:
            if key in response and isinstance(response[key], list):
                response["count"] = len(response[key])
                break

    return response

app = FastAPI(title="RailYatra v2 API", version="2.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "message": "RailYatra v2 API running",
        "status": "ok",
        "version": "2.1.0",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "counts": {
            "trains": fetch_one("SELECT COUNT(*) AS count FROM trains")["count"],
            "stations": fetch_one("SELECT COUNT(*) AS count FROM stations")["count"],
            "train_stops": fetch_one("SELECT COUNT(*) AS count FROM train_stops")["count"],
        },
    }


@app.get("/stations")
def stations(
    q: str = Query(..., description="Station code or station name"),
    limit: int = Query(10, description="Maximum station suggestions"),
):
    return {
        "query": q,
        "count": len(search_stations(q, limit)),
        "stations": search_stations(q, limit),
    }


@app.get("/search")
def search(
    source: str,
    destination: str,
    limit: int = 10,
    journey_date: str | None = None,
    date: str | None = None,
    class_code: str = "SL",
    train_type: str = "All",
    quota: str = "GN",
):
    result = plan_journey(
        source=source,
        destination=destination,
        limit=limit,
        journey_date=journey_date or date,
        class_code=class_code,
    )

    result = apply_train_type_filter_to_response(result, train_type)

    if isinstance(result, dict):
        result["selected_quota"] = quota.upper().strip()

    return result
    
@app.get("/direct")
def direct(
    source: str = Query(...),
    destination: str = Query(...),
    limit: int = Query(10),
):
    source = source.upper().strip()
    destination = destination.upper().strip()

    results = find_direct_trains(source, destination)

    return {
        "source": source,
        "destination": destination,
        "count": len(results[:limit]),
        "trains": results[:limit],
    }


@app.get("/transfer")
def transfer(
    source: str = Query(...),
    destination: str = Query(...),
    limit: int = Query(10),
):
    source = source.upper().strip()
    destination = destination.upper().strip()

    routes = find_one_transfer_routes(source, destination, limit)

    return {
        "source": source,
        "destination": destination,
        "count": len(routes),
        "routes": routes,
    }


@app.get("/train/{train_no}")
def train_detail(train_no: str):
    train_no = train_no.strip()

    train = fetch_one(
        """
        SELECT train_no, train_name, train_type, source_station, destination_station
        FROM trains
        WHERE train_no = ?
        """,
        (train_no,),
    )

    if not train:
        raise HTTPException(status_code=404, detail="Train not found")

    route = fetch_all(
        """
        SELECT
            ts.station_code,
            s.station_name,
            ts.stop_order,
            ts.arrival_time,
            ts.departure_time,
            ts.day
        FROM train_stops ts
        LEFT JOIN stations s ON ts.station_code = s.station_code
        WHERE ts.train_no = ?
        ORDER BY CAST(ts.stop_order AS INTEGER)
        """,
        (train_no,),
    )

    return {
        "train": train,
        "total_stops": len(route),
        "route": route,
    }


@app.get("/station/{station_code}")
def station_detail(station_code: str):
    station_code = station_code.upper().strip()

    station = fetch_one(
        """
        SELECT station_code, station_name, city, state, latitude, longitude
        FROM stations
        WHERE station_code = ?
        """,
        (station_code,),
    )

    if not station:
        raise HTTPException(status_code=404, detail="Station not found")

    trains = fetch_all(
        """
        SELECT
            ts.train_no,
            t.train_name,
            ts.arrival_time,
            ts.departure_time,
            ts.day
        FROM train_stops ts
        LEFT JOIN trains t ON ts.train_no = t.train_no
        WHERE ts.station_code = ?
        LIMIT 50
        """,
        (station_code,),
    )

    return {
        "station": station,
        "sample_train_count": len(trains),
        "trains": trains,
    }
@app.get("/multi-route")
def multi_route(
    source: str = Query(...),
    destination: str = Query(...),
    max_transfers: int = Query(3),
    limit: int = Query(10),
):
    source = source.upper().strip()
    destination = destination.upper().strip()

    routes = find_multi_transfer_routes(
        source=source,
        destination=destination,
        max_transfers=max_transfers,
        limit=limit,
    )

    return {
        "source": source,
        "destination": destination,
        "max_transfers": max_transfers,
        "count": len(routes),
        "routes": routes,
    }

ensure_official_fare_table()


@app.get("/fare")
def lookup_fare(train_no: str, source: str, destination: str, class_code: str = "SL"):
    fare = get_official_fare(
        train_no=train_no,
        source=source,
        destination=destination,
        class_code=class_code,
    )

    if not fare:
        return {
            "found": False,
            "train_no": train_no.upper(),
            "source": source.upper(),
            "destination": destination.upper(),
            "class_code": class_code.upper(),
            "message": "Fare not found in local fare table",
        }

    return {
        "found": True,
        "fare": fare,
    }


@app.get("/fares/stats")
def fare_stats():
    return get_fare_stats()


@app.get("/fares")
def list_fares(
    train_no: str | None = None,
    source: str | None = None,
    destination: str | None = None,
    class_code: str | None = None,
    limit: int = 50,
):
    rows = search_official_fares(
        train_no=train_no,
        source=source,
        destination=destination,
        class_code=class_code,
        limit=limit,
    )

    return {
        "count": len(rows),
        "fares": rows,
    }


DATA_RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"


@app.get("/fares/import/files")
def list_importable_fare_files():
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)

    files = [
        {
            "file": file.name,
            "path": f"data/raw/{file.name}",
        }
        for file in DATA_RAW_DIR.glob("*.csv")
    ]

    return {
        "count": len(files),
        "files": files,
    }


@app.post("/fares/import")
def import_fare_csv(csv_file: str = "fares_original_format.csv"):
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)

    safe_file_name = Path(csv_file).name
    file_path = DATA_RAW_DIR / safe_file_name

    if not file_path.exists():
        return {
            "success": False,
            "message": "CSV file not found in data/raw",
            "expected_location": f"data/raw/{safe_file_name}",
        }

    result = import_fares_from_csv(file_path)

    return {
        "success": True,
        "message": "Fare CSV import completed",
        "result": result,
        "stats": get_fare_stats(),
    }


@app.get("/fare/sources")
def fare_sources():
    return {
        "sources": get_fare_sources(),
    }


@app.get("/fare/lookup")
def fare_lookup(
    train_no: str,
    source: str,
    destination: str,
    class_code: str = "SL",
):
    return lookup_best_fare(
        train_no=train_no,
        source=source,
        destination=destination,
        class_code=class_code,
    )


@app.post("/fare/manual")
def add_manual_verified_fare(
    train_no: str,
    source: str,
    destination: str,
    fare: int,
    class_code: str = "SL",
    source_type: str = "manual_verified",
):
    if fare <= 0:
        return {
            "success": False,
            "message": "Fare must be greater than 0",
        }

    upsert_official_fare(
        train_no=train_no,
        source=source,
        destination=destination,
        class_code=class_code,
        fare=fare,
        source_type=source_type,
    )

    saved_fare = get_official_fare(
        train_no=train_no,
        source=source,
        destination=destination,
        class_code=class_code,
    )

    return {
        "success": True,
        "message": "Manual verified fare saved",
        "fare": saved_fare,
        "stats": get_fare_stats(),
    }

# --- Phase 3 staging read-only API start ---
from backend.staging.queries import (
    find_direct_trains as staging_find_direct_trains,
    find_station_by_code as staging_find_station_by_code,
    find_train_by_number as staging_find_train_by_number,
    get_staging_counts as staging_get_counts,
    get_train_stops as staging_get_train_stops,
    search_stations as staging_search_stations,
)


@app.get("/staging/health")
def staging_health():
    counts = staging_get_counts()

    ready = (
        counts.get("staging_stations", 0) >= 8000
        and counts.get("staging_trains", 0) >= 5000
        and counts.get("staging_train_stops", 0) >= 400000
    )

    return {
        "status": "ready" if ready else "not_ready",
        "mode": "read_only",
        "phase": "phase_3_staging_integration",
        "counts": counts,
        "database_write_skipped": True,
        "production_railway_tables_modified": False,
    }


@app.get("/staging/stations")
def staging_stations(q: str = "", limit: int = 10):
    query = q.strip()
    safe_limit = max(1, min(limit, 25))

    if not query:
        return {
            "mode": "staging_read_only",
            "query": query,
            "count": 0,
            "stations": [],
            "database_write_skipped": True,
            "production_railway_tables_modified": False,
        }

    stations = staging_search_stations(query=query, limit=safe_limit)

    return {
        "mode": "staging_read_only",
        "query": query.upper(),
        "count": len(stations),
        "stations": stations,
        "database_write_skipped": True,
        "production_railway_tables_modified": False,
    }


@app.get("/staging/trains/{train_number}/stops")
def staging_train_stops(train_number: str, limit: int = 200):
    safe_train_number = train_number.strip()
    safe_limit = max(1, min(limit, 500))

    train = staging_find_train_by_number(safe_train_number)
    stops = staging_get_train_stops(safe_train_number, limit=safe_limit)

    return {
        "mode": "staging_read_only",
        "train_number": safe_train_number,
        "train_found": train is not None,
        "train": train,
        "count": len(stops),
        "stops": stops,
        "database_write_skipped": True,
        "production_railway_tables_modified": False,
    }


@app.get("/staging/direct")
def staging_direct(source: str, destination: str, limit: int = 20):
    source_code = source.upper().strip()
    destination_code = destination.upper().strip()
    safe_limit = max(1, min(limit, 50))

    source_station = staging_find_station_by_code(source_code)
    destination_station = staging_find_station_by_code(destination_code)

    routes = staging_find_direct_trains(
        source_station_code=source_code,
        destination_station_code=destination_code,
        limit=safe_limit,
    )

    return {
        "mode": "staging_read_only",
        "source": source_code,
        "destination": destination_code,
        "source_station_found": source_station is not None,
        "destination_station_found": destination_station is not None,
        "count": len(routes),
        "routes": routes,
        "database_write_skipped": True,
        "production_railway_tables_modified": False,
    }
# --- Phase 3 staging read-only API end ---

# --- Phase 3 production-candidate search API start ---
try:
    phase3_search_staging_routes
except NameError:
    from backend.staging.route_engine import search_staging_routes as phase3_search_staging_routes


@app.get("/search-v2")
def search_v2(source: str, destination: str, direct_limit: int = 8, transfer_limit: int = 3):
    source_code = source.upper().strip()
    destination_code = destination.upper().strip()

    safe_direct_limit = max(1, min(direct_limit, 20))
    safe_transfer_limit = max(0, min(transfer_limit, 10))

    if not source_code or not destination_code:
        return {
            "status": "error",
            "message": "source and destination are required",
            "engine": "phase_3_staging_route_engine",
            "source": source_code,
            "destination": destination_code,
            "count": 0,
            "routes": [],
            "database_write_skipped": True,
            "production_railway_tables_modified": False,
        }

    result = phase3_search_staging_routes(
        source_station_code=source_code,
        destination_station_code=destination_code,
        direct_limit=safe_direct_limit,
        transfer_limit=safe_transfer_limit,
    )

    return {
        "status": "ok",
        "endpoint": "/search-v2",
        "engine": result.get("engine"),
        "mode": result.get("mode"),
        "source": result.get("source"),
        "destination": result.get("destination"),
        "count": result.get("count"),
        "direct_count": result.get("direct_count"),
        "one_transfer_count": result.get("one_transfer_count"),
        "routes": result.get("routes", []),
        "compatibility_note": "search-v2 is powered by Phase 3 staging railway data; legacy /search is unchanged",
        "database_write_skipped": True,
        "production_railway_tables_modified": False,
    }
# --- Phase 3 production-candidate search API end ---
