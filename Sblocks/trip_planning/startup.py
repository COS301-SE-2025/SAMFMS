#!/usr/bin/env python3
"""
Startup script for Trip Planning Service
Handles dependency waiting and service initialization
"""
import time
import logging
import subprocess
import sys
import socket
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def wait_for_service(host, port, max_attempts=30, delay=2):
    """Wait for a service to become available"""
    logger.info(f"Waiting for {host}:{port} to become available...")
    
    for attempt in range(max_attempts):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                logger.info(f"Successfully connected to {host}:{port}")
                return True
        except Exception as e:
            logger.debug(f"Connection attempt {attempt + 1} failed: {e}")
        
        if attempt < max_attempts - 1:
            logger.info(f"Attempt {attempt + 1}/{max_attempts} failed, retrying in {delay} seconds...")
            time.sleep(delay)
    
    logger.error(f"Failed to connect to {host}:{port} after {max_attempts} attempts")
    return False

def main():
    """Main startup function"""
    logger.info("Starting Trip Planning Service...")
    
    # Wait for RabbitMQ
    rabbitmq_host = os.getenv('RABBITMQ_HOST', 'rabbitmq')
    if not wait_for_service(rabbitmq_host, 5672):
        logger.error("RabbitMQ is not available, exiting...")
        sys.exit(1)
    
    # Wait for MongoDB
    mongodb_url = os.getenv('MONGODB_URL', 'mongodb://mongodb_trip_planning:27017')
    mongodb_host = mongodb_url.split('//')[1].split(':')[0]
    mongodb_port = int(mongodb_url.split(':')[-1])
    
    if not wait_for_service(mongodb_host, mongodb_port):
        logger.error("MongoDB is not available, exiting...")
        sys.exit(1)
    
    logger.info("All dependencies are ready, starting FastAPI application...")
    
    # Get port from environment variable
    port = os.getenv("TRIP_PLANNING_SERVICE_PORT", "8000")
    
    # Start the FastAPI application
    try:
        cmd = ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", port]
        logger.info(f"Executing: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to start FastAPI application: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
        sys.exit(0)

if __name__ == "__main__":
    main()
