from backend.routing.direct import find_direct_trains
from backend.routing.transfer import find_one_transfer_routes


def get_smart_recommendations(source, destination, limit=10):
    source = source.upper().strip()
    destination = destination.upper().strip()

    direct_trains = find_direct_trains(source, destination)
    transfer_routes = find_one_transfer_routes(source, destination, limit)

    recommendations = []

    for train in direct_trains:
        recommendations.append({
            "type": "direct",
            "score": train["journey_score"] + 100,
            "label": "Best direct train",
            "data": train
        })

    for route in transfer_routes:
        recommendations.append({
            "type": "one_transfer",
            "score": route["score"],
            "label": "Backup transfer route",
            "data": route
        })

    recommendations.sort(key=lambda x: x["score"], reverse=True)

    return recommendations[:limit]
