from __future__ import annotations

from typing import Any


def get_beta_checklist() -> dict[str, Any]:
    ready_items = [
        {
            "key": "real_railway_data",
            "label": "Real railway data loaded",
            "status": "ready",
            "detail": (
                "8,990 stations, 5,208 trains and "
                "417,080 train stops are available."
            ),
        },
        {
            "key": "route_recommendation",
            "label": "Route recommendation engine",
            "status": "ready",
            "detail": (
                "Direct and one-transfer journeys can be "
                "searched and ranked."
            ),
        },
        {
            "key": "date_aware_timing",
            "label": "Date-aware journey estimates",
            "status": "ready",
            "detail": (
                "Journey dates, estimated arrival times "
                "and total durations are displayed."
            ),
        },
        {
            "key": "transfer_validation",
            "label": "Transfer validation",
            "status": "ready",
            "detail": (
                "Unsafe short transfers are rejected and "
                "long or unknown waits are penalised."
            ),
        },
        {
            "key": "deduplication",
            "label": "Duplicate route removal",
            "status": "ready",
            "detail": (
                "Equivalent routes and slip-train variants "
                "are collapsed."
            ),
        },
        {
            "key": "response_cache",
            "label": "Recommendation response cache",
            "status": "ready",
            "detail": (
                "Frequently repeated recommendation "
                "requests use a five-minute memory cache."
            ),
        },
        {
            "key": "frontend_resilience",
            "label": "Frontend resilience",
            "status": "ready",
            "detail": (
                "Loading states, timeout handling, retry "
                "and empty-result guidance are available."
            ),
        },
        {
            "key": "production_smoke",
            "label": "Production smoke testing",
            "status": "ready",
            "detail": (
                "The live frontend, backend, data layer, "
                "recommendations and cache are tested."
            ),
        },
        {
            "key": "scheduled_monitor",
            "label": "Scheduled production monitoring",
            "status": "ready",
            "detail": (
                "GitHub Actions checks production every "
                "six hours and records failures."
            ),
        },
    ]

    blocked_items = [
        {
            "key": "live_availability",
            "label": "Live seat availability",
            "status": "planned",
            "detail": (
                "Requires an official or authorised "
                "railway-data integration."
            ),
        },
        {
            "key": "live_fare",
            "label": "Live fare",
            "status": "planned",
            "detail": (
                "Current recommendations do not include "
                "real-time ticket prices."
            ),
        },
        {
            "key": "pnr",
            "label": "PNR status",
            "status": "planned",
            "detail": "PNR lookup is not connected.",
        },
        {
            "key": "booking",
            "label": "Ticket booking and cancellation",
            "status": "planned",
            "detail": (
                "Booking, payment, refund and cancellation "
                "flows are not connected."
            ),
        },
        {
            "key": "production_auth",
            "label": "User accounts and production auth",
            "status": "planned",
            "detail": (
                "Login, saved journeys, alerts and account "
                "security remain commercial-phase work."
            ),
        },
    ]

    return {
        "status": "public_beta_live_route_recommendation_only",
        "version": "0.9.0-beta",
        "phase": "phase_32_public_beta_launch",
        "ready_count": len(ready_items),
        "blocked_count": len(blocked_items),
        "ready_items": ready_items,
        "blocked_items": blocked_items,
        "next_actions": [
            "Collect and review public-beta feedback.",
            "Track production-monitor failures.",
            "Improve timetable and operating-day accuracy.",
            "Add accounts, saved searches and journey alerts.",
            "Pursue authorised live-data and booking partnerships.",
        ],
        "public_beta_decision": {
            "go_no_go": "GO",
            "can_launch_route_recommendation_public_beta": True,
            "can_show_demo_to_users": True,
            "can_show_demo_to_investors": True,
            "can_call_it_live_booking_product": False,
            "can_take_ticket_payments": False,
            "recommended_label": (
                "RailYatra Public Beta — Route Recommendations"
            ),
        },
        "disclaimer": (
            "RailYatra currently provides route discovery "
            "and estimated journey recommendations. It does "
            "not provide live availability, live fares, PNR "
            "or ticket booking."
        ),
        "safety": {
            "real_data_read_only": True,
            "unsafe_short_transfers_rejected": True,
            "duplicate_routes_removed": True,
            "live_booking_claim_blocked": True,
            "payments_blocked": True,
            "production_monitoring_active": True,
        },
    }
