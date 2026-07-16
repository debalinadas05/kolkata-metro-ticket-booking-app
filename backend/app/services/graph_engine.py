import heapq
from app.db.sqlite_client import get_sqlite_conn


def _load_graph():
    with get_sqlite_conn() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT id, name, line FROM stations")
        stations = {row["id"]: {"name": row["name"], "line": row["line"]} for row in cursor.fetchall()}

        cursor.execute("SELECT station_a_id, station_b_id, travel_time_minutes, fare_inr FROM connections")
        connections = cursor.fetchall()

        cursor.execute("SELECT station_from_id, station_to_id, transfer_time_minutes FROM interchanges")
        interchanges = cursor.fetchall()

    graph = {sid: [] for sid in stations}

    for row in connections:
        a, b, t, fare = row["station_a_id"], row["station_b_id"], row["travel_time_minutes"], row["fare_inr"]
        graph[a].append((b, t, fare, False))

    for row in interchanges:
        a, b, t = row["station_from_id"], row["station_to_id"], row["transfer_time_minutes"]
        graph[a].append((b, t, 0, True))

    return stations, graph


def _find_station_ids(stations, name):
    name_lower = name.strip().lower()
    matches = [sid for sid, info in stations.items() if info["name"].lower() == name_lower]
    if not matches:
        raise ValueError(f"Station not found: {name}")
    return matches


def get_metro_route(source_name: str, destination_name: str):
    stations, graph = _load_graph()

    source_ids = _find_station_ids(stations, source_name)
    dest_ids = set(_find_station_ids(stations, destination_name))

    # heap entries: (time_cost, node_id, path_ids, edge_is_interchange_flags, fare_cost)
    heap = [(0, sid, [sid], [], 0) for sid in source_ids]
    visited = set()

    while heap:
        time_cost, node, path_ids, edge_flags, fare_cost = heapq.heappop(heap)

        if node in visited:
            continue
        visited.add(node)

        if node in dest_ids:
            return _build_response(stations, path_ids, edge_flags, time_cost, fare_cost)

        for neighbor, edge_time, edge_fare, is_interchange in graph.get(node, []):
            if neighbor in visited:
                continue
            heapq.heappush(heap, (
                time_cost + edge_time,
                neighbor,
                path_ids + [neighbor],
                edge_flags + [is_interchange],
                fare_cost + edge_fare
            ))

    raise ValueError(f"No route found between {source_name} and {destination_name}")


def _build_response(stations, path_ids, edge_flags, total_time, total_fare):
    itinerary = []
    for i, sid in enumerate(path_ids):
        info = stations[sid]
        entry = {
            "station_name": info["name"],
            "line": info["line"],
            "is_interchange": False,
            "transfer_to": None
        }
        if i < len(edge_flags) and edge_flags[i]:
            entry["is_interchange"] = True
            entry["transfer_to"] = stations[path_ids[i + 1]]["line"]
        itinerary.append(entry)

    return {
        "route_summary": {
            "source": stations[path_ids[0]]["name"],
            "destination": stations[path_ids[-1]]["name"],
            "total_fare_inr": total_fare,
            "total_travel_time_minutes": total_time,
            "interchanges_count": sum(edge_flags)
        },
        "ordered_itinerary": itinerary
    }