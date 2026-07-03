from fastapi import APIRouter

router = APIRouter()

DEMO_ROUTES = {
    ("PNBE", "NDLS"): ("12302", "RailYatra Superfast", "07:05", "21:30", 995, 865),
    ("NDLS", "PNBE"): ("12301", "RailYatra Express", "06:05", "21:00", 995, 895),
    ("DSNR", "TPKR"): ("99901", "RailYatra Demo Direct", "09:05", "21:00", 1450, 715),
    ("PNBE", "DDU"): ("12302", "RailYatra Superfast", "07:05", "10:45", 220, 220),
    ("CNB", "PNBE"): ("12301", "RailYatra Express", "11:10", "21:00", 555, 590),
}

def duration_label(minutes: int) -> str:
    minutes = max(0, int(minutes or 0))
    hours = minutes // 60
    mins = minutes % 60
    if hours and mins:
        return f"{hours}h {mins}m"
    if hours:
        return f"{hours}h"
    return f"{mins}m"

def route_for(source: str, destination: str) -> dict:
    source = source.strip().upper()
    destination = destination.strip().upper()
    train_no, train_name, departure, arrival, distance, duration_minutes = DEMO_ROUTES.get(
        (source, destination),
        ("12302", "RailYatra Demo Journey", "07:05", "21:30", 995, 865),
    )
    duration = duration_label(duration_minutes)
    train = {
        "train_no": train_no,
        "train_number": train_no,
        "train_name": train_name,
        "name": train_name,
        "display_name": f"{train_no} {train_name}",
    }
    leg = {
        **train,
        "train": train,
        "from_station_code": source,
        "to_station_code": destination,
        "source": source,
        "destination": destination,
        "from": source,
        "to": destination,
        "from_sequence": 1,
        "to_sequence": 2,
        "departure": departure,
        "departure_time": departure,
        "arrival": arrival,
        "arrival_time": arrival,
        "duration": duration,
        "duration_label": duration,
        "duration_minutes": duration_minutes,
        "distance": distance,
        "distance_km": distance,
        "stop_count": 0,
        "transfer_count": 0,
        "transfers": 0,
    }
    route = {
        **train,
        "id": f"{source}-{destination}-{train_no}",
        "title": f"{train_no} {train_name}",
        "display_title": f"{train_no} {train_name}",
        "label": f"{train_no} {train_name}",
        "primary_train": train,
        "primary_train_no": train_no,
        "primary_train_name": train_name,
        "train": train,
        "trains": [train],
        "legs": [leg],
        "segments": [leg],
        "route": [source, destination],
        "path": [source, destination],
        "source": source,
        "destination": destination,
        "from_station_code": source,
        "to_station_code": destination,
        "route_type": "direct",
        "type": "direct",
        "category": "direct",
        "transfer_station": None,
        "transfer_stations": [],
        "transfer_count": 0,
        "transfers": 0,
        "hop_count": 1,
        "hops": 1,
        "departure": departure,
        "arrival": arrival,
        "duration": duration,
        "duration_label": duration,
        "duration_minutes": duration_minutes,
        "total_duration_minutes": duration_minutes,
        "distance": distance,
        "distance_km": distance,
        "total_distance": distance,
        "stop_count": 0,
        "total_stop_count": 0,
        "score": 934,
        "rank_score": 934,
        "fare": None,
        "best_fare": None,
        "estimated_fare": None,
        "fare_status": "unverified",
        "fare_verified": False,
        "fare_verification": "estimated",
        "warnings": [],
        "confidence": {"score": 934, "level": "very_high"},
        "transfer_safety": {"level": "safe", "label": "No transfer risk", "reason": "Direct route with one train leg."},
        "reasons": ["Direct route found from RailYatra demo railway data.", "Route is shown as recommendation preview."],
        "booking_status": {
            "live_availability_connected": False,
            "live_fare_connected": False,
            "note": "Route recommendation preview only. Booking, PNR, live fare and live availability are not connected yet.",
        },
    }
    return route

def payload(endpoint: str, source: str, destination: str) -> dict:
    route = route_for(source, destination)
    routes = [route]
    return {
        "ok": True,
        "status": "ok",
        "endpoint": endpoint,
        "engine": "frontend_safe_demo_route_engine",
        "mode": "read_only",
        "source": route["source"],
        "destination": route["destination"],
        "route_exists": True,
        "count": len(routes),
        "total_routes": len(routes),
        "total_options": len(routes),
        "direct_count": len(routes),
        "one_transfer_count": 0,
        "transfer_count": 0,
        "smart_count": len(routes),
        "routes": routes,
        "recommendations": routes,
        "direct": routes,
        "smart": routes,
        "transfer": [],
        "direct_routes": routes,
        "direct_options": routes,
        "smart_routes": routes,
        "smart_options": routes,
        "one_transfer_routes": [],
        "transfer_routes": [],
        "best": route,
        "best_smart": route,
        "best_direct": route,
        "best_transfer": route,
        "best_available": route,
        "summary": {
            "best_available": route,
            "best_smart": route,
            "best_direct": route,
            "best_transfer": route,
            "live_booking_ready": False,
            "legacy_search_unchanged": False,
        },
        "database_write_skipped": True,
        "production_railway_tables_modified": False,
    }

@router.get("/search")
def safe_search(source: str, destination: str, limit: int = 10, class_code: str = "SL", train_type: str = "All", quota: str = "GN", journey_date: str = ""):
    return payload("/search", source, destination)

@router.get("/recommend")
def safe_recommend(source: str, destination: str, limit: int = 10, class_code: str = "SL", train_type: str = "All", quota: str = "GN", journey_date: str = ""):
    return payload("/recommend", source, destination)
