from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import googlemaps
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GOOGLE_API_KEY = ""

class Destination(BaseModel):
    address: str
    time_window_start: int  # tempo em segundos do início do dia
    time_window_end: int    # tempo em segundos do início do dia

class RouteRequest(BaseModel):
    origin: str
    origin_end: Optional[str] = None
    destinations: List[Destination]

def create_distance_time_matrix(gmaps_client, addresses):
    """
    Utiliza a Google Distance Matrix API para obter as matrizes de distância e tempo entre todos os endereços.
    """
    result = gmaps_client.distance_matrix(origins=addresses, destinations=addresses, mode='driving')
    distance_matrix = []
    time_matrix = []
    for row in result['rows']:
        distance_row = []
        time_row = []
        for element in row['elements']:
            distance = element['distance']['value']
            time = element['duration']['value']
            distance_row.append(distance)
            time_row.append(time)
        distance_matrix.append(distance_row)
        time_matrix.append(time_row)
    return distance_matrix, time_matrix

def create_data_model(time_matrix, destinations, origin_time_window):
    """
    Cria o dicionário de dados necessário para o OR-Tools, incluindo a matriz de tempo e as janelas de tempo.
    """
    data = {}
    data['time_matrix'] = time_matrix
    data['time_windows'] = []
    data['time_windows'].append((origin_time_window[0], origin_time_window[1]))
    for dest in destinations:
        data['time_windows'].append((dest.time_window_start, dest.time_window_end))
    data['num_vehicles'] = 1
    data['depot'] = 0
    return data

def solve_vrptw(data):
    """
    Configura e resolve o problema VRPTW usando OR-Tools.
    """
    manager = pywrapcp.RoutingIndexManager(len(data['time_matrix']),
                                           data['num_vehicles'], data['depot'])
    routing = pywrapcp.RoutingModel(manager)

    def time_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['time_matrix'][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(time_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    time_dimension_name = 'Time'
    routing.AddDimension(
        transit_callback_index,
        30*60,           # tempo máximo de espera permitido (30 minutos)
        24*3600,         # limite superior para o tempo de serviço (24 horas)
        False,           # não forçar a cumulativa do início para zero
        time_dimension_name)
    time_dimension = routing.GetDimensionOrDie(time_dimension_name)

    for location_idx, time_window in enumerate(data['time_windows']):
        index = manager.NodeToIndex(location_idx)
        time_dimension.CumulVar(index).SetRange(time_window[0], time_window[1])

    for vehicle_id in range(data['num_vehicles']):
        start_index = routing.Start(vehicle_id)
        time_dimension.CumulVar(start_index).SetRange(data['time_windows'][0][0], data['time_windows'][0][1])
        end_index = routing.End(vehicle_id)
        time_dimension.CumulVar(end_index).SetRange(data['time_windows'][0][0], data['time_windows'][0][1])

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC

    solution = routing.SolveWithParameters(search_parameters)
    if solution:
        route = []
        index = routing.Start(0)
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            route.append(node_index)
            index = solution.Value(routing.NextVar(index))
        node_index = manager.IndexToNode(index)
        route.append(node_index)
        return route
    else:
        return None

@app.post("/optimize")
async def optimize_route(request: RouteRequest):
    """
    Endpoint para otimizar a rota.
    Recebe um ponto de origem e uma lista de destinos com janelas de tempo.
    """
    gmaps = googlemaps.Client(key=GOOGLE_API_KEY)
    addresses = [request.origin] + [dest.address for dest in request.destinations]

    _, time_matrix = create_distance_time_matrix(gmaps, addresses)

    origin_time_window = (0, 24*3600)

    data = create_data_model(time_matrix, request.destinations, origin_time_window)

    route_indices = solve_vrptw(data)
    if not route_indices:
        return {"error": "Nenhuma solução encontrada"}

    route_addresses = [addresses[i] for i in route_indices if i < len(addresses)]

    origin_address = route_addresses[0]
    destination_address = route_addresses[-1]
    waypoints = route_addresses[1:-1]
    waypoints_str = "|".join(waypoints)
    maps_url = (f"https://www.google.com/maps/dir/?api=1"
                f"&origin={origin_address}"
                f"&destination={destination_address}"
                f"&waypoints={waypoints_str}"
                f"&travelmode=driving")

    return {
        "optimized_route": route_addresses,
        "google_maps_url": maps_url
    }