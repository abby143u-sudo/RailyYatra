from __future__ import annotations

import os
from typing import Any


def get_product_status() -> dict[str, Any]:
    version = os.getenv(
        "RAILYATRA_RELEASE_VERSION",
        "0.9.0-beta",
    )

    frontend_url = os.getenv(
        "RAILYATRA_FRONTEND_URL",
        "https://raily-yatra.vercel.app",
    )

    backend_url = os.getenv(
        "RAILYATRA_BACKEND_URL",
        "https://railyyatra-backend.onrender.com",
    )

    build_commit = (
        os.getenv("RENDER_GIT_COMMIT")
        or os.getenv("RAILYATRA_BUILD_COMMIT")
        or "local"
    )

    return {
        "status": "public_beta_live",
        "product_name": "RailYatra",
        "version": version,
        "release_channel": "public_beta",
        "release_date": os.getenv(
            "RAILYATRA_RELEASE_DATE",
            "2026-07-10",
        ),
        "phase": "phase_32_public_beta_launch",
        "current_mode": (
            "real_route_recommendation_public_beta"
        ),
        "build": {
            "commit": build_commit,
            "environment": os.getenv(
                "RAILYATRA_ENV",
                "production",
            ),
        },
        "public_urls": {
            "frontend": frontend_url,
            "backend": backend_url,
            "api_documentation": f"{backend_url}/docs",
        },
        "launch_decision": {
            "decision": "GO",
            "scope": (
                "Public beta for railway route discovery "
                "and ranked journey recommendations"
            ),
            "live_booking_product": False,
        },
        "available_engines": {
            "legacy_search": {
                "endpoint": "/search",
                "status": "available",
                "purpose": "Original MVP journey search.",
                "protected": True,
            },
            "search_v2": {
                "endpoint": "/search-v2",
                "status": "available",
                "purpose": (
                    "Real-data direct and one-transfer "
                    "route discovery."
                ),
                "protected": True,
            },
            "recommend_v2": {
                "endpoint": "/recommend-v2",
                "status": "available",
                "purpose": (
                    "Date-aware ranked recommendations "
                    "with duration, transfer safety, "
                    "validation and deduplication."
                ),
                "protected": True,
            },
            "staging_api": {
                "endpoint": "/staging/*",
                "status": "available",
                "purpose": (
                    "Read-only railway data and train-stop "
                    "inspection APIs."
                ),
                "protected": True,
            },
        },
        "data_layer": {
            "source": "real railway staging data",
            "read_only": True,
            "stations": 8990,
            "trains": 5208,
            "train_stops": 417080,
        },
        "operations": {
            "production_smoke_tests": True,
            "scheduled_monitoring": True,
            "recommendation_cache": True,
            "frontend_timeout_and_retry": True,
            "transfer_validation": True,
            "duplicate_route_removal": True,
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
            "can_use_public_beta_label": True,
            "can_demo_real_routes": True,
            "can_rank_recommendations": True,
            "can_show_date_aware_estimates": True,
            "can_show_transfer_safety": True,
            "can_show_station_suggestions": True,
            "can_show_train_stop_drilldown": True,
            "can_claim_live_booking": False,
            "can_accept_payments": False,
        },
        "limitations": [
            (
                "Timetable dates and durations are estimates "
                "derived from available railway data."
            ),
            (
                "Train operating-day verification is not "
                "available for every train."
            ),
            "Live fares and seat availability are unavailable.",
            "PNR, booking, payment and cancellation are unavailable.",
        ],
        "safety": {
            "legacy_search_unchanged": True,
            "database_write_skipped": True,
            "railway_tables_read_only": True,
            "live_booking_claim_blocked": True,
            "payment_collection_blocked": True,
        },
        "next_steps": [
            "Collect public-beta feedback and error reports.",
            "Improve timetable and operating-day data accuracy.",
            "Add user accounts, saved journeys and alerts.",
            "Secure an authorised live railway-data partnership.",
            "Add booking only after compliance and partner approval.",
        ],
    }
