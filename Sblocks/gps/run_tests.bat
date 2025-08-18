@echo off
REM GPS Service Test Runner for Windows

echo 🧪 Running GPS Service Tests...

REM Set environment variables for testing
set MONGODB_URL=mongodb://localhost:27017
set DATABASE_NAME=test_samfms_gps
set RABBITMQ_URL=amqp://guest:guest@localhost:5672/

REM Install test dependencies
echo 📦 Installing test dependencies...
pip install pytest pytest-asyncio pytest-cov

REM Run tests with coverage
echo 🔬 Running tests with coverage...
pytest tests/ -v --cov=. --cov-report=html --cov-report=term

echo ✅ Tests completed. Coverage report available in htmlcov/
pause
