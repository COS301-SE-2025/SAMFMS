import asyncio
from rpc_messaging import AsyncRPCClient

loop = asyncio.get_event_loop()
rpc_client = AsyncRPCClient(loop)
rpc_client.start()

async def request_vehicle_status(vehicle_id: str):
    message = {
        "action": "get_status",
        "vehicle_id": vehicle_id
    }
    future = rpc_client.send_request(
        exchange="trip_vehicle_comm",
        routing_key="trip.to.vehicle.status",
        message=message
    )
    try:
        response = await asyncio.wait_for(future, timeout=10)
        return response
    except asyncio.TimeoutError:
        return {"error": "Timeout waiting for vehicle DBlock response"}
