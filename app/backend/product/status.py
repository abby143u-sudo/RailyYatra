from __future__ import annotations

from typing import Any


def get_product_status() -> dict[str, Any]:
    return {
        "status": "beta_foundation_ready",
        "product_name": "RailYatra",
        "phase": "phase_5_public_beta_readiness",
        "current_mode": "real_data_preview",
        "available_engines": {
            "legacy_search": {
                "endpoint": "/search",
                "status": "available",
                "purpose": "Original MVP/demo journey search.",
                "protected": True,
            },
            "search_v2": {
                "endpoint": "/search-v2",
                "status": "available",
                "purpose": "Production-candidate route search using staging railway data.",
                "protected": True,
            },
            "recommend_v2": {
                "endpoint": "/recommend-v2",
                "status": "available",
                "purpose": "Ranked route recommendations with confidence, transfer safety, and reasons.",
                "protected": True,
            },
            "staging_api": {
                "endpoint": "/staging/*",
                "status": "available",
                "purpose": "Read-only real railway data inspection and route helpers.",
                "protected": True,
            },
        },
        "data_layer": {
            "source": "staging railway data",
            "read_only": True,
            "stations": 8990,
            "trains": 5208,
            "train_stops": 417080,
        },
        "live_integrations": {
            "live_fare": False,
            "live_availability": False,
            "pnr": False,
            "booking": False,
            "payment": False,
            "cancellation": False,
        },
        "public_beta_flags": {
            "can_demo_real_routes": True,
            "can_rank_recommendations": True,
            "can_show_station_suggestions": True,
            "can_show_train_stop_drilldown": True,
            "can_claim_live_booking": False,
            "can_accept_payments": False,
        },
        "safety": {
            "legacy_search_unchanged": True,
            "database_write_skipped": True,
            "production_railway_tables_modified": False,
            "frontend_dist_committed": False,
        },
        "next_steps": [
            "Connect product status to frontend.",
            "Add user-facing mode labels for real-data preview.",
            "Prepare public beta readiness checklist.",
            "Add deployment configuration after local checks stay green.",
        ],
    }
