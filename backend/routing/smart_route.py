from backend.routing.direct import find_direct_trains
from backend.routing.transfer import find_one_transfer_routes
from backend.graph.algorithms import has_route


def plan_journey(source, destination, limit=10):
    source = source.upper().strip()
    destination = destination.upper().strip()

    route_exists = has_route(source, destination)

    direct_routes = find_direct_trains(source, destination)
    transfer_routes = find_one_transfer_routes(source, destination, limit)

    recommendations = []

    for route in direct_routes:
        recommendations.append({
            "type": "direct",
            "score": route["journey_score"] + 100,
            "label": "Best direct train",
            "data": route
        })

    for route in transfer_routes:
        recommendations.append({
            "type": "one_transfer",
            "score": route["score"],
            "label": "Backup transfer route",
            "data": route
        })

    recommendations.sort(key=lambda x: x["score"], reverse=True)

    best = recommendations[0] if recommendations else None

    return {
        "source": source,
        "destination": destination,
        "route_exists": route_exists,
        "direct_count": len(direct_routes),
        "transfer_count": len(transfer_routes),
        "best": best,
        "recommendations": recommendations[:limit]
    }