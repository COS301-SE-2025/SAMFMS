import pytest
from fastapi import Request
from starlette.responses import Response
from starlette.datastructures import Headers
from ...middleware.logging_middleware import LoggingMiddleware
from ...middleware.logging_middleware import logger
from unittest.mock import patch
from datetime import datetime

@pytest.mark.asyncio
async def test_logging_middleware_logs_request_and_response_with_logging():
    mock_request = Request(scope={
        "type": "http",
        "method": "GET",
        "path": "/test",
        "headers": Headers({"user-agent": "test-agent"}).raw,
        "client": ("127.0.0.1", 12345),
    })
    mock_response = Response(status_code=200)

    async def mock_call_next(request):
        return mock_response

    middleware = LoggingMiddleware(app=None)

    with patch("security.middleware.logging_middleware.logger.info") as mock_logger_info:
        response = await middleware.dispatch(mock_request, mock_call_next)

        # Assertions for headers
        assert response.headers["X-Request-ID"] is not None
        assert response.headers["X-Process-Time"] is not None
        assert response.status_code == 200

        # Assertions for logging
        timestamp = datetime.utcnow().isoformat() + "Z"
        mock_logger_info.assert_any_call(
            "Incoming request",
            extra={
                "request_id": response.headers["X-Request-ID"],
                "method": "GET",
                "url": "http://testserver/test",
                "ip_address": "127.0.0.1",
                "user_agent": "test-agent",
                "timestamp": timestamp,  # Ensure timestamp is logged
            }
        )
        mock_logger_info.assert_any_call(
            "Request completed",
            extra={
                "request_id": response.headers["X-Request-ID"],
                "status_code": 200,
                "process_time_ms": float(response.headers["X-Process-Time"]),
                "ip_address": "127.0.0.1",
                "timestamp": timestamp,  # Ensure timestamp is logged
            }
        )