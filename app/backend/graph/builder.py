import networkx as nx
from backend.database.connection import fetch_all


_graph_cache = None


def build_graph():
    rows = fetch_all("""
        SELECT train_no, station_code, stop_order, arrival_time, departure_time
        FROM train_stops
        ORDER BY train_no, CAST(stop_order AS INTEGER)
    """)

    graph = nx.DiGraph()
    current_train = None
    previous_stop = None

    for row in rows:
        train_no = row["train_no"]
        station_code = row["station_code"]

        if train_no != current_train:
            current_train = train_no
            previous_stop = None

        graph.add_node(station_code)

        if previous_stop:
            graph.add_edge(
                previous_stop["station_code"],
                station_code,
                train_no=train_no,
                departure_time=previous_stop["departure_time"],
                arrival_time=row["arrival_time"],
            )

        previous_stop = row

    return graph


def get_graph():
    global _graph_cache

    if _graph_cache is None:
        _graph_cache = build_graph()

    return _graph_cache
