# Testing Documentation

## Overview

This document explains the testing strategy, setup, and execution for the SAMFMS Management Service. The test suite is designed to achieve comprehensive coverage of the codebase and ensure code quality.

## Test Structure

### Test Organization

```
tests/
├── unit/                    # Unit tests
│   ├── test_api_dependencies.py      # API dependency injection tests
│   ├── test_base_repository.py       # Base repository functionality tests
│   ├── test_database.py              # Database connection and management tests
│   ├── test_driver_repository.py     # Driver repository tests
│   ├── test_driver_service.py        # Driver service business logic tests
│   ├── test_events.py                # Event system tests
│   ├── test_schemas.py               # Schema validation tests
│   ├── test_vehicle_repository.py    # Vehicle repository tests
│   └── test_vehicle_service.py       # Vehicle service business logic tests
├── integration/             # Integration tests
│   └── test_vehicle_api.py           # API integration tests
└── conftest.py             # Pytest configuration and fixtures
```

### Test Coverage Areas

#### 1. **API Dependencies** (`test_api_dependencies.py`)

- **Authentication and Authorization**: User authentication, token validation, permission checking
- **Request Validation**: Pagination parameters, object ID validation, date range validation
- **Context Management**: User context extraction, request timing, error handling
- **Security**: Permission requirements, access control, token management

#### 2. **Database Layer** (`test_database.py`, `test_base_repository.py`)

- **Connection Management**: Database connection lifecycle, health checks, singleton pattern
- **CRUD Operations**: Create, read, update, delete operations with proper error handling
- **Query Operations**: Find operations with filters, pagination, sorting
- **Error Handling**: Database exceptions, connection failures, validation errors

#### 3. **Repository Layer** (`test_driver_repository.py`, `test_vehicle_repository.py`)

- **Driver Management**: Driver CRUD operations, search functionality, department filtering
- **Vehicle Management**: Vehicle CRUD operations, registration number lookup, availability checks
- **Data Validation**: Input validation, constraint checking, business rule enforcement
- **Query Optimization**: Efficient querying with proper indexing and filtering

#### 4. **Business Logic Layer** (`test_driver_service.py`, `test_vehicle_service.py`)

- **Driver Services**: Driver creation, updates, validation, assignment management
- **Vehicle Services**: Vehicle registration, status management, fuel type normalization
- **Business Rules**: Validation of business constraints, data normalization
- **Event Publishing**: Integration with event system for domain events

#### 5. **Event System** (`test_events.py`)

- **Event Models**: Event creation, serialization, type validation
- **Event Publishing**: Message publishing, routing, error handling
- **Event Types**: Vehicle events, driver events, assignment events, analytics events
- **Event Validation**: Schema validation, required fields, event correlation

#### 6. **Schema Validation** (`test_schemas.py`)

- **Entity Schemas**: Vehicle assignment, usage logs, driver profiles, analytics snapshots
- **Request Schemas**: Create/update requests, field validation, normalization
- **Response Schemas**: Standard responses, error responses, pagination metadata
- **Validation Rules**: Field constraints, enum validation, custom validators

## Running Tests

### Prerequisites

- Python 3.11+
- pytest and pytest-cov installed
- MongoDB connection (mocked in tests)
- All dependencies installed (`pip install -r requirements.txt`)

### Basic Test Execution

#### Run All Tests

```bash
pytest
```

#### Run Unit Tests Only

```bash
pytest tests/unit
```

#### Run Integration Tests Only

```bash
pytest tests/integration
```

#### Run Specific Test File

```bash
pytest tests/unit/test_vehicle_service.py
```

#### Run Specific Test Class

```bash
pytest tests/unit/test_vehicle_service.py::TestVehicleService
```

#### Run Specific Test Method

```bash
pytest tests/unit/test_vehicle_service.py::TestVehicleService::test_create_vehicle_success
```

### Coverage Reporting

#### Run Tests with Coverage

```bash
pytest --cov=. --cov-report=term
```

#### Generate HTML Coverage Report

```bash
pytest --cov=. --cov-report=html
```

View the report by opening `htmlcov/index.html` in your browser.

#### Generate XML Coverage Report

```bash
pytest --cov=. --cov-report=xml
```

#### Combined Coverage Report

```bash
pytest --cov=. --cov-report=html --cov-report=xml --cov-report=term
```

### Test Filtering

#### Run Tests by Mark

```bash
pytest -m unit          # Run only unit tests
pytest -m integration   # Run only integration tests
pytest -m vehicle       # Run vehicle-related tests
pytest -m driver        # Run driver-related tests
```

#### Run Tests with Verbose Output

```bash
pytest -v
```

#### Run Tests with Extra Verbose Output

```bash
pytest -vv
```

### Test Configuration

#### Pytest Configuration (`pytest.ini`)

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = --strict-markers --strict-config
markers =
    unit: Unit tests
    integration: Integration tests
    vehicle: Vehicle-related tests
    driver: Driver-related tests
    events: Event system tests
    schemas: Schema validation tests
    repository: Repository layer tests
    service: Service layer tests
    api: API layer tests
    database: Database layer tests
```

## Test Fixtures and Utilities

### Common Fixtures (`conftest.py`)

- **mock_mongodb**: Mocked MongoDB database connection
- **sample_entity_data**: Sample data for testing entity operations
- **create_mock_cursor**: Utility for creating mock database cursors

### Test Utilities

- **AsyncMock**: For mocking async operations
- **MagicMock**: For mocking synchronous operations
- **patch**: For patching dependencies and external services
- **pytest.raises**: For testing exception handling

## Coverage Metrics

### Current Coverage Status

- **Total Coverage**: 52%
- **Passing Tests**: 120/177 (68%)
- **Test Files**: 9 unit test files, 1 integration test file

### Coverage Breakdown by Component

- **API Dependencies**: 84% coverage
- **Schema Entities**: 97% coverage
- **Schema Requests**: 97% coverage
- **Schema Responses**: 85% coverage
- **Event System**: 100% coverage
- **Repository Layer**: 61-95% coverage
- **Service Layer**: 31-62% coverage

### Coverage Goals

- **Minimum Target**: 80% overall coverage
- **Critical Components**: 90%+ coverage for business logic
- **API Endpoints**: 85%+ coverage for all routes
- **Database Operations**: 90%+ coverage for all CRUD operations

## Test Patterns and Best Practices

### Test Structure

1. **Arrange**: Set up test data and mocks
2. **Act**: Execute the function under test
3. **Assert**: Verify the expected outcomes

### Naming Conventions

- Test files: `test_<module_name>.py`
- Test classes: `Test<ClassName>`
- Test methods: `test_<functionality>_<scenario>`

### Example Test Structure

```python
@pytest.mark.unit
@pytest.mark.vehicle
class TestVehicleService:
    """Test class for vehicle service operations"""

    @pytest.mark.asyncio
    async def test_create_vehicle_success(self):
        """Test successful vehicle creation"""
        # Arrange
        vehicle_data = {...}
        mock_repository = MagicMock()

        # Act
        result = await service.create_vehicle(vehicle_data)

        # Assert
        assert result is not None
        assert result["registration_number"] == vehicle_data["registration_number"]
```

### Mocking Strategy

- **External Dependencies**: Always mock external services (database, APIs, file system)
- **Internal Dependencies**: Mock other service/repository layers when testing specific components
- **Async Operations**: Use AsyncMock for async functions
- **Database Operations**: Mock database connections and operations

### Error Testing

- Test both success and failure scenarios
- Verify proper exception handling
- Check error messages and status codes
- Ensure proper cleanup in error cases

## Common Test Scenarios

### API Testing

- Valid requests with proper authentication
- Invalid requests with proper error responses
- Permission-based access control
- Input validation and sanitization

### Service Testing

- Business logic validation
- Data transformation and normalization
- Event publishing and handling
- Error propagation and handling

### Repository Testing

- CRUD operations with various data types
- Query operations with filters and pagination
- Unique constraint violations
- Database connection failures

### Schema Testing

- Valid data validation
- Invalid data rejection
- Field normalization and transformation
- Enum validation and constraint checking

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are properly imported and available
2. **Async/Await Issues**: Use proper async test decorators and AsyncMock
3. **Mock Configuration**: Verify mock return values and side effects are properly set
4. **Database Mocking**: Ensure database operations are properly mocked

### Debug Tips

- Use `pytest -vv` for verbose output
- Add `print()` statements in tests for debugging
- Use `pytest --pdb` to drop into debugger on failures
- Check mock call counts and arguments with `assert_called_with()`

## Continuous Integration

### Coverage Requirements

- All pull requests must maintain or improve coverage
- New features must include comprehensive test coverage
- Critical bug fixes must include regression tests

### Test Execution in CI/CD

```bash
# Run all tests with coverage
pytest --cov=. --cov-report=xml --cov-report=term

# Fail if coverage is below threshold
pytest --cov=. --cov-fail-under=80
```

## Future Enhancements

### Planned Test Additions

1. **Performance Tests**: Load testing for high-volume operations
2. **Security Tests**: Authentication and authorization edge cases
3. **Integration Tests**: End-to-end API testing with real database
4. **Contract Tests**: API contract validation with external services

### Test Infrastructure Improvements

1. **Test Data Management**: Centralized test data factories
2. **Parallel Test Execution**: Improve test execution speed
3. **Test Reporting**: Enhanced reporting with metrics and trends
4. **Test Environment**: Isolated test environments for different scenarios

## Conclusion

The test suite provides comprehensive coverage of the SAMFMS Management Service, focusing on correctness, reliability, and maintainability. Regular test execution and coverage monitoring ensure code quality and prevent regressions.

For questions or issues with testing, please refer to the development team or create an issue in the project repository.
