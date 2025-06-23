from fastapi import FastAPI,Body,WebSocket
from fastapi.websockets import WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import uvicorn
import asyncio
import aio_pika
import uuid
import json
from contextlib import asynccontextmanager


from database import db
from logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

from rabbitmq.consumer import consume_messages,consume_single_message, consume_messages_Direct
from rabbitmq.admin import create_exchange
from rabbitmq.producer import publish_message
from services.request_router import request_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown events."""
    logger.info("Core service starting up...")
    
    try:
        client = AsyncIOMotorClient("mongodb://host.docker.internal:27017")
        await client.admin.command('ping')
        logger.info("Successfully connected to MongoDB")
        client.close()
    except Exception as e:        logger.error(f"Failed to connect to MongoDB: {e}")
    
    # Initialize plugin manager
    try:
        from services.plugin_service import plugin_manager
        await plugin_manager.initialize_plugins()
        logger.info("Plugin manager initialized")
    except Exception as e:
        logger.error(f"Failed to initialize plugin manager: {e}")

    consumer_task = asyncio.create_task(consume_messages("service_status"))
    # herrie consumer for core
    asyncio.create_task(consume_messages_Direct("core_responses","core_responses", on_response))
    await create_exchange("general", aio_pika.ExchangeType.FANOUT)
    await publish_message("general", aio_pika.ExchangeType.FANOUT, {"message": "Core service started"})

    # Initialize request router
    try:
        await request_router.initialize()
        logger.info("Request router initialized")
    except Exception as e:
        logger.error(f"Failed to initialize request router: {e}")

    logger.info("Started consuming messages from service_status queue")
    
    logger.info("Core service startup completed")
    
    yield

    logger.info("Core service shutting down...")
    for task in [consumer_task]:
        if not task.done():
            task.cancel()
    logger.info("Core service shutdown completed")

app = FastAPI(
    title="SAMFMS Core Service",
    description="Central API gateway for South African Fleet Management System",
    version="1.0.0",
    lifespan=lifespan
)

origins = [
    "http://localhost:3000",     # React development server
    "http://127.0.0.1:3000",
    "http://localhost:5000",     # Production build if served differently
    "*",                        # Optional: Allow all origins (less secure)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],        # Allow all methods including OPTIONS
    allow_headers=["*"],        # Allow all headers
)

# Import and include routers
from routes.auth import router as auth_router
from routes.plugins import router as plugins_router
from routes.service_proxy import router as service_proxy_router

app.include_router(auth_router)
app.include_router(plugins_router, prefix="/api")
app.include_router(service_proxy_router)


# Add a route for health checks (needed by Security middleware)
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}

# Herre code for websocket between Frontend and Core to retrieve live locations of vehicles
pending_futures = {}

# This function receives vehicle locations
async def on_response(message):
    try:
        logger.info(f"Message received from GPS: {message}")
        body = message.body.decode()
        data = json.loads(body)
        logger.info(f"Data from message: {data}")
        
        correlation_id = data.get("correlation_id")
        if correlation_id and correlation_id in pending_futures:
            future = pending_futures[correlation_id]
            if not future.done():
                vehicles = data.get("vehicles", [])
                future.set_result(vehicles)
            del pending_futures[correlation_id]
        else:
            logger.warning(f"No pending future found for correlation_id: {correlation_id}")
            
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON message: {e}")
    except Exception as e:
        logger.error(f"Error processing GPS response: {e}")


@app.websocket("/ws/vehicles")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connection established")
    
    try:
        while True:
            try:
                # Get live vehicle data
                vehicles = await get_live_vehicle_data()
                logger.info(f"Sending to frontend: {vehicles}")
                
                # Send data to frontend
                await websocket.send_json({"vehicles": vehicles})
                
                # Wait before next update - this is your main update interval
                await asyncio.sleep(2)
                
            except WebSocketDisconnect:
                logger.info("WebSocket disconnected by client")
                break
            except Exception as e:
                logger.error(f"Error in WebSocket loop: {e}")
                try:
                    await websocket.send_json({"error": str(e)})
                except Exception as send_error:
                    logger.error(f"Failed to send error message: {send_error}")
                    break
                # Wait a bit before retrying to avoid rapid error loops
                await asyncio.sleep(1)
                
    except Exception as e:
        logger.error(f"WebSocket endpoint error: {e}")
    finally:
        logger.info("WebSocket connection closed")

# endpoint to test get_live_vehicle_data
@app.get("/test/live_vehicles")
async def test_live_vehicles():
    """
    Test endpoint to fetch live vehicle data using get_live_vehicle_data().
    """
    vehicles = await get_live_vehicle_data()
    return {"vehicles": vehicles}

# This function will send messages on the message queue to show that it wants the live locations from gps
async def get_live_vehicle_data():
    correlation_id = str(uuid.uuid4())
    loop = asyncio.get_event_loop()
    future = loop.create_future()

    pending_futures[correlation_id] = future

    try:
        # Publish the request to GPS
        await publish_message(
            "gps_requests_Direct",
            aio_pika.ExchangeType.DIRECT,
            {
                "operation": "retrieve_live_locations",
                "type": "location",
                "correlation_id": correlation_id
            },
            routing_key="gps_requests_Direct"
        )

        # Response from GPS will be stored here
        vehicles = await asyncio.wait_for(future, timeout=5)
        logger.info(f"Vehicle live location data received: {vehicles}")
        return vehicles
        
    except asyncio.TimeoutError:
        logger.warning("Timeout waiting for GPS service response")
        return [] 
        
    except Exception as e:
        logger.error(f"Error getting live vehicle data: {e}")
        return [] 
        
    finally:
        pending_futures.pop(correlation_id, None)


#######################################################

# Herrie code for message queues
################################################################################
# send request to GPS SBlock with rabbitmq
@app.post("/gps/request_location")
async def request_gps_location(parameter: dict = Body(...)):
    await publish_message(
        "gps_requests_Direct",
        aio_pika.ExchangeType.DIRECT,
        {
            "operation": "retrieve",
            "type": "location",
            "parameters": parameter
        },
        routing_key="gps_requests_Direct"
    )
    return {"status": "Location request sent to GPS service"}

@app.post("/gps/request_speed")
async def request_gps_speed(vehicle_id: str):
    await publish_message(
        "gps_requests_Direct",
        aio_pika.ExchangeType.DIRECT,
        {
            "operation": "retrieve",
            "type": "speed",
            "vehicle_id": vehicle_id
        },
        routing_key="gps_requests_Direct"
    )
    return {"status": "Speed request sent to GPS service"}

@app.post("/gps/request_direction")
async def request_gps_direction(vehicle_id: str):
    await publish_message(
        "gps_requests_Direct",
        aio_pika.ExchangeType.DIRECT,
        {
            "operation": "retrieve",
            "type": "direction",
            "vehicle_id": vehicle_id
        },
        routing_key="gps_requests_Direct"
    )
    return {"status": "Direction request sent to GPS service"}

@app.post("/gps/request_fuel_level")
async def request_gps_fuel_level(vehicle_id: str):
    await publish_message(
        "gps_requests_Direct",
        aio_pika.ExchangeType.DIRECT,
        {
            "operation": "retrieve",
            "type": "fuel_level",
            "vehicle_id": vehicle_id
        },
        routing_key="gps_requests_Direct"
    )
    return {"status": "Fuel level request sent to GPS service"}

@app.post("/gps/request_last_update")
async def request_gps_last_update(vehicle_id: str):
    await publish_message(
        "gps_requests_Direct",
        aio_pika.ExchangeType.DIRECT,
        {
            "operation": "retrieve",
            "type": "last_update",
            "vehicle_id": vehicle_id
        },
        routing_key="gps_requests_Direct"
    )
    return {"status": "Last update request sent to GPS service"}

def handle_core_response(message):
    logger.info("Message received: " + message)
    print("Received GPS data:", message)
    # Here you could store the result, notify the UI, etc.

################################################################################

if __name__ == "__main__":
    logger.info("🚀 Starting Core service...")
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_config=None  # Use our custom logging configuration
    )


