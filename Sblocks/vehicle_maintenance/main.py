from fastapi import FastAPI
from service_request_handler import maintenance_request_handler

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    """Initialize Vehicle Maintenance service on startup"""
    try:
        await maintenance_request_handler.initialize()
        print("Maintenance service request handler initialized")
    except Exception as e:
        print(f"Maintenance service request handler initialization failed: {e}")
    
    publish_message("service_presence", aio_pika.ExchangeType.FANOUT, {"type": "service_presence", "service":"vehicle_maintenance"}, "")


@app.get("/")
def read_root():
    return {"message": "Hello from Vehicle Maintenance Service"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "vehicle_maintenance"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
