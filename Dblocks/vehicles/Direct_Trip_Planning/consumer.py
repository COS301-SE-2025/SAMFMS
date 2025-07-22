import asyncio
from rpc_messaging import AsyncRPCServer
from ..database import get_db
import logging

logger = logging.getLogger(__name__)

db = get_db()

async def handle_trip_request_async(request_data):
    try:
        action = request_data.get("action")

        if action == "get_active_trips":
            # Query the active trips from MongoDB
            active_trips_cursor = db["vehicle_trips"].find({"status": {"$in": ["planned", "in_progress"]}})
            active_trips = await active_trips_cursor.to_list(length=None)
            
            # Convert ObjectIds and datetime to JSON-safe format
            for trip in active_trips:
                trip["_id"] = str(trip["_id"])
                if "start_time" in trip:
                    trip["start_time"] = trip["start_time"].isoformat()
                if "end_time" in trip:
                    trip["end_time"] = trip["end_time"].isoformat()
            
            return {"trips": active_trips, "count": len(active_trips)}

        return {"error": f"Unknown action '{action}'"}
    
    except Exception as e:
        logger.error(f"Error handling trip request: {e}")
        return {"error": str(e)}

# Wrap it so AsyncRPCServer gets a sync-looking function
def handler_wrapper(request_data):
    return asyncio.get_event_loop().run_until_complete(handle_trip_request_async(request_data))

rpc_server = AsyncRPCServer(
    queue_name="vehicle_from_trip",
    exchange="trip_vehicle_comm",
    routing_key="trip.to.vehicle.*",
    handler=handler_wrapper
)

rpc_server.start()
