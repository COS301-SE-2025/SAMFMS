import pytest
from fastapi import Request
from starlette.responses import Response
from starlette.datastructures import Headers
from ...middleware.logging_middleware import LoggingMiddleware

@pytest.mark.asyncio
async def test_logging_middleware_logs_request_and_response():
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

    response = await middleware.dispatch(mock_request, mock_call_next)

    assert response.headers["X-Request-ID"] is not None
    assert response.headers["X-Process-Time"] is not None
    assert response.status_code == 200