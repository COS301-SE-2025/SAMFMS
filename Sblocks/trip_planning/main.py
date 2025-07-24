from fastapi import FastAPI

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    """Initialize Trip Planning service on startup"""
    try:
        await trip_planning_request_handler.initialize()
        print("Trip Planning service request handler initialized")
    except Exception as e:
        print(f"Trip Planning service request handler initialization failed: {e}")
    publish_message("service_presence", aio_pika.ExchangeType.FANOUT, {"type": "service_presence", "service":"trip_planning"}, "")


@app.get("/")
def read_root():
    return {"message": "Hello from Trip Planning Service"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "trip_planning"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
