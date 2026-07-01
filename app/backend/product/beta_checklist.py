from __future__ import annotations

from typing import Any


def get_beta_checklist() -> dict[str, Any]:
    ready_items = [
        {
            "key": "real_data_staging",
            "label": "Real railway staging data loaded",
            "status": "ready",
            "detail": "Stations, trains and train stops are available in read-only staging tables.",
        },
        {
            "key": "search_v2",
            "label": "Production-candidate search endpoint",
            "status": "ready",
            "detail": "/search-v2 can return real staging-data routes.",
        },
        {
            "key": "recommend_v2",
            "label": "Recommendation endpoint",
            "status": "ready",
            "detail": "/recommend-v2 can rank routes with confidence, reasons and transfer safety.",
        },
        {
            "key": "frontend_preview",
            "label": "Frontend real-data preview",
            "status": "ready",
            "detail": "Frontend has search-v2, recommend-v2, station suggestions and product status panels.",
        },
        {
            "key": "safety_gate",
            "label": "Safety checks",
            "status": "ready",
            "detail": "Combined checks and pre-import safety gate are available.",
        },
    ]

    blocked_items = [
        {
            "key": "live_availability",
            "label": "Live seat availability",
            "status": "blocked",
            "detail": "Official or partner API is not connected yet.",
        },
        {
            "key": "live_fare",
            "label": "Live fare",
            "status": "blocked",
            "detail": "Static route engine is ready, but live fare integration is not connected.",
        },
        {
            "key": "pnr",
            "label": "PNR status",
            "status": "blocked",
            "detail": "PNR lookup is not connected yet.",
        },
        {
            "key": "booking",
            "label": "Ticket booking",
            "status": "blocked",
            "detail": "Booking flow, payment and cancellation are not connected yet.",
        },
        {
            "key": "production_auth",
            "label": "Production auth and admin",
            "status": "pending",
            "detail": "User login, admin controls and audit policies are not production-ready yet.",
        },
    ]

    next_actions = [
        "Make recommend-v2 the main user-facing search experience.",
        "Add public-demo mode labels across the frontend.",
        "Add deployment configuration.",
        "Prepare environment variables and production settings.",
        "Add backend CORS configuration for deployed frontend domain.",
        "Add monitoring/logging before public beta.",
        "Do not claim booking, payment, PNR or live availability until official integration exists.",
    ]

    return {
        "status": "public_beta_preview_ready_not_live_booking_ready",
        "phase": "phase_5_public_beta_readiness",
        "ready_count": len(ready_items),
        "blocked_count": len(blocked_items),
        "ready_items": ready_items,
        "blocked_items": blocked_items,
        "next_actions": next_actions,
        "public_beta_decision": {
            "can_show_demo_to_users": True,
            "can_show_demo_to_investors": True,
            "can_call_it_live_booking_product": False,
            "can_take_ticket_payments": False,
            "recommended_label": "Real railway route recommendation preview",
        },
        "safety": {
            "legacy_search_unchanged": True,
            "database_write_skipped": True,
            "production_railway_tables_modified": False,
            "live_booking_claim_blocked": True,
        },
    }
