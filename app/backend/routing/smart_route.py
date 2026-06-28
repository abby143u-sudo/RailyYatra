from backend.routing.direct import find_direct_trains
from backend.routing.transfer import find_one_transfer_routes
from backend.routing.multi_transfer import find_multi_transfer_routes
from backend.graph.algorithms import has_route


def plan_journey(source, destination, limit=10):
    source = source.upper().strip()
    destination = destination.upper().strip()

    route_exists = has_route(source, destination)

    direct_routes = find_direct_trains(source, destination)
    transfer_routes = find_one_transfer_routes(source, destination, limit)
    multi_routes = find_multi_transfer_routes(
        source=source,
        destination=destination,
        max_transfers=3,
        limit=limit,
    )

    direct_recommendations = []
    transfer_recommendations = []
    multi_recommendations = []

    for route in direct_routes:
        direct_recommendations.append({
            "type": "direct",
            "score": route.get("journey_score", 0) + 100,
            "label": "Best direct train",
            "data": route
        })

    for route in transfer_routes:
        transfer_recommendations.append({
            "type": "one_transfer",
            "score": route.get("score", 0),
            "label": "Backup transfer route",
            "data": route
        })

    for route in multi_routes:
        label = "Smart direct train" if route.get("transfers", 0) == 0 else "Smart multi-transfer route"

        multi_recommendations.append({
            "type": "multi_transfer",
            "score": route.get("score", 0),
            "label": label,
            "data": route
        })

    direct_recommendations.sort(key=lambda x: x["score"], reverse=True)
    transfer_recommendations.sort(key=lambda x: x["score"], reverse=True)
    multi_recommendations.sort(key=lambda x: x["score"], reverse=True)

    all_recommendations = (
        multi_recommendations +
        direct_recommendations +
        transfer_recommendations
    )

    all_recommendations.sort(key=lambda x: x["score"], reverse=True)

    best = all_recommendations[0] if all_recommendations else None

    balanced_recommendations = []
    balanced_recommendations.extend(multi_recommendations[:4])
    balanced_recommendations.extend(direct_recommendations[:3])
    balanced_recommendations.extend(transfer_recommendations[:3])

    balanced_recommendations.sort(key=lambda x: x["score"], reverse=True)

    return {
        "source": source,
        "destination": destination,
        "route_exists": route_exists,
        "direct_count": len(direct_routes),
        "transfer_count": len(transfer_routes),
        "multi_route_count": len(multi_routes),
        "total_recommendations": len(all_recommendations),
        "best": best,
        "recommendations": balanced_recommendations[:limit]
    }
