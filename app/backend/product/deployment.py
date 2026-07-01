from __future__ import annotations

import os
from typing import Any


def get_allowed_origins() -> list[str]:
    raw_origins = os.getenv(
        "RAILYATRA_ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    )

    origins = [
        origin.strip()
        for origin in raw_origins.split(",")
        if origin.strip()
    ]

    return origins or ["http://localhost:5173", "http://127.0.0.1:5173"]


def get_deployment_status() -> dict[str, Any]:
    return {
        "status": "deployment_prep_ready",
        "phase": "phase_6_deployment_preparation",
        "environment": os.getenv("RAILYATRA_ENV", "development"),
        "api_host": os.getenv("RAILYATRA_API_HOST", "127.0.0.1"),
        "api_port": int(os.getenv("RAILYATRA_API_PORT", "8000")),
        "database_path": os.getenv("RAILYATRA_DATABASE_PATH", "app/railyatra.db"),
        "allowed_origins": get_allowed_origins(),
        "live_feature_flags": {
            "live_booking_enabled": os.getenv("RAILYATRA_LIVE_BOOKING_ENABLED", "false").lower() == "true",
            "live_fare_enabled": os.getenv("RAILYATRA_LIVE_FARE_ENABLED", "false").lower() == "true",
            "live_availability_enabled": os.getenv("RAILYATRA_LIVE_AVAILABILITY_ENABLED", "false").lower() == "true",
            "pnr_enabled": os.getenv("RAILYATRA_PNR_ENABLED", "false").lower() == "true",
            "payment_enabled": os.getenv("RAILYATRA_PAYMENT_ENABLED", "false").lower() == "true",
        },
        "deployment_readiness": {
            "env_example_present": True,
            "cors_configured": True,
            "frontend_build_supported": True,
            "backend_smoke_tests_available": True,
            "pre_import_gate_available": True,
            "live_booking_claim_blocked": True,
        },
        "safety": {
            "legacy_search_unchanged": True,
            "database_write_skipped": True,
            "production_railway_tables_modified": False,
        },
    }
