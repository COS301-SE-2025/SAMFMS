from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import uvicorn
import asyncio
import aio_pika
from contextlib import asynccontextmanager

from database import db
from logging_config import setup_logging, get_logger


setup_logging()
logger = get_logger(__name__)

from rabbitmq.consumer import consume_messages
from rabbitmq.admin import create_exchange, add_sblock, remove_sblock
from rabbitmq.producer import publish_message

@asynccontextmanager
async def lifespan(app: FastAPI):
    
    logger.info("Core service starting up...")
    
    try:
        client = AsyncIOMotorClient("mongodb://host.docker.internal:27017")
        await client.admin.command('ping')
        logger.info("Successfully connected to MongoDB")
        client.close()
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
    
    
    try:
        from services.plugin_service import plugin_manager
        await plugin_manager.initialize_plugins()
        logger.info("Plugin manager initialized")
    except Exception as e:
        logger.error(f"Failed to initialize plugin manager: {e}")

    consumer_task = asyncio.create_task(consume_messages("service_status"))
    await create_exchange("general", aio_pika.ExchangeType.FANOUT)
    await publish_message("general", aio_pika.ExchangeType.FANOUT, {"message": "Core service started"})

    logger.info("Started consuming messages from service_status queue")
    
    logger.info("Core service startup completed")
    
    yield
    

    logger.info("Core service shutting down...")
    if not consumer_task.done():
        consumer_task.cancel()
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

app.include_router(auth_router)
app.include_router(plugins_router, prefix="/api")



@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}

@app.get("/sblock/add/{sblock_ip}/{username}", tags=["SBlock"])
async def add_sblock_route(sblock_ip: str, username: str):
    try:
        await add_sblock(sblock_ip, username)
        return {"status": "success", "message": f"SBlock {username} added"}
    except Exception as e:
        logger.error(f"Error adding SBlock: {str(e)}")
        return {"status": "error", "message": str(e)}
    

    
@app.get("/sblock/remove/{sblock_ip}/{username}", tags=["SBlock"])
async def remove_sblock_route(sblock_ip: str, username: str):
    try:
        await remove_sblock(sblock_ip, username)
        return {"status": "success", "message": f"SBlock {username} removed"}
    except Exception as e:
        logger.error(f"Error removing SBlock: {str(e)}")
        return {"status": "error", "message": str(e)}



if __name__ == "__main__":
    logger.info("🚀 Starting Core service...")
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_config=None  
    )
