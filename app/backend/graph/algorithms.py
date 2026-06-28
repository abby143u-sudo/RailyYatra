import networkx as nx
from backend.graph.builder import get_graph


def shortest_path(source, destination):
    graph = get_graph()

    if source not in graph:
        return None

    if destination not in graph:
        return None

    try:
        return nx.shortest_path(graph, source, destination)
    except nx.NetworkXNoPath:
        return None


def shortest_hops(source, destination):
    path = shortest_path(source, destination)

    if not path:
        return None

    return len(path) - 1


def has_route(source, destination):
    return shortest_path(source, destination) is not None
