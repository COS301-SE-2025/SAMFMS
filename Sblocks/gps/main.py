"""
GPS Service - SAMFMS Microservice
Enhanced with structured logging, health monitoring, performance metrics, and RabbitMQ request handling.
"""

# Somewhere the will have to be like a default start location// probably the companies building
# Traccar account will be created for the admin, admin details should be passed to GPS SBlock

import os
import asyncio
import aio_pika
import json
import httpx
# import for vehicle simulation
import time
import requests
import openrouteservice
import threading
from pydantic import BaseModel
from requests.auth import HTTPBasicAuth

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware

from logging_config import setup_logging, get_logger
from connections import ConnectionManager
from middleware import get_logging_middleware, get_security_middleware
from health_metrics import get_health_status, get_metrics
from service_request_handler import gps_request_handler

# message queue imports
from rabbitmq.consumer import consume_messages_Direct,consume_messages_FanOut
from rabbitmq.admin import create_exchange
from rabbitmq.producer import publish_message


SERVICE_NAME = "gps-service"
SERVICE_VERSION = "1.0.0"
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

logger = setup_logging(SERVICE_NAME)

app = FastAPI(
    title="GPS Service",
    version=SERVICE_VERSION,
    description="GPS tracking and location services for SAMFMS",
    docs_url="/docs" if ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if ENVIRONMENT == "development" else None
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.middleware("http")(get_security_middleware())
app.middleware("http")(get_logging_middleware())


# Event handlers
@app.on_event("startup")
async def startup_event():
    """Initialize service on startup."""
    logger.info(
        "GPS Service starting up",
        extra={
            "version": SERVICE_VERSION,
            "environment": ENVIRONMENT,
            "service": SERVICE_NAME
        }    )
    
    # Test connections during startup
    redis_conn = ConnectionManager.get_redis_connection()
    if redis_conn:
        logger.info("Redis connection established successfully")
    else:
        logger.error("Failed to establish Redis connection")
    
    rabbitmq_conn = ConnectionManager.get_rabbitmq_connection()
    if rabbitmq_conn:
        logger.info("RabbitMQ connection established successfully")
        rabbitmq_conn.close()  # Close test connection
    else:
        logger.error("Failed to establish RabbitMQ connection")
    
    # Initialize GPS service request handler
    try:
        await gps_request_handler.initialize()
        logger.info("GPS service request handler initialized")
    except Exception as e:
        logger.error(f"GPS service request handler initialization failed: {e}")
    
    logger.info("GPS Service startup completed")

    # Start the RabbitMQ consumer
    asyncio.create_task(consume_messages_Direct("gps_requests_Direct","gps_requests_Direct",handle_gps_request))
    asyncio.create_task(consume_messages_Direct("gps_responses_Direct","gps_responses_Direct" ,handle_DBlock_responses))

    


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    logger.info("GPS Service shutting down")
    
    # Close all connections
    ConnectionManager.close_connections()
    
    logger.info("GPS Service shutdown completed")


# API Endpoints
@app.get("/")
def read_root():
    """Root endpoint with service information."""
    logger.info("Root endpoint accessed")
    return {
        "message": "Hello from GPS Service",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "environment": ENVIRONMENT
    }


@app.get("/health")
def health_check():
    """Comprehensive health check endpoint."""
    return get_health_status()


@app.get("/metrics")
def metrics():
    """Performance metrics endpoint."""
    return get_metrics()


@app.get("/gps/locations")
def get_locations():
    """Get GPS location data."""
    logger.info("GPS locations endpoint accessed")
    
    # TODO: Implement actual GPS location retrieval
    # This is a placeholder implementation
    try:
        redis_conn = ConnectionManager.get_redis_connection()
        if redis_conn:
            # Example: Get locations from Redis
            # locations = redis_conn.get("gps:locations")
            logger.debug("Retrieved GPS locations from Redis")
        
        return {
            "locations": [],
            "message": "GPS locations retrieved successfully",
            "count": 0
        }
        
    except Exception as e:
        logger.error(
            "Failed to retrieve GPS locations",
            extra={
                "error": str(e),
                "endpoint": "/gps/locations"
            }
        )
        raise


@app.post("/gps/locations")
def update_location(location_data: dict):
    """Update GPS location data."""
    logger.info("GPS location update endpoint accessed")
    
    # TODO: Implement actual GPS location update
    # This is a placeholder implementation
    try:
        redis_conn = ConnectionManager.get_redis_connection()
        if redis_conn:
            # Example: Store location in Redis
            # redis_conn.set("gps:locations", json.dumps(location_data))
            logger.debug("Stored GPS location data in Redis")
        
        rabbitmq_conn = ConnectionManager.get_rabbitmq_connection()
        if rabbitmq_conn:
            # Example: Publish location update to message queue
            # channel = rabbitmq_conn.channel()
            # channel.basic_publish(exchange='', routing_key='gps_updates', body=json.dumps(location_data))
            logger.debug("Published GPS location update to message queue")
            rabbitmq_conn.close()
        
        return {
            "message": "GPS location updated successfully",
            "location_id": location_data.get("id", "unknown")
        }
        
    except Exception as e:
        logger.error(
            "Failed to update GPS location",
            extra={
                "error": str(e),
                "endpoint": "/gps/locations",
                "location_data": location_data
            }
        )
        raise

# Traccar function to create a new simulation
async def create_new_simulation(device_id, lat, lon, speed):
    payload = {
        "device_id": device_id,
        "start_latitude": lat,
        "start_longitude": lon,
        "speed": speed
    }

    async with httpx.AsyncClient() as client:
        response = await client.post("http://simulator_manager:8000/simulate_vehicle", json=payload)
        return response.json()

# Herrie code: For Message queue between GPS SBlock and Core
# Function to handle the direct messages sent to the gps_requests queue
async def handle_gps_request(message: aio_pika.IncomingMessage):
    async with message.process():
        data = json.loads(message.body.decode())
        logger.info(f"Received message: {data}")

        operation = data.get("operation")
        data_type = data.get("type")

        # if it is retrieve then forward it to DBlock
        if operation == "retrieve":
            await request_gps_location(data)
        else:
            logger.warning(f"Unsupported operation: {operation} for message: {data}")

# function to for responses from DBlock
async def handle_DBlock_responses(message: aio_pika.IncomingMessage):
    async with message.process():
        data = json.loads(message.body.decode())
        logger.info(f"Received message from DBlock: {data}")

# function to forward messages to dblock
async def request_gps_location(message: dict):
    await publish_message(
        "gps_db_requests",
        aio_pika.ExchangeType.DIRECT,
        {"message": f"Message From GPS SBlock to GPS DBlock test : {message}"},
        routing_key="gps_db_requests"
    )
    return {"status": "Request sent to GPS DB service"}
#############################################################################

# Herrie code for GPS vehicle simulation
TRACCAR_HOST = "http://traccar:5055"
ORS_API_KEY = "5b3ce3597851110001cf6248967d5deccac54ac1bca4d679e41d602d"
DELAY = 2

def simulate_vehicle_route(device_id, traccar_host, ors_api_key, start, end, delay=2):
    client = openrouteservice.Client(key=ors_api_key)
    route = client.directions(
        coordinates=[start, end],
        profile='driving-car',
        format='geojson'
    )
    coordinates = route['features'][0]['geometry']['coordinates']

    print(f"Simulating vehicle '{device_id}' on a real route...")
    print(f"Total points in route: {len(coordinates)}")

    for point in coordinates:
        lon, lat = point
        response = requests.get(traccar_host, params={
            "id": device_id,
            "lat": lat,
            "lon": lon,
            "speed": 50
        })
        print(f"[{response.status_code}] Sent point: ({lat:.6f}, {lon:.6f})")
        time.sleep(delay)

    print("Route complete.")

class SimulationRequest(BaseModel):
    device_id: str
    start_lat: float
    start_lon: float
    end_lat: float
    end_lon: float

@app.post("/simulate_vehicle")
def api_simulate_vehicle(req: SimulationRequest):
    ors_api_key = os.getenv("ORS_API_KEY", ORS_API_KEY)
    traccar_host = os.getenv("TRACCAR_HOST", TRACCAR_HOST)
    delay = int(os.getenv("SIM_DELAY", DELAY))

    # Run simulation in a background thread so it doesn't block the API
    threading.Thread(
        target=simulate_vehicle_route,
        args=(req.device_id, traccar_host, ors_api_key, [req.start_lon, req.start_lat], [req.end_lon, req.end_lat], delay),
        daemon=True
    ).start()

    return {"status": "started", "device_id": req.device_id}

def add_traccar_device(name, unique_id):
    url = f"http://traccar:8082/api/devices"
    payload = {
        "name": name,
        "uniqueId": unique_id
    }

    response = requests.post(
        url,
        json = payload,
        auth = HTTPBasicAuth("herrie732@gmail.com","Eirreh732") # will have to create a traccar account for fleetmanager    
    )
    if response.status_code == 200:
        print(f"Device '{name}' added successfully.")
        return response.json()
    else:
        print(f"Failed to add device: {response.text}")
        return None

class CreateDeviceRequest(BaseModel):
    name: str
    unique_id: str

@app.post("/create_device")
def create_device(req: CreateDeviceRequest):
    result = add_traccar_device(req.name, req.unique_id)
    if result:
        return {"status": "created", "device": result}
    else:
        return {"status": "error", "message": "Failed to create device"}
# User creation does not work yet!
class CreateUserRequest(BaseModel):
    name: str
    email: str
    password: str

def add_traccar_user(name,email, password):
    url = "http://traccar:8082/api/users"
    payload = {
        "name": name,
        "email": email,
        "password": password
    }
    # By default, Traccar requires admin authentication to create users
    # Replace with your admin credentials or use environment variables for security
    admin_user = os.getenv("TRACCAR_ADMIN_USER", "admin")
    admin_pass = os.getenv("TRACCAR_ADMIN_PASS", "admin")
    response = requests.post(
        url,
        json=payload,
        auth=HTTPBasicAuth(admin_user, admin_pass)
    )
    logger.info(f"Traccar user creation response: {response.status_code} {response.text}")
    if response.status_code in (200, 201):
        print(f"User '{email}' created successfully.")
        return response.json()
    else:
        print(f"Failed to create user: {response.text}")        
        return None

@app.post("/create_traccar_user")
def create_traccar_user(req: CreateUserRequest):
    result = add_traccar_user(req.name, req.email, req.password)
    if result:
        return {"status": "created", "user": result}
    else:
        return {"status": "error", "message": "Failed to create user"}
    
# Code for adding geofences

class PolylineGeofenceRequest(BaseModel):
    name: str
    coordinates: list  # List of [lon, lat] pairs
    description: str = ""

class CircleGeofenceRequest(BaseModel):
    name: str
    center_lat: float
    center_lon: float
    radius: float  # in meters
    description: str = ""

def add_polyline_geofence(name, coordinates, description=""):
    url = "http://traccar:8082/api/geofences"
    payload = {
        "name": name,
        "description": description,
        "area": "POLYGON((" + ", ".join([f"{lon} {lat}" for lon, lat in coordinates] + [f"{coordinates[0][0]} {coordinates[0][1]}"]) + "))"
    }
    #admin_user = os.getenv("TRACCAR_ADMIN_USER", "admin")
    #admin_pass = os.getenv("TRACCAR_ADMIN_PASS", "admin")
    response = requests.post(
        url,
        json=payload,
        auth=HTTPBasicAuth("herrie732@gmail.com","Eirreh732")
    )
    logger.info(f"Traccar polyline geofence response: {response.status_code} {response.text}")
    if response.status_code in (200, 201):
        return response.json()
    else:
        return None

def add_circle_geofence(name, center_lat, center_lon, radius, description=""):
    url = "http://traccar:8082/api/geofences"
    payload = {
        "name": name,
        "description": description,
        "area": f"CIRCLE({center_lon} {center_lat},{radius})"
    }
    #admin_user = os.getenv("TRACCAR_ADMIN_USER", "admin")
    #admin_pass = os.getenv("TRACCAR_ADMIN_PASS", "admin")
    response = requests.post(
        url,
        json=payload,
        auth=HTTPBasicAuth("herrie732@gmail.com","Eirreh732")
    )
    logger.info(f"Traccar circle geofence response: {response.status_code} {response.text}")
    if response.status_code in (200, 201):
        return response.json()
    else:
        return None

@app.post("/geofence/polyline")
def create_polyline_geofence(req: PolylineGeofenceRequest):
    result = add_polyline_geofence(req.name, req.coordinates, req.description)
    if result:
        return {"status": "created", "geofence": result}
    else:
        return {"status": "error", "message": "Failed to create polyline geofence"}

@app.post("/geofence/circle")
def create_circle_geofence(req: CircleGeofenceRequest):
    result = add_circle_geofence(req.name, req.center_lat, req.center_lon, req.radius, req.description)
    if result:
        return {"status": "created", "geofence": result}
    else:
        return {"status": "error", "message": "Failed to create circle geofence"}

#############################################################################
    
if __name__ == "__main__":
    import uvicorn
    logger.info("Starting GPS Service in standalone mode")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_config=None  # Use our custom logging configuration
    )
