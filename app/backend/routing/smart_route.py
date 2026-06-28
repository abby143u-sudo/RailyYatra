from backend.services.train_day_service import build_running_day_info
from backend.services.fare_coverage_service import calculate_fare_coverage
from backend.routing.direct import find_direct_trains
from backend.routing.transfer import find_one_transfer_routes
from backend.routing.multi_transfer import find_multi_transfer_routes
from backend.graph.algorithms import has_route
from backend.services.fare_estimator import estimate_journey_fare
from backend.services.official_fare_service import enrich_fare_with_table
from backend.services.split_ticket_engine import build_split_ticket_plan


def plan_journey(source, destination, limit=10, journey_date=None, class_code='SL'):
    source = source.upper().strip()
    destination = destination.upper().strip()
    class_code = str(class_code or "SL").upper().strip()

    route_exists = has_route(source, destination)

    direct_routes = find_direct_trains(source, destination)
    transfer_routes = find_one_transfer_routes(source, destination, limit)
    multi_routes = find_multi_transfer_routes(
        source=source,
        destination=destination,
        max_transfers=3,
        limit=limit,
    )

    direct_recommendations = build_direct_recommendations(direct_routes)
    transfer_recommendations = build_transfer_recommendations(transfer_routes)
    multi_recommendations = build_multi_recommendations(multi_routes)

    direct_recommendations.sort(key=lambda x: x["score"], reverse=True)
    transfer_recommendations.sort(key=lambda x: x["score"], reverse=True)
    multi_recommendations.sort(key=lambda x: x["score"], reverse=True)

    used_smart_trains = get_train_numbers_from_multi(multi_recommendations)

    filtered_direct = [
        item for item in direct_recommendations
        if str(item["data"].get("train_no")) not in used_smart_trains
    ]

    if not filtered_direct:
        filtered_direct = direct_recommendations

    all_recommendations = (
        multi_recommendations +
        filtered_direct +
        transfer_recommendations
    )

    all_recommendations = [
        enrich_recommendation(item, source, destination, journey_date, class_code)
        for item in all_recommendations
    ]

    if journey_date:
        all_recommendations = [
            item for item in all_recommendations
            if not item.get("running_day")
            or item.get("running_day", {}).get("available", True)
        ]

    all_recommendations.sort(key=lambda x: x["score"], reverse=True)

    best = all_recommendations[0] if all_recommendations else None

    balanced_recommendations = []
    balanced_recommendations.extend(multi_recommendations[:4])
    balanced_recommendations.extend(filtered_direct[:3])
    balanced_recommendations.extend(transfer_recommendations[:3])

    balanced_recommendations = [
        enrich_recommendation(item, source, destination, journey_date, class_code)
        for item in balanced_recommendations
    ]

    balanced_recommendations = remove_duplicate_recommendations(
        balanced_recommendations
    )

    if journey_date:
        balanced_recommendations = [
            item for item in balanced_recommendations
            if not item.get("running_day")
            or item.get("running_day", {}).get("available", True)
        ]

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


def enrich_recommendation(item, source, destination, journey_date=None, class_code='SL'):
    item = dict(item)

    item["fare"] = estimate_journey_fare(
        item_type=item.get("type"),
        data=item.get("data", {}),
    )

    item["fare"] = enrich_fare_with_table(
        item_type=item.get("type"),
        data=item.get("data", {}),
        fare=item.get("fare", {}),
        source=source,
        destination=destination,
        class_code=class_code,
    )

    item["fare_coverage"] = calculate_fare_coverage(
        item_type=item.get("type"),
        data=item.get("data", {}),
        source=source,
        destination=destination,
        class_code=class_code,
    )

    item["running_day"] = build_running_day_info(
        item_type=item.get("type"),
        data=item.get("data", {}),
        journey_date=journey_date,
    )

    item["split_ticket"] = build_split_ticket_plan(
        item_type=item.get("type"),
        data=item.get("data", {}),
        fare=item.get("fare", {}),
        source=source,
        destination=destination,
    )

    return item


def build_direct_recommendations(direct_routes):
    recommendations = []

    for route in direct_routes:
        recommendations.append({
            "type": "direct",
            "score": route.get("journey_score", 0) + 100,
            "label": "Best direct train",
            "data": route
        })

    return recommendations


def build_transfer_recommendations(transfer_routes):
    recommendations = []

    for route in transfer_routes:
        recommendations.append({
            "type": "one_transfer",
            "score": route.get("score", 0),
            "label": "Backup transfer route",
            "data": route
        })

    return recommendations


def build_multi_recommendations(multi_routes):
    recommendations = []

    for route in multi_routes:
        label = (
            "Smart direct train"
            if route.get("transfers", 0) == 0
            else "Smart multi-transfer route"
        )

        recommendations.append({
            "type": "multi_transfer",
            "score": route.get("score", 0),
            "label": label,
            "data": route
        })

    return recommendations


def get_train_numbers_from_multi(multi_recommendations):
    train_numbers = set()

    for item in multi_recommendations:
        legs = item.get("data", {}).get("train_legs", [])

        for leg in legs:
            train_no = leg.get("train_no")
            if train_no:
                train_numbers.add(str(train_no))

    return train_numbers


def recommendation_key(item):
    item_type = item.get("type")
    data = item.get("data", {})

    if item_type == "direct":
        return ("direct", str(data.get("train_no")))

    if item_type == "multi_transfer":
        legs = data.get("train_legs", [])
        train_chain = tuple(str(leg.get("train_no")) for leg in legs)
        return ("multi_transfer", train_chain)

    if item_type == "one_transfer":
        return (
            "one_transfer",
            str(data.get("first_train")),
            str(data.get("transfer_station")),
            str(data.get("second_train")),
        )

    return (item_type, str(data))


def remove_duplicate_recommendations(recommendations):
    seen = set()
    unique = []

    for item in recommendations:
        key = recommendation_key(item)

        if key in seen:
            continue

        seen.add(key)
        unique.append(item)

    return unique
