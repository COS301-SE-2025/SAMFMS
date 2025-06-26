from fastapi import FastAPI,Body,WebSocket, Request, HTTPException
from fastapi.websockets import WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import uvicorn
import asyncio
import aio_pika
import uuid
import json
import os
from datetime import datetime
from contextlib import asynccontextmanager


from database import db
from logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

from rabbitmq.consumer import consume_messages, consume_single_message, consume_messages_Direct
from rabbitmq.admin import create_exchange, addSblock, removeSblock
from rabbitmq.producer import publish_message
from services.request_router import request_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    
    logger.info("Core service starting up...")
    
    # Store consumer tasks for proper cleanup
    consumer_tasks = []
    
    # Add startup delay to prevent race conditions
    startup_delay = int(os.getenv("SERVICE_STARTUP_DELAY", "10"))
    logger.info(f"Waiting {startup_delay} seconds before initialization...")
    await asyncio.sleep(startup_delay)
    
    # Test MongoDB connection with retry logic
    try:
        mongodb_url = os.getenv("MONGODB_URL", "mongodb://mongodb_core:27017")
        max_retries = 10
        for attempt in range(max_retries):
            try:
                client = AsyncIOMotorClient(mongodb_url)
                await client.admin.command('ping')
                logger.info("Successfully connected to MongoDB")
                client.close()
                break
            except Exception as e:
                logger.warning(f"MongoDB connection attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)
                else:
                    logger.error(f"Failed to connect to MongoDB after {max_retries} attempts")
                    raise
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        # Don't exit - let the service start and retry later

    # Initialize plugin manager
    try:
        from services.plugin_service import plugin_manager
        await plugin_manager.initialize_plugins()
        logger.info("Plugin manager initialized")
    except Exception as e:
        logger.error(f"Failed to initialize plugin manager: {e}")

    # Wait for RabbitMQ and initialize messaging with retry logic
    try:
        from rabbitmq.admin import wait_for_rabbitmq
        await wait_for_rabbitmq()
        
        # Create consumer tasks with proper error handling
        consumer_task = asyncio.create_task(consume_messages("service_status"))
        consumer_tasks.append(consumer_task)
        asyncio.create_task(consume_messages("service_presence"))

        # Consumer for live vehicle locations
        asyncio.create_task(consume_messages_Direct("core_responses","core_responses", on_response))
        asyncio.create_task(consume_messages_Direct("core_responses_geofence","core_responses_geofence",on_response_geofence))
        # C
        
        await create_exchange("general", aio_pika.ExchangeType.FANOUT)
        await publish_message("general", aio_pika.ExchangeType.FANOUT, {"message": "Core service started"})
        logger.info("Started consuming messages from service_status queue")
        logger.info("Started consuming messages from service_presence queue")
    except Exception as e:
        logger.error(f"Failed to initialize RabbitMQ: {e}")
        # Continue startup - messaging will retry

    # Start the response consumer for management/generic responses
    try:
        asyncio.create_task(request_router.response_manager.consume_responses())
        logger.info("Started response_manager.consume_responses task")
    except Exception as e:
        logger.error(f"Failed to start response_manager.consume_responses: {e}")

    # Initialize request router
    try:
        await request_router.initialize()
        logger.info("Request router initialized")
    except Exception as e:
        logger.error(f"Failed to initialize request router: {e}")
    
    logger.info("Core service startup completed")
    
    yield

    logger.info("Core service shutting down...")
    # Properly shutdown consumer tasks
    for task in consumer_tasks:
        if not task.done():
            task.cancel()
            try:
                await asyncio.wait_for(task, timeout=5.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                logger.info(f"Consumer task cancelled/timed out during shutdown")
            except Exception as e:
                logger.warning(f"Error during task shutdown: {e}")
    
    logger.info("Core service shutdown completed")

app = FastAPI(
    title="SAMFMS Core Service",
    description="Central API gateway for South African Fleet Management System",
    version="1.0.0",
    lifespan=lifespan
)

origins = [
    "http://localhost:3000",     
    "http://127.0.0.1:3000",
    "http://localhost:5000",     
    "*",                        
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],        
    allow_headers=["*"],        
)


from routes.auth import router as auth_router
from routes.plugins import router as plugins_router

# Try to import service_proxy router with error handling
try:
    from routes.service_proxy import router as service_proxy_router
    logger.info("✅ Service proxy router imported successfully")
    service_proxy_available = True
except Exception as e:
    logger.error(f"❌ Failed to import service proxy router: {e}")
    service_proxy_router = None
    service_proxy_available = False

app.include_router(auth_router)
app.include_router(plugins_router, prefix="/api")

# Only include service_proxy if it imported successfully
if service_proxy_available and service_proxy_router:
    app.include_router(service_proxy_router)  # service_proxy already has /api prefix
    logger.info("✅ Service proxy router included successfully")
else:
    logger.error("❌ Service proxy router not available - using fallback routes")



@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}

@app.get("/api/health/services", tags=["Health"])
async def check_service_health():
    """Check health of downstream services"""
    services_status = {}
    
    for service in ["management", "gps", "trip_planning", "vehicle_maintenance"]:
        try:
            # Test service communication via RabbitMQ with timeout
            correlation_id = str(uuid.uuid4())
            test_message = {
                "correlation_id": correlation_id,
                "endpoint": "/health",
                "method": "GET",
                "data": {},
                "user_context": {"user_id": "health_check"},
                "timestamp": datetime.utcnow().isoformat(),
                "service": service,
                "trace_id": correlation_id
            }
            
            # Quick health check with short timeout
            response = await asyncio.wait_for(
                request_router.send_request_and_wait(service, test_message, correlation_id),
                timeout=5.0
            )
            services_status[service] = "healthy"
        except asyncio.TimeoutError:
            services_status[service] = "timeout - service may be unavailable"
        except Exception as e:
            services_status[service] = f"unhealthy: {str(e)}"
    
    overall_status = "healthy" if all("healthy" in status for status in services_status.values()) else "degraded"
    
    return {
        "status": overall_status,
        "services": services_status,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/test/connection", tags=["Testing"])
async def test_service_connection():
    """Test endpoint to verify Core to Management service communication"""
    try:
        correlation_id = str(uuid.uuid4())
        test_message = {
            "correlation_id": correlation_id,
            "endpoint": "/api/drivers",
            "method": "GET",
            "data": {"limit": 1},
            "user_context": {"user_id": "test_user", "permissions": ["read:drivers"]},
            "timestamp": datetime.utcnow().isoformat(),
            "service": "management",
            "trace_id": correlation_id
        }
        
        # Test communication with management service
        response = await asyncio.wait_for(
            request_router.send_request_and_wait("management", test_message, correlation_id),
            timeout=10.0
        )
        
        return {
            "status": "success",
            "message": "Core to Management service communication working",
            "response_received": True,
            "data": response
        }
        
    except asyncio.TimeoutError:
        return {
            "status": "error",
            "message": "Timeout - Management service not responding",
            "response_received": False
        }
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Communication error: {str(e)}",
            "response_received": False
        }

# All request routing is now handled by the service proxy router
# No redirect routes needed - direct API routing through /api/ endpoints

@app.get("/sblock/add/{sblock_ip}/{username}", tags=["SBlock"])
async def add_sblock_route(sblock_ip: str, username: str):
    try:
        await addSblock(username)
        return {"status": "success", "message": f"SBlock {username} added"}
    except Exception as e:
        logger.error(f"Error adding SBlock: {str(e)}")
        return {"status": "error", "message": str(e)}
    

    
@app.get("/sblock/remove/{sblock_ip}/{username}", tags=["SBlock"])
async def remove_sblock_route(sblock_ip: str, username: str):
    try:
        await removeSblock(username)
        return {"status": "success", "message": f"SBlock {username} removed"}
    except Exception as e:
        logger.error(f"Error removing SBlock: {str(e)}")
        return {"status": "error", "message": str(e)}

# Here code for websocket between Frontend and Core to retrieve live locations of vehicles
pending_futures = {}

# This function receives vehicle locations
async def on_response(message):
    logger.info(f"Message received from GPS: {message}")
    body = message.body.decode()
    data = json.loads(body)
    logger.info(f"Data from message: {data}")
    correlation_id = data.get("correlation_id")
    if correlation_id in pending_futures:
        pending_futures[correlation_id].set_result(data["vehicles"])
        del pending_futures[correlation_id]

# This function receives the newly created geofence
pending_futures_geofences = {}

async def on_response_geofence(message):
    logger.info(f"Message received from GPS about Geofence: {message}")
    body = message.body.decode()
    data = json.loads(body)
    correlation_id = data.get("correlation_id")
    geofence = data.get("geofence")
    if geofence == "failed":
        logger.info("For build")
    else:
        logger.info("For build")



@app.websocket("/ws/vehicles")
async def websocket_endpoint(websocket: WebSocket):
    logger.info("Web socket accessed")
    await websocket.accept()
    logger.info("WebSocket connection accepted and ready to send data.")
    try:
        while True:
            try:
                vehicles = await get_live_vehicle_data()
                logger.info(f"Sending to frontend: {vehicles}")
                await websocket.send_json({"vehicles": vehicles})
                await asyncio.sleep(2)  # Wait 5 seconds before sending the next update
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

    # Store the future so on_response can access it
    pending_futures[correlation_id] = future

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

    try:
        vehicles = await asyncio.wait_for(future, timeout=5)
        logger.info(f"Vehicle live location data received: {vehicles}")
        return vehicles
    except asyncio.TimeoutError:
        logger.warning("Timeout waiting for GPS SBlock response")
        # Clean up the future if it timed out
        pending_futures.pop(correlation_id, None)
        return []


#######################################################
# Herrie code for gps geofences
@app.post("/api/gps/geofences/circle")
async def add_new_geofence(parameter: dict = Body(...)):
    logger.info(f"Add geofence request received: {parameter}")
    await publish_message(
        "gps_requests_Direct",
        aio_pika.ExchangeType.DIRECT,
        {
            "operation": "add_new_geofence",
            "parameters": parameter
        },
        routing_key="gps_requests_Direct"
    )


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




###########################


@app.get("/debug/routes", tags=["Debug"])
async def list_routes():
    """Debug endpoint to list all available routes"""
    routes = []
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            routes.append({
                "path": route.path,
                "methods": list(route.methods) if route.methods else [],
                "name": getattr(route, 'name', 'unknown')
            })
    return {"routes": routes}


@app.get("/api/test/simple", tags=["Testing"])
async def simple_test():
    """Simple test endpoint to verify /api routing works"""
    return {"status": "success", "message": "API routing is working", "timestamp": datetime.utcnow().isoformat()}


@app.get("/api/vehicles/direct", tags=["Testing"])
async def get_vehicles_direct():
    """Direct vehicles endpoint for testing without service proxy"""
    try:
        correlation_id = str(uuid.uuid4())
        test_message = {
            "correlation_id": correlation_id,
            "endpoint": "/api/vehicles",
            "method": "GET",
            "data": {"limit": 100},
            "user_context": {"user_id": "direct_test", "permissions": ["read:vehicles"]},
            "timestamp": datetime.utcnow().isoformat(),
            "service": "management",
            "trace_id": correlation_id
        }
        
        # Test direct communication with management service
        response = await asyncio.wait_for(
            request_router.send_request_and_wait("management", test_message, correlation_id),
            timeout=30.0
        )
        
        return response
        
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Management service timeout")
    except Exception as e:
        logger.error(f"Direct vehicles request failed: {e}")
        raise HTTPException(status_code=500, detail=f"Service error: {str(e)}")


# Temporary direct vehicles endpoint for testing (bypassing auth)
@app.get("/api/vehicles", tags=["Testing"])
async def get_vehicles_direct(limit: int = 100):
    """Temporary direct vehicles endpoint to test routing"""
    try:
        logger.info(f"Direct vehicles endpoint called with limit: {limit}")
        
        # Try to route to management service directly
        correlation_id = str(uuid.uuid4())
        test_message = {
            "correlation_id": correlation_id,
            "endpoint": "/api/vehicles",
            "method": "GET",
            "data": {"limit": limit},
            "user_context": {"user_id": "test_user", "permissions": ["*"]},
            "timestamp": datetime.utcnow().isoformat(),
            "service": "management",
            "trace_id": correlation_id
        }
        
        # Test communication with management service
        try:
            response = await asyncio.wait_for(
                request_router.send_request_and_wait("management", test_message, correlation_id),
                timeout=10.0
            )
            logger.info("✅ Got response from management service")
            return response
            
        except asyncio.TimeoutError:
            logger.error("❌ Timeout waiting for management service")
            return {
                "vehicles": [],
                "total": 0,
                "error": "Management service timeout",
                "fallback": True
            }
        except Exception as e:
            logger.error(f"❌ Error communicating with management service: {e}")
            return {
                "vehicles": [
                    {
                        "id": "test-1",
                        "make": "Toyota",
                        "model": "Corolla",
                        "year": "2020",
                        "status": "Active",
                        "driver": "Test Driver"
                    }
                ],
                "total": 1,
                "error": f"Communication error: {str(e)}",
                "fallback": True
            }
            
    except Exception as e:
        logger.error(f"Error in direct vehicles endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Compatibility route for nginx forwarding (receives /vehicles instead of /api/vehicles)
@app.get("/vehicles", tags=["Compatibility"])
async def get_vehicles_compatibility(limit: int = 100):
    """Compatibility route for nginx forwarding - forwards to /api/vehicles"""
    logger.info(f"Received /vehicles request (nginx forwarding), redirecting to /api/vehicles with limit: {limit}")
    return await get_vehicles_direct(limit)

@app.post("/vehicles", tags=["Compatibility"])
async def create_vehicle_compatibility(vehicle_data: dict):
    """Compatibility route for nginx forwarding POST /vehicles to core"""
    logger.info("Received POST /vehicles request (nginx forwarding), forwarding to management service")
    try:
        correlation_id = str(uuid.uuid4())
        test_message = {
            "correlation_id": correlation_id,
            "endpoint": "/api/vehicles",
            "method": "POST",
            "data": vehicle_data,
            "user_context": {
                "user_id": "nginx_compat", 
                "permissions": ["*"],  # Grant all permissions for compatibility
                "role": "admin",
                "bypass_auth": True  # Bypass auth checks for nginx compatibility
            },
            "timestamp": datetime.utcnow().isoformat(),
            "service": "management",
            "trace_id": correlation_id
        }
        
        # Forward to management service
        response = await asyncio.wait_for(
            request_router.send_request_and_wait("management", test_message, correlation_id),
            timeout=30.0
        )
        
        return response
        
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Management service timeout")
    except Exception as e:
        logger.error(f"Compatibility vehicles POST request failed: {e}")
        raise HTTPException(status_code=500, detail=f"Service error: {str(e)}")

@app.put("/vehicles/{vehicle_id}", tags=["Compatibility"])
async def update_vehicle_compatibility(vehicle_id: str, vehicle_data: dict):
    """Compatibility route for nginx forwarding PUT /vehicles/{id} to core"""
    logger.info(f"Received PUT /vehicles/{vehicle_id} request (nginx forwarding), forwarding to management service")
    try:
        correlation_id = str(uuid.uuid4())
        test_message = {
            "correlation_id": correlation_id,
            "endpoint": f"/api/vehicles/{vehicle_id}",
            "method": "PUT",
            "data": vehicle_data,
            "user_context": {"user_id": "nginx_compat", "permissions": ["write:vehicles"]},
            "timestamp": datetime.utcnow().isoformat(),
            "service": "management",
            "trace_id": correlation_id
        }
        
        # Forward to management service
        response = await asyncio.wait_for(
            request_router.send_request_and_wait("management", test_message, correlation_id),
            timeout=30.0
        )
        
        return response
        
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Management service timeout")
    except Exception as e:
        logger.error(f"Compatibility vehicles PUT request failed: {e}")
        raise HTTPException(status_code=500, detail=f"Service error: {str(e)}")

@app.delete("/vehicles/{vehicle_id}", tags=["Compatibility"])
async def delete_vehicle_compatibility(vehicle_id: str):
    """Compatibility route for nginx forwarding DELETE /vehicles/{id} to core"""
    logger.info(f"Received DELETE /vehicles/{vehicle_id} request (nginx forwarding), forwarding to management service")
    try:
        correlation_id = str(uuid.uuid4())
        test_message = {
            "correlation_id": correlation_id,
            "endpoint": f"/api/vehicles/{vehicle_id}",
            "method": "DELETE",
            "data": {"vehicle_id": vehicle_id},
            "user_context": {"user_id": "nginx_compat", "permissions": ["delete:vehicles"]},
            "timestamp": datetime.utcnow().isoformat(),
            "service": "management",
            "trace_id": correlation_id
        }
        
        # Forward to management service
        response = await asyncio.wait_for(
            request_router.send_request_and_wait("management", test_message, correlation_id),
            timeout=30.0
        )
        
        return response
        
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Management service timeout")
    except Exception as e:
        logger.error(f"Compatibility vehicles DELETE request failed: {e}")
        raise HTTPException(status_code=500, detail=f"Service error: {str(e)}")

@app.get("/api/debug/routes", tags=["Testing"])
async def debug_routes():
    """Debug endpoint to check what routes are registered"""
    routes_info = []
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            routes_info.append({
                "path": route.path,
                "methods": list(route.methods) if route.methods else [],
                "name": getattr(route, 'name', 'unknown')
            })
    
    return {
        "total_routes": len(routes_info),
        "routes": routes_info,
        "api_routes": [r for r in routes_info if r["path"].startswith("/api")]
    }

@app.get("/service_presence", tags=["plugins"])
async def service_presence():
    services = await db.get_collection("service_presence").find({}, {"service": 1, "_id": 0}).to_list(length=None)
    service_names = [service["service_name"] for service in services]
    return service_names

if __name__ == "__main__":
    logger.info("🚀 Starting Core service...")
    port = int(os.getenv("CORE_PORT", "8000"))
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_config=None  
    )


@app.get("/api/drivers", tags=["Drivers"])
async def get_drivers(limit: int = 100):
    """
    Fetch drivers from the management service.
    """
    try:
        logger.info(f"Direct drivers endpoint called with limit: {limit}")
        correlation_id = str(uuid.uuid4())
        test_message = {
            "correlation_id": correlation_id,
            "endpoint": "/api/drivers",
            "method": "GET",
            "data": {"limit": limit},
            "user_context": {"user_id": "test_user", "permissions": ["read:drivers"]},
            "timestamp": datetime.utcnow().isoformat(),
            "service": "management",
            "trace_id": correlation_id
        }
        response = await asyncio.wait_for(
            request_router.send_request_and_wait("management", test_message, correlation_id),
            timeout=10.0
        )
        logger.info("✅ Got response from management service for drivers")
        return response
    except asyncio.TimeoutError:
        logger.error("❌ Timeout waiting for management service (drivers)")
        return {
            "drivers": [],
            "total": 0,
            "error": "Management service timeout",
            "fallback": True
        }
    except Exception as e:
        logger.error(f"❌ Error communicating with management service (drivers): {e}")
        return {
            "drivers": [],
            "total": 0,
            "error": f"Communication error: {str(e)}",
            "fallback": True
        }