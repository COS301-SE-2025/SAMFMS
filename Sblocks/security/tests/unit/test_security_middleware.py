import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from middleware.security_middleware import SecurityHeadersMiddleware, CORSMiddleware  # Update import path

# Test app setup
app = FastAPI()

@app.get("/test")
@pytest.mark.asyncio
async def test_route(request: Request):
    return {"message": "test"}

# Tests for SecurityHeadersMiddleware
def test_security_headers_middleware():
    # Add middleware
    app.add_middleware(SecurityHeadersMiddleware)
    client = TestClient(app)
    
    response = client.get("/test")
    
    # Verify security headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-XSS-Protection"] == "1; mode=block"
    assert response.headers["Strict-Transport-Security"] == "max-age=31536000; includeSubDomains"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert response.headers["Content-Security-Policy"] == "default-src 'self'"

# Tests for CORSMiddleware
@pytest.fixture
def cors_app():
    app = FastAPI()
    app.add_middleware(CORSMiddleware, allowed_origins=["https://allowed.com"])
    
    @app.get("/test")
    async def test_route():
        return {"message": "test"}
    
    return TestClient(app)

def test_cors_preflight_request(cors_app):
    # Preflight request
    headers = {
        "Origin": "https://allowed.com",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "Authorization"
    }
    response = cors_app.options("/test", headers=headers)
    
    # Verify CORS headers
    assert response.headers["Access-Control-Allow-Origin"] == "*"
    assert response.headers["Access-Control-Allow-Methods"] == "GET, POST, PUT, DELETE, OPTIONS"
    assert response.headers["Access-Control-Allow-Headers"] == "Authorization, Content-Type"
    assert response.status_code == 200

def test_cors_allowed_origin(cors_app):
    # Regular request with allowed origin
    response = cors_app.get("/test", headers={"Origin": "https://allowed.com"})
    
    assert response.headers["Access-Control-Allow-Origin"] == "https://allowed.com"
    assert response.headers["Access-Control-Allow-Credentials"] == "true"
    assert response.headers["Access-Control-Allow-Methods"] == "GET, POST, PUT, DELETE, OPTIONS"
    assert response.headers["Access-Control-Allow-Headers"] == "Authorization, Content-Type"

def test_cors_disallowed_origin(cors_app):
    # Regular request with disallowed origin
    response = cors_app.get("/test", headers={"Origin": "https://disallowed.com"})
    
    # Should not have CORS headers except Allow-Credentials
    assert "Access-Control-Allow-Origin" not in response.headers
    assert response.headers["Access-Control-Allow-Credentials"] == "true"

def test_cors_wildcard_origin():
    # Test with wildcard allowed origin
    app = FastAPI()
    app.add_middleware(CORSMiddleware, allowed_origins=["*"])
    
    @app.get("/test")
    async def test_route():
        return {"message": "test"}
    
    client = TestClient(app)
    response = client.get("/test", headers={"Origin": "https://any-domain.com"})
    
    assert response.headers["Access-Control-Allow-Origin"] == "https://any-domain.com"

def test_cors_credentials_header(cors_app):
    # Verify credentials header exists in all responses
    response = cors_app.get("/test")
    assert response.headers["Access-Control-Allow-Credentials"] == "true"
    
    # Even for disallowed origins
    response = cors_app.get("/test", headers={"Origin": "https://disallowed.com"})
    assert response.headers["Access-Control-Allow-Credentials"] == "true"