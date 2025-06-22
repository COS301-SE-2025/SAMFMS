from fastapi import FastAPI,Body,WebSocket
from fastapi.websockets import WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import uvicorn
import asyncio
import aio_pika
import uuid
from contextlib import asynccontextmanager


from database import db
from logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

from rabbitmq.consumer import consume_messages
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
    consumer_task_core = asyncio.create_task(consume_messages("core_responses"))
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
    for task in [consumer_task, consumer_task_core]:
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
@app.websocket("/ws/vehicles")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            try:
                vehicles = await get_live_vehicle_data()
                await websocket.send_json({"vehicles": vehicles})
            except WebSocketDisconnect:
                logger.info("WebSocket disconnected")
                break
            except Exception as e:
                logger.error(f"Error in WebSocket loop: {e}")
                try:
                    await websocket.send_json({"error": str(e)})
                except Exception:
                    logger.error("Failed to send error message to WebSocket (likely closed).")
                    break
            await asyncio.sleep(1)
    except Exception as e:
        logger.error(f"WebSocket endpoint error: {e}")

# This function will send messages on the message queue to show that it wants the live locations from gps
async def get_live_vehicle_data():
    correlation_id = str(uuid.uuid4())
    loop = asyncio.get_event_loop()
    future = loop.create_future()

    # This handler will be called when a message is received on the reply queue
    async def on_response(message):
        body = message.body.decode()
        # Parse and check correlation_id
        import json
        data = json.loads(body)
        if data.get("correlation_id") == correlation_id:
            future.set_result(data["vehicles"])  # or whatever your GPS SBlock returns

    # Start consuming the reply queue
    from rabbitmq.consumer import consume_single_message
    asyncio.create_task(consume_single_message("core_responses", on_response))

    # Publish the request with the correlation_id
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

    # Wait for the response (with timeout)
    try:
        vehicles = await asyncio.wait_for(future, timeout=5)
        logger.info("Vehicle live location data received: {vehicles}")
        return vehicles
    except asyncio.TimeoutError:
        return {"error": "Timeout waiting for GPS SBlock response"}


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
    consume_messages("core_responses", handle_core_response)
    logger.info("🚀 Starting Core service...")
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_config=None  # Use our custom logging configuration
    )


