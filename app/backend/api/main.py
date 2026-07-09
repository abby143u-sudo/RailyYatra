from datetime import date
from collections import OrderedDict
from copy import deepcopy
from threading import Lock
from time import monotonic
from backend.api.data_quality_api import router as data_quality_router
from backend.api.legacy_search_fallback import router as legacy_search_fallback_router
from backend.api.live_status_api import router as live_status_router
from backend.api.cors_public_middleware import railyatra_cors_middleware
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
from fastapi import FastAPI, Query, HTTPException, Response
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
    import sqlite3
    from pathlib import Path

    app_root = Path(__file__).resolve().parents[2]
    cwd = Path.cwd()
    db_candidates = [
        app_root / "railyatra.db",
        app_root / "app" / "railyatra.db",
        cwd / "railyatra.db",
        cwd / "app" / "railyatra.db",
    ]

    table_sets = [
        ("staging", {"stations": "staging_stations", "trains": "staging_trains", "train_stops": "staging_train_stops"}),
        ("legacy", {"stations": "stations", "trains": "trains", "train_stops": "train_stops"}),
    ]

    checked = []

    for db_path in db_candidates:
        if not db_path.exists():
            checked.append({"path": str(db_path), "exists": False})
            continue

        for source, tables in table_sets:
            try:
                conn = sqlite3.connect(db_path)
                counts = {}
                for public_name, table_name in tables.items():
                    counts[public_name] = int(conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0])
                conn.close()
                if all(value >= 0 for value in counts.values()):
                    return {
                        "status": "healthy",
                        "source": source,
                        "database_path": str(db_path),
                        "counts": counts,
                    }
            except Exception as error:
                checked.append({
                    "path": str(db_path),
                    "exists": True,
                    "source": source,
                    "error": str(error),
                })
            finally:
                try:
                    conn.close()
                except Exception:
                    pass

    return {
        "status": "unhealthy",
        "reason": "No readable railway database tables found",
        "checked": checked,
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
            ts.stop_sequence,
            ts.arrival_time,
            ts.departure_time,
            ts.day
        FROM train_stops ts
        LEFT JOIN stations s ON ts.station_code = s.station_code
        WHERE ts.train_no = ?
        ORDER BY CAST(ts.stop_sequence AS INTEGER)
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
def search_v2(
    source: str,
    destination: str,
    direct_limit: int = 8,
    transfer_limit: int = 3,
    journey_date: date | None = None,
):
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
        journey_date=(
            journey_date.isoformat()
            if journey_date
            else None
        ),
    )

    return {
        "status": "ok",
        "endpoint": "/search-v2",
        "engine": result.get("engine"),
        "mode": result.get("mode"),
        "source": result.get("source"),
        "destination": result.get("destination"),
        "journey_date": result.get("journey_date"),
        "count": result.get("count"),
        "direct_count": result.get("direct_count"),
        "one_transfer_count": result.get("one_transfer_count"),
        "routes": result.get("routes", []),
        "compatibility_note": "search-v2 is powered by Phase 3 staging railway data; legacy /search is unchanged",
        "database_write_skipped": True,
        "production_railway_tables_modified": False,
    }
# --- Phase 3 production-candidate search API end ---

# --- Phase 4 recommendation-v2 API start ---
from backend.staging.recommendation_engine import (
    recommend_staging_routes as phase4_recommend_staging_routes,
)



_PHASE28_CACHE_TTL_SECONDS = 300
_PHASE28_CACHE_MAX_ENTRIES = 256

_phase28_recommend_cache = OrderedDict()
_phase28_recommend_cache_lock = Lock()
_phase28_recommend_cache_stats = {
    "hits": 0,
    "misses": 0,
    "expired": 0,
    "evictions": 0,
}


def _phase28_cache_get(key):
    with _phase28_recommend_cache_lock:
        cached_item = _phase28_recommend_cache.get(key)

        if cached_item is None:
            _phase28_recommend_cache_stats["misses"] += 1
            return None, None

        created_at, payload = cached_item
        age_seconds = monotonic() - created_at

        if age_seconds >= _PHASE28_CACHE_TTL_SECONDS:
            del _phase28_recommend_cache[key]
            _phase28_recommend_cache_stats["expired"] += 1
            _phase28_recommend_cache_stats["misses"] += 1
            return None, None

        _phase28_recommend_cache.move_to_end(key)
        _phase28_recommend_cache_stats["hits"] += 1

        return deepcopy(payload), age_seconds


def _phase28_cache_store(key, payload):
    with _phase28_recommend_cache_lock:
        _phase28_recommend_cache[key] = (
            monotonic(),
            deepcopy(payload),
        )
        _phase28_recommend_cache.move_to_end(key)

        while (
            len(_phase28_recommend_cache)
            > _PHASE28_CACHE_MAX_ENTRIES
        ):
            _phase28_recommend_cache.popitem(last=False)
            _phase28_recommend_cache_stats["evictions"] += 1


def _phase28_set_cache_headers(
    response: Response,
    status: str,
    age_seconds: float = 0,
):
    response.headers["X-Cache"] = status
    response.headers["X-Cache-Age"] = str(
        max(0, int(age_seconds))
    )
    response.headers["X-Cache-TTL"] = str(
        _PHASE28_CACHE_TTL_SECONDS
    )
    response.headers["Cache-Control"] = (
        "public, max-age=60, stale-while-revalidate=30"
    )


def _phase28_clear_recommend_cache():
    with _phase28_recommend_cache_lock:
        entry_count = len(_phase28_recommend_cache)
        _phase28_recommend_cache.clear()

        for key in _phase28_recommend_cache_stats:
            _phase28_recommend_cache_stats[key] = 0

        return entry_count


@app.get("/recommend-v2")
def recommend_v2(
    source: str,
    destination: str,
    response: Response,
    direct_limit: int = 8,
    transfer_limit: int = 2,
    journey_date: date | None = None,
):
    source_code = source.upper().strip()
    destination_code = destination.upper().strip()

    safe_direct_limit = max(1, min(direct_limit, 20))
    safe_transfer_limit = max(0, min(transfer_limit, 10))

    journey_date_value = (
        journey_date.isoformat()
        if journey_date
        else None
    )

    if not source_code or not destination_code:
        _phase28_set_cache_headers(
            response=response,
            status="BYPASS",
        )

        return {
            "status": "error",
            "message": "source and destination are required",
            "endpoint": "/recommend-v2",
            "engine": "phase_4_recommendation_engine",
            "source": source_code,
            "destination": destination_code,
            "count": 0,
            "recommendations": [],
            "database_write_skipped": True,
            "production_railway_tables_modified": False,
        }

    cache_key = (
        source_code,
        destination_code,
        safe_direct_limit,
        safe_transfer_limit,
        journey_date_value,
    )

    cached_result, cache_age = _phase28_cache_get(
        cache_key
    )

    if cached_result is not None:
        _phase28_set_cache_headers(
            response=response,
            status="HIT",
            age_seconds=cache_age or 0,
        )
        return cached_result

    result = phase4_recommend_staging_routes(
        source_station_code=source_code,
        destination_station_code=destination_code,
        direct_limit=safe_direct_limit,
        transfer_limit=safe_transfer_limit,
        journey_date=journey_date_value,
    )

    _phase28_cache_store(
        key=cache_key,
        payload=result,
    )

    _phase28_set_cache_headers(
        response=response,
        status="MISS",
    )

    return result


@app.get("/recommend-v2/cache-status")
def recommend_v2_cache_status():
    with _phase28_recommend_cache_lock:
        return {
            "status": "ok",
            "cache": "recommend-v2-memory-cache",
            "ttl_seconds": _PHASE28_CACHE_TTL_SECONDS,
            "maximum_entries": (
                _PHASE28_CACHE_MAX_ENTRIES
            ),
            "current_entries": len(
                _phase28_recommend_cache
            ),
            "statistics": dict(
                _phase28_recommend_cache_stats
            ),
            "scope": (
                "Current backend process only"
            ),
        }
# --- Phase 4 recommendation-v2 API end ---

# --- Phase 5 product status API start ---
from backend.product.status import get_product_status as phase5_get_product_status


@app.get("/product/status")
def product_status():
    return phase5_get_product_status()
# --- Phase 5 product status API end ---

# --- Phase 5 beta checklist API start ---
from backend.product.beta_checklist import get_beta_checklist as phase5_get_beta_checklist


@app.get("/product/beta-checklist")
def product_beta_checklist():
    return phase5_get_beta_checklist()
# --- Phase 5 beta checklist API end ---

# --- Phase 6 CORS configuration start ---
from backend.product.deployment import (
    get_allowed_origins as phase6_get_allowed_origins,
    get_deployment_status as phase6_get_deployment_status,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=phase6_get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/product/deployment-status")
def product_deployment_status():
    return phase6_get_deployment_status()
# --- Phase 6 CORS configuration end ---

from backend.api.feedback_api import router as feedback_router
app.include_router(feedback_router)

from backend.api.analytics_api import router as analytics_router
app.include_router(analytics_router)

from backend.api.admin_api import router as admin_router
app.include_router(admin_router)

from backend.api.security_middleware import register_security_middleware
register_security_middleware(app)

from backend.api.error_handlers import register_error_handlers
register_error_handlers(app)
app.middleware("http")(railyatra_cors_middleware)



# RailYatra hard CORS for Vercel frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://raily-yatra.vercel.app",
        "https://rail-yatra.vercel.app",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_origin_regex=r"https://.*\\.vercel\\.app",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(live_status_router)


# Replace unstable legacy /search and /recommend with safe fallback routes
app.router.routes = [
    route for route in app.router.routes
    if not (
        getattr(route, "path", "") in {"/search", "/recommend"}
        and "GET" in getattr(route, "methods", set())
    )
]
app.include_router(legacy_search_fallback_router)

app.include_router(data_quality_router)


# === Phase 18 Beta Feedback API ===
from datetime import datetime, timezone as _phase18_timezone
import os as _phase18_os

from fastapi import (
    HTTPException as _Phase18HTTPException,
    Request as _Phase18Request,
)
from pydantic import BaseModel as _Phase18BaseModel

from backend.api.beta_feedback_store import (
    count_beta_feedback_entries,
    delete_beta_feedback,
    beta_feedback_status_counts,
    beta_feedback_store_status,
    count_beta_feedback,
    list_beta_feedback_entries,
    save_beta_feedback,
    set_beta_feedback_status,
)


class _Phase18FeedbackPayload(_Phase18BaseModel):
    message: str
    page: str | None = None
    route: str | None = None
    severity: str | None = "normal"
    name: str | None = None
    contact: str | None = None


class _Phase19FeedbackStatusPayload(_Phase18BaseModel):
    status: str


def _phase18_extract_admin_token(request: _Phase18Request) -> str:
    provided_token = (
        request.headers.get("X-RailYatra-Admin-Token", "").strip()
        or request.headers.get("x-railyatra-admin-token", "").strip()
        or request.headers.get("x-admin-token", "").strip()
        or request.query_params.get("token", "").strip()
    )

    authorization = request.headers.get("authorization", "").strip()

    if not provided_token and authorization.lower().startswith("bearer "):
        provided_token = authorization.split(" ", 1)[1].strip()

    return provided_token


def _phase18_require_admin(request: _Phase18Request) -> None:
    expected_token = _phase18_os.getenv(
        "RAILYATRA_ADMIN_TOKEN",
        "",
    ).strip()

    provided_token = _phase18_extract_admin_token(request)

    if not expected_token:
        raise _Phase18HTTPException(
            status_code=500,
            detail="Admin token is not configured.",
        )

    if provided_token != expected_token:
        raise _Phase18HTTPException(
            status_code=401,
            detail="Admin token required.",
        )


@app.get("/beta/feedback/health")
def beta_feedback_health():
    store = beta_feedback_store_status()
    feedback_count = count_beta_feedback()

    return {
        "ok": True,
        "feature": "beta_feedback",
        "storage_mode": store["mode"],
        "database_url_configured": store["database_url_configured"],
        "database_path": (
            store["sqlite_path"]
            if store["mode"] == "sqlite"
            else None
        ),
        "feedback_count": feedback_count,
    }


@app.get("/admin/beta-feedback/summary")
def beta_feedback_summary(request: _Phase18Request):
    _phase18_require_admin(request)

    store = beta_feedback_store_status()
    counts = beta_feedback_status_counts()

    return {
        "ok": True,
        "storage_mode": store["mode"],
        "database_url_configured": store[
            "database_url_configured"
        ],
        "counts": counts,
    }


@app.post("/beta/feedback")
async def create_beta_feedback(
    payload: _Phase18FeedbackPayload,
    request: _Phase18Request,
):
    message = (payload.message or "").strip()

    if len(message) < 3:
        raise _Phase18HTTPException(
            status_code=400,
            detail="Feedback message is required.",
        )

    if len(message) > 2000:
        raise _Phase18HTTPException(
            status_code=400,
            detail="Feedback message is too long.",
        )

    feedback_id = save_beta_feedback(
        {
            "message": message,
            "page": payload.page,
            "route": payload.route,
            "severity": payload.severity or "normal",
            "name": payload.name,
            "contact": payload.contact,
            "user_agent": request.headers.get("user-agent", ""),
            "status": "new",
            "created_at": datetime.now(
                _phase18_timezone.utc
            ).isoformat(),
        }
    )

    return {
        "ok": True,
        "feedback_id": feedback_id,
        "message": (
            "Feedback received. "
            "Thank you for helping improve RailYatra."
        ),
    }


@app.get("/admin/beta-feedback")
def list_beta_feedback(
    request: _Phase18Request,
    page: int = 1,
    page_size: int = 25,
    status: str | None = None,
    q: str | None = None,
):
    _phase18_require_admin(request)

    safe_page = max(1, int(page or 1))
    safe_page_size = max(
        1,
        min(int(page_size or 25), 100),
    )

    normalized_status = (
        str(status or "").strip().lower()
    )

    if normalized_status in {"", "all"}:
        normalized_status = None
    elif normalized_status not in {
        "new",
        "reviewed",
        "resolved",
    }:
        raise _Phase18HTTPException(
            status_code=400,
            detail=(
                "Status filter must be one of: "
                "all, new, reviewed, resolved."
            ),
        )

    search_query = str(q or "").strip()

    if len(search_query) > 200:
        raise _Phase18HTTPException(
            status_code=400,
            detail="Search query is too long.",
        )

    total = count_beta_feedback_entries(
        status_filter=normalized_status,
        search_query=search_query,
    )

    total_pages = max(
        1,
        (total + safe_page_size - 1) // safe_page_size,
    )

    if safe_page > total_pages:
        safe_page = total_pages

    offset = (safe_page - 1) * safe_page_size

    feedback = list_beta_feedback_entries(
        limit=safe_page_size,
        offset=offset,
        status_filter=normalized_status,
        search_query=search_query,
    )

    return {
        "ok": True,
        "count": len(feedback),
        "total": total,
        "page": safe_page,
        "page_size": safe_page_size,
        "total_pages": total_pages,
        "has_previous": safe_page > 1,
        "has_next": safe_page < total_pages,
        "filters": {
            "status": normalized_status or "all",
            "q": search_query,
        },
        "feedback": feedback,
    }


@app.patch("/admin/beta-feedback/{feedback_id}/status")
def update_beta_feedback_status(
    feedback_id: int,
    payload: _Phase19FeedbackStatusPayload,
    request: _Phase18Request,
):
    _phase18_require_admin(request)

    status = (payload.status or "").strip().lower()
    allowed_statuses = {"new", "reviewed", "resolved"}

    if status not in allowed_statuses:
        raise _Phase18HTTPException(
            status_code=400,
            detail=(
                "Status must be one of: "
                "new, reviewed, resolved."
            ),
        )

    updated = set_beta_feedback_status(
        feedback_id=feedback_id,
        status=status,
    )

    if not updated:
        raise _Phase18HTTPException(
            status_code=404,
            detail="Feedback not found.",
        )

    return {
        "ok": True,
        "feedback_id": feedback_id,
        "status": status,
        "message": "Feedback status updated.",
    }

@app.delete("/admin/beta-feedback/{feedback_id}")
def remove_beta_feedback(
    feedback_id: int,
    request: _Phase18Request,
):
    _phase18_require_admin(request)

    deleted = delete_beta_feedback(feedback_id)

    if not deleted:
        raise _Phase18HTTPException(
            status_code=404,
            detail="Feedback not found.",
        )

    return {
        "ok": True,
        "feedback_id": feedback_id,
        "message": "Feedback deleted.",
    }

