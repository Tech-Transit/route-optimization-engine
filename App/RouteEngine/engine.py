import networkx as nx
from geopy.distance import geodesic
import matplotlib.pyplot as plt
import pandas as pd
import geopy.geocoders


def find_optimal_routes(df_with_city, source, target, preferred_mode=None, k=10):
    """
    Find optimal routes between source and target with mode preference option.
    
    Parameters:
    - df_with_city: DataFrame with facility information
    - source: Source location name
    - target: Target location name
    - preferred_mode: Preferred transportation mode ('Airport', 'Seaport', 'Rail Terminal', or None)
    - k: Number of nearest neighbors to connect
    
    Returns:
    - G: NetworkX graph
    - paths: List of paths found
    - pos: Node positions for drawing
    - node_colors: Colors for each node
    - node_sizes: Sizes for each node
    """
    type_colors = {
        "Airport": "blue",
        "Seaport": "green",
        "Rail Terminal": "orange",
        "City": "red"
    }
    
    # Create a weighted directed graph
    G = nx.DiGraph()
    
    # Add nodes with positions and type
    node_colors = []
    node_sizes = []
    nodes_list = []
    
    for _, row in df_with_city.iterrows():
        G.add_node(row["Facility Name"], 
                  pos=(row["Latitude"], row["Longitude"]),
                  type=row["Type"],
                  country=row["Country"])
        
        if row["Type"] == "City":
            node_colors.append("red")
            node_sizes.append(150)
        else:
            node_colors.append(type_colors.get(row["Type"], "gray"))
            node_sizes.append(50)
        
        nodes_list.append(row["Facility Name"])
    
    # Build a spatial index
    node_locations = {node: data["pos"] for node, data in G.nodes(data=True)}
    
    # Mode preference weight factors
    mode_weight_factors = {
        None: {"Airport": 1.0, "Seaport": 1.0, "Rail Terminal": 1.0, "City": 1.0},
        "Airport": {"Airport": 0.5, "Seaport": 1.5, "Rail Terminal": 1.3, "City": 1.2},
        "Seaport": {"Airport": 1.5, "Seaport": 0.5, "Rail Terminal": 1.3, "City": 1.2},
        "Rail Terminal": {"Airport": 1.5, "Seaport": 1.3, "Rail Terminal": 0.5, "City": 1.2},
    }
    
    # Get the weight factors based on user preference
    weight_factors = mode_weight_factors.get(preferred_mode, mode_weight_factors[None])
    
    # For each node, find k nearest neighbors
    for i, node1 in enumerate(nodes_list):
        pos1 = node_locations[node1]
        country1 = G.nodes[node1]["country"]
        type1 = G.nodes[node1]["type"]
        
        # Calculate distances to all other nodes
        distances = []
        for node2 in nodes_list:
            if node1 != node2:
                pos2 = node_locations[node2]
                type2 = G.nodes[node2]["type"]
                
                # Base distance
                dist = geodesic(pos1, pos2).km
                
                # Apply mode preference - adjust weight based on node types
                # If the destination node is of preferred type, reduce the weight
                # If the origin node is of preferred type, also slightly reduce the weight
                weight_factor = weight_factors.get(type2, 1.0)
                
                # Store the original distance and adjusted weight
                adjusted_dist = dist * weight_factor
                distances.append((node2, adjusted_dist, dist))
        
        # Sort by adjusted distance and take k nearest
        distances.sort(key=lambda x: x[1])
        for node2, adjusted_dist, orig_dist in distances[:k]:
            country2 = G.nodes[node2]["country"]
            border_crossing = f"{country1} → {country2}"
            
            # Store both the adjusted weight (for pathfinding) and original distance (for display)
            G.add_edge(node1, node2, 
                      weight=round(adjusted_dist, 1), 
                      actual_distance=round(orig_dist, 1),
                      border=border_crossing)
    
    # Find multiple shortest paths
    try:
        # Get positions for plotting
        pos = {node: data["pos"] for node, data in G.nodes(data=True)}
        
        # Use Dijkstra to find shortest paths
        length, path = nx.single_source_dijkstra(G, source=source, target=target, weight='weight')
        
        # Optionally find alternative paths by temporarily removing edges from the shortest path
        paths = [path]
        temp_G = G.copy()
        
        # Find 2 more alternative paths by removing critical edges
        for i in range(2):
            # Remove a critical edge from the previous path
            if len(paths[-1]) >= 2:
                critical_edges = []
                for j in range(len(paths[-1])-1):
                    u, v = paths[-1][j], paths[-1][j+1]
                    if temp_G.has_edge(u, v):
                        critical_edges.append((u, v, temp_G[u][v]['weight'], 
                                              temp_G[u][v]['actual_distance'], 
                                              temp_G[u][v]['border']))
                        temp_G.remove_edge(u, v)
                
                # Try to find an alternative path
                try:
                    alt_length, alt_path = nx.single_source_dijkstra(temp_G, source=source, target=target, weight='weight')
                    paths.append(alt_path)
                except (nx.NetworkXNoPath, nx.NodeNotFound):
                    # Restore the edges we removed if no path is found
                    for u, v, w, d, b in critical_edges:
                        temp_G.add_edge(u, v, weight=w, actual_distance=d, border=b)
        
        return G, paths, pos, node_colors, node_sizes, nodes_list
    
    except nx.NetworkXNoPath:
        print(f"No path found between {source} and {target}.")
        return None, [], {}, [], [], []
    except nx.NodeNotFound as e:
        print(f"Node not found error: {e}")
        return None, [], {}, [], [], []

def visualize_routes(G, paths, pos, node_colors, node_sizes, nodes_list, source, target, preferred_mode=None):
    """
    Visualize the optimal routes
    """
    if not paths:
        return
    
    # Collect all edges from all paths
    all_edges = set()
    for path in paths:
        path_edges = list(zip(path, path[1:]))
        all_edges.update(path_edges)
    
    # Get edge weights and border crossings
    shortest_edge_labels = {(u, v): f"{G[u][v]['actual_distance']} km\n{G[u][v]['border']}" 
                          for u, v in all_edges if G.has_edge(u, v)}
    
    # Draw the graph
    plt.figure(figsize=(12, 8))
    
    # Draw only nodes that are in the paths or within 1 hop of the paths
    nodes_in_paths = set()
    for path in paths:
        nodes_in_paths.update(path)
    
    # Get the subgraph containing only relevant nodes
    relevant_nodes = list(nodes_in_paths)
    subgraph = G.subgraph(relevant_nodes)
    
    # Filter node colors and sizes for the subgraph
    sub_node_colors = [node_colors[nodes_list.index(node)] for node in subgraph.nodes()]
    sub_node_sizes = [node_sizes[nodes_list.index(node)] for node in subgraph.nodes()]
    
    # Draw the subgraph
    nx.draw(subgraph, {n: pos[n] for n in subgraph.nodes()}, 
            with_labels=True, node_size=sub_node_sizes, node_color=sub_node_colors, 
            edge_color="lightgray", font_size=8, font_weight="bold")

    # Draw the paths in different colors
    colors = ["red", "blue", "purple"]
    for i, path in enumerate(paths):
        edges = list(zip(path, path[1:]))
        nx.draw_networkx_edges(G, pos, edgelist=edges, edge_color=colors[i % len(colors)], width=3.5)
    
    # Draw edge labels
    nx.draw_networkx_edge_labels(G, pos, edge_labels=shortest_edge_labels, font_size=6, font_color="black", bbox=dict(facecolor="white", alpha=0.6))
    
    # Add legend
    legend_labels = {
        "blue": "Airport",
        "green": "Seaport",
        "orange": "Rail Terminal",
        "red": "City"
    }
    for color, label in legend_labels.items():
        plt.scatter([], [], color=color, label=label)
    
    # Add extra information to title if there's a mode preference
    title_suffix = f" (Preferred: {preferred_mode})" if preferred_mode else " (Multiple Paths)"
    plt.legend(loc="upper left", fontsize=8)
    plt.title(f"Optimal Routes from {source} to {target}{title_suffix}")
    plt.show()
    
    # Print important information
    for i, path in enumerate(paths):
        print(f"\nOptimal Route {i+1}:", " → ".join(path))
        print("Edge Details:")
        total_distance = 0
        unique_borders = set()
        node_types_count = {"Airport": 0, "Seaport": 0, "Rail Terminal": 0, "City": 0}
        
        for u, v in zip(path, path[1:]):
            if G.has_edge(u, v):  # Make sure the edge exists
                v_type = G.nodes[v]["type"]
                node_types_count[v_type] = node_types_count.get(v_type, 0) + 1
                
                print(f"{u} → {v} ({G.nodes[v]['type']}): {G[u][v]['actual_distance']} km, Border: {G[u][v]['border']}")
                total_distance += G[u][v]['actual_distance']
                unique_borders.add(G[u][v]['border'])
        
        print("Total Distance:", round(total_distance, 1), "km")
        print("Total Border Crossings:", len(unique_borders))
        print("Border Crossing Countries:", ", ".join(unique_borders))
        print("Transportation Mode Usage:")
        for mode, count in node_types_count.items():
            if count > 0:
                print(f"  - {mode}: {count} facilities")

def get_routes_info(G, paths, source, target):
    """
    Returns the optimal routes' information with cost and transit time estimation.
    """
    if not paths:
        return {"message": "No paths found."}

    # Cost assumptions
    cost_per_km = {"Airport": 5.0, "Seaport": 1.5, "Rail Terminal": 2.0, "City": 1.0}
    border_crossing_fee = 50  # USD per border crossing

    # Transit time assumptions
    speed_kmh = {"Airport": 800, "Seaport": 35, "Rail Terminal": 60, "City": 50}
    border_delay_hours = {"Airport": 3, "Seaport": 12, "Rail Terminal": 6, "City": 1}

    routes_info = []
    for i, path in enumerate(paths):
        route_data = {
            "route": " → ".join(path),
            "edge_details": [],
            "total_distance": 0,
            "total_cost": 0,
            "total_border_crossings": 0,
            "border_crossing_countries": [],
            "transportation_mode_usage": {"Airport": 0, "Seaport": 0, "Rail Terminal": 0, "City": 0},
            "total_transit_time_hours": 0  # Transit time storage
        }

        for u, v in zip(path, path[1:]):
            if G.has_edge(u, v):
                v_type = G.nodes[v]["type"]
                route_data["transportation_mode_usage"][v_type] += 1
                distance = G[u][v]["actual_distance"]

                # Cost calculation
                cost = distance * cost_per_km[v_type]
                route_data["total_cost"] += cost

                # Transit time calculation
                travel_time = distance / speed_kmh[v_type]  # Distance ÷ Speed
                route_data["total_transit_time_hours"] += travel_time

                route_data["edge_details"].append(
                    f"{u} → {v} ({v_type}): {distance} km, Cost: ${cost:.2f}, Time: {travel_time:.2f} hrs, Border: {G[u][v]['border']}"
                )

                route_data["total_distance"] += distance
                route_data["border_crossing_countries"].append(G[u][v]["border"])

        # Add border crossing cost and delays
        unique_borders = set(route_data["border_crossing_countries"])
        border_cost = len(unique_borders) * border_crossing_fee
        border_delay = sum(border_delay_hours.get(G.nodes[v]["type"], 0) for v in path if v in G.nodes)

        route_data["total_cost"] += border_cost
        route_data["total_transit_time_hours"] += border_delay  # Add delays

        route_data["total_cost"] = round(route_data["total_cost"], 2)
        route_data["total_transit_time_hours"] = round(route_data["total_transit_time_hours"], 1)
        route_data["total_distance"] = round(route_data["total_distance"], 1)
        route_data["total_border_crossings"] = len(unique_borders)
        route_data["border_crossing_countries"] = ", ".join(unique_borders)

        routes_info.append(route_data)

    return routes_info

def rank_routes(routes_info):
    """
    Ranks the routes based on total transit time and total cost.
    Returns a dictionary formatted for JSON response.
    """

    # Sorting based on transit time (ascending)
    ranked_by_time = sorted(routes_info, key=lambda x: x["total_transit_time_hours"])
    
    # Sorting based on total cost (ascending)
    ranked_by_cost = sorted(routes_info, key=lambda x: x["total_cost"])

    # Formatting results
    return {
        "ranked_by_time": [
            {
                "rank": i + 1,
                "route": route["route"],
                "total_transit_time_hours": route["total_transit_time_hours"],
                "total_cost": route["total_cost"]
            }
            for i, route in enumerate(ranked_by_time)
        ],
        "ranked_by_cost": [
            {
                "rank": i + 1,
                "route": route["route"],
                "total_cost": route["total_cost"],
                "total_transit_time_hours": route["total_transit_time_hours"]
            }
            for i, route in enumerate(ranked_by_cost)
        ]
    }



def get_route_cords(G, paths, source, target):
    if not paths:
        return {"message": "No paths found."}

    routes_info = []
    for i, path in enumerate(paths):
        # Get coordinates for each node in the path
        coordinates = []
        for node in path:
            # Extract coordinates from graph node attributes
            if 'pos' in G.nodes[node]:
                coords = G.nodes[node]['pos']
                coordinates.append({
                    'name': node,
                    'type': G.nodes[node]['type'],
                    'lat': coords[0],
                    'lng': coords[1]
                })
        
        route_data = {
            "route_id": i + 1,
            "coordinates": coordinates,
            "edge_details": [],
            "total_distance": 0,
            "total_border_crossings": 0,
            "border_crossing_countries": [],
            "transportation_mode_usage": {"Airport": 0, "Seaport": 0, "Rail Terminal": 0, "City": 0}
        }

        for u, v in zip(path, path[1:]):
            if G.has_edge(u, v):
                v_type = G.nodes[v]["type"]
                route_data["transportation_mode_usage"][v_type] += 1
                route_data["edge_details"].append({
                    "from": u,
                    "to": v,
                    "type": v_type,
                    "distance": G[u][v]['actual_distance'],
                    "border": G[u][v]['border']
                })
                route_data["total_distance"] += G[u][v]["actual_distance"]
                route_data["border_crossing_countries"].append(G[u][v]["border"])

        route_data["total_distance"] = round(route_data["total_distance"], 1)
        route_data["total_border_crossings"] = len(set(route_data["border_crossing_countries"]))
        route_data["border_crossing_countries"] = list(set(route_data["border_crossing_countries"]))

        routes_info.append(route_data)

    return routes_info

def get_lat_lon(location_name):
    geolocator = geopy.geocoders.Nominatim(user_agent="geo_locator")
    location = geolocator.geocode(location_name, exactly_one=True)
    if location:
        return location.latitude, location.longitude
    else:
        return "Location not found"

def get_optimal_routes(G, paths):
    """
    Returns a list of optimal routes with only the path and total distance.
    """
    if not paths:
        return {"message": "No paths found."}

    optimal_routes = []
    for path in paths:
        total_distance = sum(G[u][v]["actual_distance"] for u, v in zip(path, path[1:]))
        optimal_routes.append({"route": " → ".join(path), "total_distance": round(total_distance, 1)})

    return optimal_routes

def get_optimal_routes_with_coords(G, paths):
    """
    Returns a list of optimal routes with their coordinates instead of names.
    """
    if not paths:
        return {"message": "No paths found."}

    optimal_routes = []
    for path in paths:
        coordinates = [(G.nodes[node]["pos"][0], G.nodes[node]["pos"][1]) for node in path]
        total_distance = sum(G[u][v]["actual_distance"] for u, v in zip(path, path[1:]))
        optimal_routes.append({"coordinates": coordinates, "total_distance": round(total_distance, 1)})

    return optimal_routes


# Example usage:
def main(preferred_mode=None):
    # Define source and target nodes
    source = "Mundra Port"
    target = "Port of Piraeus"
    
    # Find optimal routes with mode preference
    G, paths, pos, node_colors, node_sizes, nodes_list = find_optimal_routes(
        df_with_city, source, target, preferred_mode=preferred_mode, k=10
    )
    
    # if G:
    #     # Visualize the routes
    #     visualize_routes(G, paths, pos, node_colors, node_sizes, nodes_list, source, target, preferred_mode)

if __name__ == "__main__":
    # Run with different mode preferences
    main()  # No preference
    # main("Airport")  # Prefer air routes
    # main("Seaport")  # Prefer sea routes
    # main("Rail Terminal")  # Prefer rail routes
