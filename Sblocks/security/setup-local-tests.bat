@echo off
REM Quick setup script for local development testing
echo Setting up local test environment...

REM Install test dependencies
echo Installing test dependencies...
pip install pytest pytest-asyncio pytest-mock pytest-cov httpx fakeredis mongomock

echo.
echo Local test environment setup complete!
echo.
echo To run tests locally:
echo   python -m pytest
echo   python -m pytest tests/unit/
echo   python -m pytest tests/integration/
echo   python -m pytest --cov=. --cov-report=html
echo.
echo Note: Integration tests may require actual database connections.
echo For fully isolated testing, use: run-tests.bat
echo.
pause
