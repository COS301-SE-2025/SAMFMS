# simulator_manager.py
from fastapi import FastAPI, Body
import docker

app = FastAPI()
client = docker.from_env()  

SIMULATOR_IMAGE = "simulation-image:latest"  # Build this image as described earlier

@app.post("/simulate_vehicle")
def simulate_vehicle(
    device_id: int = Body(...),
    start_latitude: float = Body(...),
    start_longitude: float = Body(...),
    speed: float = Body(...),
    interval: int = Body(5)
):
    container_name = f"simulator_{device_id}"
    # Remove existing container if exists
    try:
        old = client.containers.get(container_name)
        old.stop()
        old.remove()
    except docker.errors.NotFound:
        pass

    container = client.containers.run(
        SIMULATOR_IMAGE,
        command=[
            "--device", str(device_id),
            "--startLatitude", str(start_latitude),
            "--startLongitude", str(start_longitude),
            "--speed", str(speed),
            "--interval", str(interval),
            "--server", "traccar:5055"
        ],
        detach=True,
        name=container_name
    )
    return {"status": "started", "container_id": container.id}