import asyncio
from rpc_messaging import AsyncRPCClient

loop = asyncio.get_event_loop()
rpc_client = AsyncRPCClient(loop)
rpc_client.start()

async def notify_trip_planner(vehicle_id: str, assignment_data: dict):
    message = {
        "action": "notify_assignment",
        "vehicle_id": vehicle_id,
        "assignment": assignment_data
    }

    future = rpc_client.send_request(
        exchange="trip_vehicle_comm",
        routing_key="vehicle.to.trip.assignment",
        message=message
    )

    try:
        response = await asyncio.wait_for(future, timeout=10)
        return response
    except asyncio.TimeoutError:
        return {"error": "Timeout waiting for Trip SBlock"}
