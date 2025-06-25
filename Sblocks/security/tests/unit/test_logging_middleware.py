import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from fastapi.exceptions import HTTPException
import logging
from datetime import datetime
import uuid
from middleware.logging_middleware import LoggingMiddleware

app = FastAPI()

@app.get("/success")
async def success_route(request: Request):
    return {"message": "success"}

@app.get("/http-error")
async def http_error_route():
    raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/unhandled-error")
async def unhandled_error_route():
    raise ValueError("Something went wrong")

app.add_middleware(LoggingMiddleware)

client = TestClient(app)

def test_request_id_header(caplog):
    caplog.set_level(logging.INFO)
    response = client.get("/success")
    assert "X-Request-ID" in response.headers
    assert "X-Process-Time" in response.headers
    assert uuid.UUID(response.headers["X-Request-ID"], version=4)

def test_successful_request_logging(caplog):
    caplog.set_level(logging.INFO)
    response = client.get("/success")
    
    incoming_log = next(r for r in caplog.records if r.message == "Incoming request")
    completed_log = next(r for r in caplog.records if r.message == "Request completed")

    assert incoming_log.method == "GET"
    assert "/success" in incoming_log.url
    assert completed_log.status_code == 200
    assert completed_log.process_time_ms >= 0


def test_unhandled_error_logging(caplog):
    caplog.set_level(logging.ERROR)
    
    with pytest.raises(ValueError):
        client.get("/unhandled-error")
    
    error_log = caplog.records[0]
    assert error_log.message == "Request failed"
    assert "Something went wrong" in error_log.error
    assert error_log.process_time_ms >= 0

def test_log_structure(caplog):
    caplog.set_level(logging.INFO)
    client.get("/success")
    
    incoming_log = next(r for r in caplog.records if r.message == "Incoming request")
    assert hasattr(incoming_log, "request_id")
    assert hasattr(incoming_log, "ip_address")
    assert hasattr(incoming_log, "user_agent")
    assert hasattr(incoming_log, "timestamp")
    
    datetime.fromisoformat(incoming_log.timestamp.replace("Z", "+00:00"))