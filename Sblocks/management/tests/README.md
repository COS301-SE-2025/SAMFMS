# Management Service Testing Guide

This document provides comprehensive information about the testing infrastructure for the Management service block.

## Test Structure

```
tests/
├── conftest.py              # Shared test configuration and fixtures
├── pytest.ini              # Pytest configuration
├── unit/                    # Unit tests
│   ├── test_vehicle_service.py      # VehicleService unit tests
│   ├── test_vehicle_repository.py   # VehicleRepository unit tests
│   └── test_schemas.py              # Schema validation tests
├── integration/             # Integration tests
│   ├── test_vehicle_api.py          # Vehicle API endpoint tests
│   └── test_service_integration.py  # Service layer integration tests
└── fixtures/                # Test data fixtures
    └── sample_data.py       # Sample test data
```

## Test Categories

### Unit Tests

- **Marker**: `@pytest.mark.unit`
- **Purpose**: Test individual components in isolation
- **Features**: Mocked dependencies, fast execution, high coverage

### Integration Tests

- **Marker**: `@pytest.mark.integration`
- **Purpose**: Test component interactions and API endpoints
- **Features**: Real service interactions (with mocked external dependencies)

### Vehicle Tests

- **Marker**: `@pytest.mark.vehicle`
- **Purpose**: All vehicle-related functionality
- **Features**: Cross-cutting tests for vehicle operations

## Running Tests

### Prerequisites

1. **Install test dependencies**:

   ```bash
   pip install pytest pytest-asyncio httpx factory-boy
   ```

2. **Set up test environment**:
   ```bash
   # Copy environment file for testing
   cp .env.example .env.test
   ```

### Using the Test Runner

The `run_tests.py` script provides convenient commands for running tests:

```bash
# Run all tests
python run_tests.py

# Run only unit tests
python run_tests.py --unit

# Run only integration tests
python run_tests.py --integration

# Run vehicle-related tests only
python run_tests.py --vehicle

# Run tests with coverage report
python run_tests.py --coverage

# Run specific test file
python run_tests.py --file test_vehicle_service.py

# Run specific test function
python run_tests.py --file test_vehicle_service.py --test test_create_vehicle_success

# Verbose output
python run_tests.py --verbose

# List available test markers
python run_tests.py --markers
```

### Direct Pytest Commands

```bash
# Run all tests
pytest

# Run unit tests only
pytest -m unit

# Run integration tests only
pytest -m integration

# Run vehicle tests only
pytest -m vehicle

# Run with coverage
pytest --cov=. --cov-report=html --cov-report=term

# Run specific test file
pytest tests/unit/test_vehicle_service.py

# Run specific test function
pytest tests/unit/test_vehicle_service.py::TestVehicleService::test_create_vehicle_success

# Verbose output
pytest -v

# Stop on first failure
pytest -x

# Run tests in parallel (requires pytest-xdist)
pytest -n auto
```

## Test Configuration

### Pytest Configuration (`pytest.ini`)

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --tb=short
    --strict-markers
    --disable-warnings
asyncio_mode = auto
markers =
    unit: Unit tests
    integration: Integration tests
    vehicle: Vehicle-related tests
    slow: Slow running tests
    database: Tests requiring database
```

### Test Fixtures (`conftest.py`)

Key fixtures available in all tests:

- **`mock_mongodb`**: Mocked MongoDB database
- **`mock_rabbitmq`**: Mocked RabbitMQ connection
- **`mock_redis`**: Mocked Redis connection
- **`sample_vehicle_data`**: Sample vehicle data for testing
- **`vehicle_factory`**: Factory for creating test vehicles

## Writing Tests

### Unit Test Example

```python
import pytest
from unittest.mock import AsyncMock, patch
from services.vehicle_service import VehicleService

@pytest.mark.unit
@pytest.mark.vehicle
class TestVehicleService:

    @pytest.mark.asyncio
    async def test_create_vehicle_success(self, sample_vehicle_data):
        """Test successful vehicle creation"""
        with patch('repositories.repositories.VehicleRepository') as mock_repo:
            # Arrange
            mock_repo.return_value.create.return_value = "vehicle_id_123"
            service = VehicleService()

            # Act
            result = await service.create_vehicle(sample_vehicle_data)

            # Assert
            assert result == "vehicle_id_123"
            mock_repo.return_value.create.assert_called_once()
```

### Integration Test Example

```python
import pytest
from httpx import AsyncClient
from main import app

@pytest.mark.integration
@pytest.mark.vehicle
class TestVehicleAPI:

    @pytest.fixture
    async def client(self):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    @pytest.mark.asyncio
    async def test_create_vehicle_endpoint(self, client, valid_vehicle_payload):
        """Test vehicle creation endpoint"""
        response = await client.post("/api/vehicles/", json=valid_vehicle_payload)
        assert response.status_code == 201
        assert "id" in response.json()
```

## Test Data Management

### Using Factories

```python
from tests.conftest import VehicleFactory

# Create a vehicle with default values
vehicle = VehicleFactory()

# Create a vehicle with custom values
vehicle = VehicleFactory(
    registration_number="ABC123GP",
    make="Toyota",
    model="Corolla"
)

# Create multiple vehicles
vehicles = VehicleFactory.create_batch(5)
```

### Sample Data

Sample data is available through fixtures:

```python
def test_example(sample_vehicle_data):
    # sample_vehicle_data contains a realistic vehicle object
    assert sample_vehicle_data["make"] == "Toyota"
```

## Mocking External Dependencies

### Database Mocking

```python
@pytest.mark.asyncio
async def test_with_database(mock_mongodb):
    # mock_mongodb is automatically injected
    mock_mongodb.vehicles.find_one.return_value = {"_id": "123"}

    # Your test code here
    result = await some_function()

    # Verify database calls
    mock_mongodb.vehicles.find_one.assert_called_once()
```

### RabbitMQ Mocking

```python
@pytest.mark.asyncio
async def test_with_rabbitmq(mock_rabbitmq):
    # mock_rabbitmq provides mocked connection and channel
    mock_rabbitmq.channel.basic_publish.return_value = True

    # Your test code here
    await publish_message("test")

    # Verify message publishing
    mock_rabbitmq.channel.basic_publish.assert_called_once()
```

## Coverage Reports

### Generating Coverage Reports

```bash
# Run tests with coverage
pytest --cov=. --cov-report=html --cov-report=term

# View HTML coverage report
# Open htmlcov/index.html in browser
```

### Coverage Configuration

Coverage is configured to:

- Include all Python files in the project
- Exclude test files from coverage calculation
- Generate both terminal and HTML reports
- Fail if coverage drops below 80%

## Best Practices

### Test Organization

1. **Group related tests in classes**
2. **Use descriptive test names**
3. **Follow AAA pattern**: Arrange, Act, Assert
4. **One assertion per test when possible**
5. **Use fixtures for common setup**

### Async Testing

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result is not None
```

### Parameterized Tests

```python
@pytest.mark.parametrize("input,expected", [
    ("gasoline", "petrol"),
    ("gas", "petrol"),
    ("petrol", "petrol"),
])
def test_fuel_type_normalization(input, expected):
    result = normalize_fuel_type(input)
    assert result == expected
```

### Testing Exceptions

```python
def test_invalid_vehicle_raises_error():
    with pytest.raises(ValueError, match="Invalid vehicle data"):
        validate_vehicle({})
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio httpx factory-boy
      - name: Run tests
        run: python run_tests.py --coverage
```

## Troubleshooting

### Common Issues

1. **Import Errors**

   ```bash
   # Ensure PYTHONPATH includes the project root
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   ```

2. **Async Test Issues**

   ```python
   # Make sure to use pytest.mark.asyncio
   @pytest.mark.asyncio
   async def test_async_function():
       pass
   ```

3. **Mock Issues**
   ```python
   # Use patch with correct path
   with patch('services.vehicle_service.VehicleRepository') as mock:
       pass
   ```

### Debug Mode

```bash
# Run tests with debugging
pytest --pdb

# Drop into debugger on first failure
pytest --pdb -x
```

## Test Metrics

Target metrics for test coverage:

- **Overall Coverage**: >80%
- **Service Layer**: >90%
- **Repository Layer**: >85%
- **API Endpoints**: >85%

Current test statistics:

- Unit tests: 25+ test cases
- Integration tests: 15+ test cases
- Total coverage: ~85%

## Contributing

When adding new functionality:

1. **Write tests first** (TDD approach)
2. **Maintain coverage targets**
3. **Add appropriate markers**
4. **Update this documentation**
5. **Run full test suite before committing**

### Test Checklist

- [ ] Unit tests for business logic
- [ ] Integration tests for API endpoints
- [ ] Error case coverage
- [ ] Edge case validation
- [ ] Performance considerations
- [ ] Documentation updates
