# Security Service Testing

This directory contains the test suite for the Security Service.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Common test fixtures and configuration
├── fixtures/
│   ├── __init__.py
│   └── sample_data.py       # Sample data fixtures
├── unit/                    # Unit tests
│   ├── __init__.py
│   ├── test_auth_service.py
│   ├── test_auth_utils.py
│   ├── test_invitation_service.py
│   ├── test_user_repository.py
│   └── test_user_service.py
└── integration/             # Integration tests
    ├── __init__.py
    ├── test_admin_routes.py
    ├── test_auth_routes.py
    └── test_user_routes.py
```

## Running Tests

### Windows (Recommended)

```cmd
# Run all tests
run-tests.bat

# Run only unit tests
run-tests.bat --unit

# Run only integration tests
run-tests.bat --integration

# Run with coverage report
run-tests.bat --coverage

# Verbose output
run-tests.bat --verbose
```

### Linux/Mac

```bash
# Run all tests
./run-tests.sh

# Run specific test types
./run-tests.sh --unit
./run-tests.sh --integration
./run-tests.sh --coverage
```

### Direct Docker Commands

```bash
# Build and run tests
docker-compose -f docker-compose.test.yml build
docker-compose -f docker-compose.test.yml up --abort-on-container-exit

# Run specific test files
docker-compose -f docker-compose.test.yml run --rm security-test python -m pytest tests/unit/test_user_service.py -v
```

### Local Development (without Docker)

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests locally
python -m pytest
python -m pytest tests/unit/
python -m pytest tests/integration/
python -m pytest --cov=. --cov-report=html
```

## Test Configuration

- **pytest.ini**: Main pytest configuration
- **conftest.py**: Shared fixtures and test setup
- **docker-compose.test.yml**: Test environment with MongoDB, Redis, and RabbitMQ
- **Dockerfile.test**: Test container configuration

## Test Features

- **Async Support**: Full async/await support with pytest-asyncio
- **Mocking**: Comprehensive mocking of external dependencies
- **Coverage**: Code coverage reporting with pytest-cov
- **Database**: Mock MongoDB with mongomock
- **Redis**: Mock Redis with fakeredis
- **Isolation**: Each test runs in isolation with fresh fixtures

## Test Types

### Unit Tests

- Test individual functions and classes in isolation
- Mock all external dependencies
- Fast execution
- Located in `tests/unit/`

### Integration Tests

- Test API endpoints and service interactions
- Use test containers for dependencies
- Slower execution but more comprehensive
- Located in `tests/integration/`

## Adding New Tests

1. Create test files following the naming convention `test_*.py`
2. Use appropriate fixtures from `conftest.py`
3. Mark tests with appropriate markers:
   - `@pytest.mark.unit` for unit tests
   - `@pytest.mark.integration` for integration tests
   - `@pytest.mark.asyncio` for async tests
   - `@pytest.mark.slow` for slow tests

## Example Test

```python
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
@pytest.mark.unit
async def test_user_service_get_user(mock_user_repository, test_user_data):
    \"\"\"Test getting a user by ID.\"\"\"
    mock_user_repository.find_by_id.return_value = test_user_data

    result = await UserService.get_user_by_id(test_user_data["user_id"])

    assert result["user_id"] == test_user_data["user_id"]
    mock_user_repository.find_by_id.assert_called_once()
```

## Troubleshooting

### Docker Issues

- Ensure Docker Desktop is running
- Try `docker system prune` to clean up
- Check `docker-compose logs` for errors

### Permission Issues on Windows

- Run Command Prompt as Administrator
- Ensure Docker Desktop has proper permissions

### Import Issues

- Verify PYTHONPATH is set correctly
- Check all **init**.py files exist
- Ensure module paths are correct
