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

from fastapi import FastAPI, HTTPException, Body, Request
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

async def test_traccar_connection():
    """Test connection to Traccar server"""
    try:
        response = requests.get(
            f"{TRACCAR_API_URL}/server",
            auth=(TRACCAR_ADMIN_USER, TRACCAR_ADMIN_PASS),
            timeout=10
        )
        response.raise_for_status()
        logger.info("Traccar connection test successful")
        return True
    except Exception as e:
        logger.error(f"Traccar connection test failed: {e}")
        return False


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
    
    startup_delay = int(os.getenv("SERVICE_STARTUP_DELAY", "15"))
    logger.info(f"Waiting {startup_delay} seconds for services to initialize...")
    await asyncio.sleep(startup_delay)

    traccar_ready = await test_traccar_connection()
    if not traccar_ready:
        logger.warning("Traccar connection failed during startup")

    # Test connections during startup
#    redis_conn = ConnectionManager.get_redis_connection()
#    if redis_conn:
#        logger.info("Redis connection established successfully")
#    else:
#        logger.error("Failed to establish Redis connection")
    
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
TRACCAR_API_URL = os.getenv("TRACCAR_API_URL", "http://traccar:8082/api")
TRACCAR_ADMIN_USER = os.getenv("TRACCAR_ADMIN_USER", "herrie732@gmail.com")
TRACCAR_ADMIN_PASS = os.getenv("TRACCAR_ADMIN_PASS", "Eirreh732")

async def fetch_and_respond_live_locations(request_data):
    correlation_id = request_data.get("correlation_id")
    # 1. Fetch live vehicle/device data from Traccar
    try:
        # This will retrieve information like name, id, online/offline
        responseDevices = requests.get(
            f"{TRACCAR_API_URL}/devices",
            auth=(TRACCAR_ADMIN_USER, TRACCAR_ADMIN_PASS)
        )
        responseDevices.raise_for_status()
        devices = responseDevices.json()
        # This will retrieve actual gps locations, speed ens.
        responsePositions = requests.get(
            f"{TRACCAR_API_URL}/positions",
            auth=(TRACCAR_ADMIN_USER, TRACCAR_ADMIN_PASS)
        )
        responsePositions.raise_for_status()
        Positions = responsePositions.json()
        # You can filter/transform devices as needed for your frontend
        vehicles = [
            {
                "id": d["id"],
                "name": d.get("name"),
                "attributes": d.get("attributes"),
                "lastUpdate": d.get("lastUpdate"),
                "model": d.get("model"),
                "category": d.get("category"),
                "status": d.get("status"),
            }
            for d in devices
        ]
        logger.info(f"Vehicles info: {vehicles} ")

        positions = [
            {
                "distance": p.get("attributes", {}).get("distance"),
                "totalDistance": p.get("attributes", {}).get("totalDistance"),
                "motion": p.get("attributes", {}).get("motion"),
                "deviceId": p.get("deviceId"),
                "latitude": p.get("latitude"),
                "longitude": p.get("longitude"),
                "altitude": p.get("altitude"),
                "speed": p.get("speed"),
                "geofenceIds": p.get("geofenceIds"),
            }
            for p in Positions
        ]
        logger.info(f"Positions info: {positions}")

        # Merge vehicles and Positions by id/deviceId
        positions_lookup = {p["deviceId"]: p for p in positions}
        merged_vehicles = []
        for v in vehicles:
            pos = positions_lookup.get(v["id"], {})
            merged_vehicle = {**v, **pos} 
            merged_vehicles.append(merged_vehicle)
        
        logger.info(f"Merged devices and positions: {merged_vehicles}")
    except Exception as e:
        vehicles = []
        print(f"Error fetching Traccar devices: {e}")

    # Response via message queue back to core
    response_payload = {
        "correlation_id": correlation_id,
        "vehicles": merged_vehicles
    }
    await publish_message(
        "core_responses",
        aio_pika.ExchangeType.DIRECT,
        response_payload,
        routing_key="core_responses"
    )

async def handle_gps_request(message: aio_pika.IncomingMessage):
    async with message.process():
        data = json.loads(message.body.decode())
        logger.info(f"Received message: {data}")

        operation = data.get("operation")
        data_type = data.get("type")

        # if it is retrieve then forward it to DBlock
        if operation == "retrieve":
            await request_gps_location(data)
        elif operation == "retrieve_live_locations":
            await fetch_and_respond_live_locations(data)
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
TRACCAR_SIMULATION_HOST = os.getenv("TRACCAR_SIMULATION_HOST", "http://traccar:5055")

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
    traccar_host = os.getenv("TRACCAR_HOST", TRACCAR_SIMULATION_HOST)
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
        auth=HTTPBasicAuth("herrie732@gmail.com", "Eirreh732")
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
    
@app.post("/test/fetch_live_locations")
async def test_fetch_live_locations(request: Request):
    """
    Test endpoint to fetch live locations from Traccar and return the result directly.
    """
    request_data = await request.json()
    # Patch fetch_and_respond_live_locations to return vehicles directly for testing
    correlation_id = request_data.get("correlation_id", "test-correlation-id")
    try:
        # Call the function and capture the vehicles
        vehicles = []
        try:
            response = requests.get(
                f"{TRACCAR_API_URL}/devices",
                auth=(TRACCAR_ADMIN_USER, TRACCAR_ADMIN_PASS)
            )
            response.raise_for_status()
            devices = response.json()
            vehicles = [
                {
                    "id": d["id"],
                    "name": d.get("name"),
                    "status": d.get("status", "unknown"),
                    "latitude": d.get("lastPosition", {}).get("latitude"),
                    "longitude": d.get("lastPosition", {}).get("longitude"),
                    "altitude": d.get("lastPosition", {}).get("altitude"),
                    "speed": d.get("lastPosition", {}).get("speed"),
                    "geofenceIds" : d.get("geofenceIds"),
                    "distance": d.get("lastPosition", {}).get("distance"),
                    "totalDistance": d.get("lastPosition", {}).get("totalDistance"),
                    "motion": d.get("lastPosition", {}).get("motion"),
                }
                for d in devices
            ]
        except Exception as e:
            vehicles = []
            return {"vehicles": vehicles, "error": str(e), "correlation_id": correlation_id}
        return {"vehicles": vehicles, "correlation_id": correlation_id}
    except Exception as e:
        return {"vehicles": [], "error": str(e), "correlation_id": correlation_id}

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting GPS Service in standalone mode")
    port = int(os.getenv("GPS_SERVICE_PORT", "8000"))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_config=None  # Use our custom logging configuration
    )

