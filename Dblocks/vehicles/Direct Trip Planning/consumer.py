from rpc_messaging import AsyncRPCServer

def handle_trip_request(request_data):
    vehicle_id = request_data.get("vehicle_id")
    action = request_data.get("action")
    if action == "get_status":
        # Fetch from DB or mock
        return {"vehicle_id": vehicle_id, "status": "ready"}
    return {"error": "unknown action"}

rpc_server = AsyncRPCServer(
    queue_name="vehicle_from_trip",
    exchange="trip_vehicle_comm",
    routing_key="trip.to.vehicle.*",
    handler=handle_trip_request
)

rpc_server.start()
