# SAMFMS Test Suite

This directory contains the comprehensive test suite for the entire SAMFMS (Smart Autonomous Fleet Management System) project.

## Quick Start

### Windows (Recommended)

```cmd
# Run all tests
run-tests.bat

# Run tests for specific service
run-tests.bat --service security
run-tests.bat --service core

# Run specific test types
run-tests.bat --unit
run-tests.bat --integration
run-tests.bat --coverage
```

### PowerShell

```powershell
# Run all tests
.\run-tests.ps1

# Run tests for specific service
.\run-tests.ps1 -Service security
.\run-tests.ps1 -Service core

# Run specific test types
.\run-tests.ps1 -Unit
.\run-tests.ps1 -Integration -Coverage
```

### Using Make (if available)

```bash
# Show available commands
make help

# Run tests
make test              # All tests
make test-security     # Security service only
make test-core         # Core service only
make test-unit         # Unit tests only
make test-integration  # Integration tests only
make test-coverage     # With coverage reports
```

## Services Available for Testing

### 🔐 Security Service

- **Location**: `Sblocks/security/`
- **Tests**: Authentication, authorization, user management, invitations
- **Test Types**: Unit and integration tests
- **Coverage**: Auth utilities, services, repositories, API routes

### ⚙️ Core Service

- **Location**: `Core/`
- **Tests**: Core functionality and database operations
- **Test Types**: Integration tests with MongoDB and RabbitMQ

## Test Commands Reference

### Full Command Options

```cmd
run-tests.bat [OPTIONS]

Options:
  --service SERVICE    Run tests for specific service (security, core, all)
  --unit              Run only unit tests
  --integration       Run only integration tests
  --coverage          Generate coverage reports
  --verbose           Verbose output
  --help              Show help message

Examples:
  run-tests.bat                          # Run all tests for all services
  run-tests.bat --service security       # Run all security tests
  run-tests.bat --service security --unit # Run security unit tests only
  run-tests.bat --coverage               # Run all tests with coverage
```

### PowerShell Parameters

```powershell
.\run-tests.ps1 [PARAMETERS]

Parameters:
  -Service SERVICE     Run tests for specific service (security, core, all)
  -Unit               Run only unit tests
  -Integration        Run only integration tests
  -Coverage           Generate coverage reports
  -Verbose            Verbose output
  -Help               Show help message
```

## Test Infrastructure

### Docker Compose Services

- **mongo**: MongoDB 7 for database testing
- **rabbitmq**: RabbitMQ 3 with management for message queue testing
- **redis**: Redis 7 for caching and session testing
- **security-test**: Security service test container
- **mcore**: Core service test container

### Test Reports

Test reports are generated in service-specific directories:

- **Security**: `Sblocks/security/test-reports/`
  - `coverage.xml`: Coverage report in XML format
  - `htmlcov/`: HTML coverage report
  - `junit.xml`: JUnit test results

### Health Checks

All services include health checks to ensure dependencies are ready before running tests:

- MongoDB: Connection and ping test
- RabbitMQ: Port connectivity check
- Redis: Ping command

## Service-Specific Testing

### Security Service Tests

```cmd
# From root
run-tests.bat --service security

# From security directory
cd Sblocks\security
run-tests.bat
```

**Test Structure:**

- `tests/unit/`: Isolated component tests
- `tests/integration/`: API endpoint tests
- `tests/fixtures/`: Test data and fixtures

**Coverage:**

- Authentication utilities
- User service and repository
- Invitation service
- Auth service
- API routes (auth, user, admin)

### Core Service Tests

```cmd
# From root
run-tests.bat --service core

# Direct docker-compose
docker-compose -f docker-compose.test.yml up --abort-on-container-exit mcore
```

## Development Workflow

### Adding New Tests

1. **For Security Service:**

   ```cmd
   cd Sblocks\security\tests
   # Add test files following the pattern test_*.py
   ```

2. **For Core Service:**
   ```cmd
   cd Core\tests
   # Add test files in the appropriate structure
   ```

### Running Tests During Development

```cmd
# Quick security test run
run-tests.bat --service security --unit

# Full test suite with coverage
run-tests.bat --coverage

# Verbose output for debugging
run-tests.bat --verbose
```

### Test Environment Management

```cmd
# Build fresh test environment
docker-compose -f docker-compose.test.yml build

# Clean up everything
docker-compose -f docker-compose.test.yml down --volumes --remove-orphans

# View logs
docker-compose -f docker-compose.test.yml logs security-test
```

## Troubleshooting

### Common Issues

1. **Docker not running**

   ```
   Error: Docker is not running or not installed
   Solution: Start Docker Desktop
   ```

2. **Port conflicts**

   ```
   Error: Port already in use
   Solution: Stop conflicting services or change ports in docker-compose.test.yml
   ```

3. **Permission issues**

   ```
   Error: Permission denied
   Solution: Run as Administrator on Windows
   ```

4. **Test failures**
   ```
   Solution: Check logs with --verbose flag
   ```

### Debugging Tests

```cmd
# Run with verbose output
run-tests.bat --verbose

# Run specific test file
docker-compose -f docker-compose.test.yml run --rm security-test python -m pytest tests/unit/test_user_service.py -v

# Access test container for debugging
docker-compose -f docker-compose.test.yml run --rm security-test bash
```

### Log Access

```cmd
# View all service logs
docker-compose -f docker-compose.test.yml logs

# View specific service logs
docker-compose -f docker-compose.test.yml logs security-test
docker-compose -f docker-compose.test.yml logs mongo
```

## CI/CD Integration

The test suite is designed to work in CI/CD pipelines:

```yaml
# Example GitHub Actions step
- name: Run SAMFMS Tests
  run: |
    .\run-tests.bat --coverage

- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    files: ./Sblocks/security/test-reports/coverage.xml
```

## Performance Notes

- **Full test suite**: ~2-5 minutes depending on system
- **Security tests only**: ~1-2 minutes
- **Unit tests only**: ~30 seconds
- **Integration tests**: ~1-3 minutes (includes container startup)

## Next Steps

1. **Expand test coverage** for additional services (GPS, Vehicles, Users, etc.)
2. **Add performance tests** for high-load scenarios
3. **Implement end-to-end tests** across multiple services
4. **Add automated security scanning** in test pipeline
