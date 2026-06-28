from fastapi import FastAPI, Query, HTTPException
from backend.routing.smart_route import plan_journey
from backend.routing.direct import find_direct_trains
from backend.routing.transfer import find_one_transfer_routes
from backend.database.connection import fetch_all, fetch_one

app = FastAPI(title="RailYatra v2 API", version="2.0.0")


@app.get("/")
def home():
    return {
        "message": "RailYatra v2 API running",
        "status": "ok",
        "version": "2.0.0"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "counts": {
            "trains": fetch_one("SELECT COUNT(*) AS count FROM trains")["count"],
            "stations": fetch_one("SELECT COUNT(*) AS count FROM stations")["count"],
            "train_stops": fetch_one("SELECT COUNT(*) AS count FROM train_stops")["count"],
        }
    }


@app.get("/search")
def search(
    source: str = Query(...),
    destination: str = Query(...),
    limit: int = Query(10)
):
    source = source.upper().strip()
    destination = destination.upper().strip()

    result = plan_journey(source, destination, limit)
    return result

    return {
        "source": source,
        "destination": destination,
        "count": len(results),
        "recommendations": results
    }


@app.get("/direct")
def direct(
    source: str = Query(...),
    destination: str = Query(...),
    limit: int = Query(10)
):
    source = source.upper().strip()
    destination = destination.upper().strip()

    results = find_direct_trains(source, destination)

    return {
        "source": source,
        "destination": destination,
        "count": len(results[:limit]),
        "trains": results[:limit]
    }


@app.get("/transfer")
def transfer(
    source: str = Query(...),
    destination: str = Query(...),
    limit: int = Query(10)
):
    source = source.upper().strip()
    destination = destination.upper().strip()

    routes = find_one_transfer_routes(source, destination, limit)

    return {
        "source": source,
        "destination": destination,
        "count": len(routes),
        "routes": routes
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
        (train_no,)
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
        (train_no,)
    )

    return {
        "train": train,
        "total_stops": len(route),
        "route": route
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
        (station_code,)
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
        (station_code,)
    )

    return {
        "station": station,
        "sample_train_count": len(trains),
        "trains": trains
    }
