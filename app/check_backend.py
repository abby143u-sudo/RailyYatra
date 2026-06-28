from backend.database.connection import fetch_one
from backend.routing.direct import find_direct_trains
from backend.routing.transfer import find_one_transfer_routes
from backend.routing.smart_route import plan_journey
from backend.graph.builder import get_graph
from backend.graph.algorithms import shortest_path


def check_database():
    print("\n✅ Checking database...")

    trains = fetch_one("SELECT COUNT(*) AS count FROM trains")["count"]
    stations = fetch_one("SELECT COUNT(*) AS count FROM stations")["count"]
    stops = fetch_one("SELECT COUNT(*) AS count FROM train_stops")["count"]

    print("Trains:", trains)
    print("Stations:", stations)
    print("Train stops:", stops)


def check_graph():
    print("\n✅ Checking graph...")

    graph = get_graph()

    print("Graph nodes:", graph.number_of_nodes())
    print("Graph edges:", graph.number_of_edges())

    route = shortest_path("NDLS", "PNBE")
    print("NDLS → PNBE route exists:", route is not None)


def check_direct_routes():
    print("\n✅ Checking direct routes...")

    results = find_direct_trains("NDLS", "PNBE")

    print("Direct trains found:", len(results))

    if results:
        print("Best direct train:", results[0])


def check_transfer_routes():
    print("\n✅ Checking transfer routes...")

    results = find_one_transfer_routes("NDLS", "PNBE", 5)

    print("Transfer routes found:", len(results))

    if results:
        print("Best transfer route:", results[0])


def check_smart_router():
    print("\n✅ Checking smart router...")

    result = plan_journey("NDLS", "PNBE", 5)

    print("Route exists:", result["route_exists"])
    print("Direct count:", result["direct_count"])
    print("Transfer count:", result["transfer_count"])
    print("Best recommendation:", result["best"])


if __name__ == "__main__":
    print("🚆 RailYatra Backend Check Started")

    check_database()
    check_graph()
    check_direct_routes()
    check_transfer_routes()
    check_smart_router()

    print("\n🎉 RailYatra backend check completed")
