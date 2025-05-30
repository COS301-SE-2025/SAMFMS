#!/usr/bin/env python3
"""
Startup script for GPS Service.
Waits for dependencies and starts the service.
"""

import socket
import time
import subprocess
import sys
import os

def wait_for_service(host, port, service_name, timeout=60):
    """Wait for a service to be available."""
    print(f"Waiting for {service_name} at {host}:{port}...")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                print(f"  {service_name} is ready!")
                return True
        except (socket.timeout, socket.error):
            print(f"  {service_name} is unavailable - sleeping")
            time.sleep(1)
    
    print(f"  Timeout waiting for {service_name}")
    return False

def main():
    """Main startup function."""
    print("Starting GPS Service dependency checks...")
    
    # Wait for Redis
    if not wait_for_service("redis", 6379, "Redis"):
        print("Failed to connect to Redis. Exiting...")
        sys.exit(1)
    
    # Wait for RabbitMQ
    if not wait_for_service("rabbitmq", 5672, "RabbitMQ"):
        print("Failed to connect to RabbitMQ. Exiting...")
        sys.exit(1)
    
    print("All dependencies are ready. Starting GPS Service...")
    
    # Start the FastAPI application
    try:
        subprocess.run([
            "uvicorn", 
            "main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to start GPS Service: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
