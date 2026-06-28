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
    source: str = Query(...),
    destination: str = Query(...),
    limit: int = Query(10),
):
    source = source.upper().strip()
    destination = destination.upper().strip()
    return plan_journey(source, destination, limit)


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
