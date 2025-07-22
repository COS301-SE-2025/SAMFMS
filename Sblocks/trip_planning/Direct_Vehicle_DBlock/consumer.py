from rpc_messaging import AsyncRPCServer

def handle_vehicle_response(request_data):
    action = request_data.get("action")
    vehicle_id = request_data.get("vehicle_id")

    if action == "notify_assignment":
        # You can store, log, or trigger trip adjustments here
        return {"message": f"Received assignment for vehicle {vehicle_id}"}

    return {"error": "Unknown action from vehicle"}

rpc_server = AsyncRPCServer(
    queue_name="trip_from_vehicle",
    exchange="trip_vehicle_comm",
    routing_key="vehicle.to.trip.*",
    handler=handle_vehicle_response
)

rpc_server.start()
