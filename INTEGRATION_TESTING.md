# SAMFMS Integration Testing

This directory contains comprehensive integration tests for the SAMFMS (Smart Automated Fleet Management System) that validate the communication between the React Frontend and FastAPI Core service, along with the complete microservices architecture.

## Overview

The integration testing suite covers:

- **Authentication Flow**: Login, token management, user session handling
- **Vehicle Management**: CRUD operations for vehicles through Frontend-Core communication
- **Driver Management**: Driver data management and API interactions
- **Analytics**: Dashboard data retrieval and analytics endpoints
- **Maintenance System**: Maintenance records and scheduling functionality
- **Service Communication**: Core-to-microservice communication via RabbitMQ
- **Error Handling**: Network failures, service unavailability, authentication issues

## Architecture

### Frontend-Core Communication Flow

```
React Frontend → Core API Gateway → Service Blocks (via RabbitMQ)
     ↑                ↓                      ↓
     ├─ Authentication (JWT)           Management Service
     ├─ HTTP REST APIs                 Maintenance Service  
     ├─ WebSocket connections          Trip Planning Service
     └─ Error handling                 GPS Service
```

### Test Architecture

```
├── Python Integration Tests (Backend)
│   └── tests/integration/test_frontend_core_integration.py
├── JavaScript Integration Tests (Frontend)
│   └── Frontend/samfms/src/__tests__/integration/
├── Docker Compose Environment
│   └── docker-compose.integration.yml
└── GitHub Actions Workflow
    └── .github/workflows/integration-tests.yml
```

## Quick Start

### 1. Run Integration Tests Locally

```bash
# Run all integration tests
./run-integration-tests.sh

# Run with logs output
./run-integration-tests.sh --logs

# Run only Python backend tests
./run-integration-tests.sh --python-only

# Run only Frontend tests
./run-integration-tests.sh --frontend-only

# Quick smoke tests (fast feedback)
./run-integration-tests.sh --quick
```

### 2. Run Tests in GitHub Actions

Tests automatically run on:
- Push to `main` or `development` branches
- Pull requests to `main` or `development`
- Manual workflow dispatch

## Test Configuration

### Environment Variables

#### Required
- `JWT_SECRET_KEY`: Secret key for JWT token generation (auto-generated if not provided)

#### Optional
- `CORE_URL`: Core service URL (default: `http://localhost:8001`)
- `FRONTEND_URL`: Frontend URL (default: `http://localhost:3001`)
- `NODE_ENV`: Node environment (default: `test`)
- `LOG_LEVEL`: Logging level (default: `INFO`)

### Test User Credentials

The integration tests use a dedicated test user:
- **Email**: `integration_test@samfms.co.za`
- **Password**: `IntegrationTest123!`
- **Role**: `fleet_manager`

This user is automatically created during test execution.

## Test Structure

### Python Integration Tests

Located in `tests/integration/test_frontend_core_integration.py`

**Test Classes:**
- `TestFrontendCoreIntegration`: Core communication flow tests
- `TestFrontendApiCompatibility`: API structure compatibility tests
- `TestServiceCommunication`: Inter-service communication tests

**Key Test Methods:**
```python
async def test_authentication_flow()           # Login/logout cycle
async def test_user_info_retrieval()          # User profile API
async def test_vehicle_api_endpoints()        # Vehicle CRUD operations
async def test_driver_api_endpoints()         # Driver management
async def test_analytics_endpoints()          # Dashboard analytics
async def test_maintenance_endpoints()        # Maintenance system
```

### Frontend Integration Tests

Located in `Frontend/samfms/src/__tests__/integration/frontend-core.test.js`

**Test Suites:**
- Authentication Flow
- Vehicle API Integration
- Driver API Integration
- Analytics API Integration
- API Configuration
- Error Handling

**Key Features:**
- Real HTTP requests to Core API
- Token management testing
- Response structure validation
- Graceful error handling
- Service availability detection

## Docker Integration Environment

### Services

The integration environment includes:

1. **Infrastructure Services**
   - MongoDB (port 27019)
   - RabbitMQ (ports 5674, 15674)
   - Redis (port 6381)

2. **Application Services**
   - Core API Service (port 8001)
   - Management Service
   - Maintenance Service
   - Trip Planning Service
   - Frontend Application (port 3001)

3. **Test Runner**
   - Combined Python/Node.js environment
   - Automated test execution
   - Result collection and reporting

### Docker Compose Commands

```bash
# Build integration environment
docker-compose -f docker-compose.integration.yml build

# Start infrastructure only
docker-compose -f docker-compose.integration.yml up -d mongodb-integration rabbitmq-integration redis-integration

# Start all services
docker-compose -f docker-compose.integration.yml up -d

# Run tests
docker-compose -f docker-compose.integration.yml run --rm integration-test-runner

# View logs
docker-compose -f docker-compose.integration.yml logs core-integration
docker-compose -f docker-compose.integration.yml logs frontend-integration

# Cleanup
docker-compose -f docker-compose.integration.yml down --volumes
```

## GitHub Actions Workflow

The integration test workflow (`.github/workflows/integration-tests.yml`) includes:

### Main Integration Tests Job
1. **Infrastructure Setup**: MongoDB, RabbitMQ, Redis
2. **Service Deployment**: Core, Management, Maintenance, Trips, Frontend
3. **Health Verification**: Service availability checks
4. **Test Execution**: Python and JavaScript integration tests
5. **Result Collection**: Logs, test reports, artifacts
6. **Cleanup**: Container and volume cleanup

### Quick Smoke Tests Job (PR only)
- Fast feedback for pull requests
- Frontend unit tests
- Python syntax validation
- Dependency resolution checks

### Workflow Features
- **Parallel execution** where possible
- **Comprehensive caching** for Docker layers and dependencies
- **Detailed reporting** with GitHub step summaries
- **Artifact collection** for debugging
- **Automatic cleanup** of resources

## Test Results and Reporting

### Local Test Results
- Python: JUnit XML in `test-results/integration-pytest.xml`
- Frontend: Jest coverage reports in `Frontend/samfms/coverage/`
- Logs: Service logs in `test-results/integration/`

### GitHub Actions Artifacts
- **integration-test-results-{run-id}**: Complete test results, logs, coverage
- **Test Summary**: Markdown summary in GitHub Actions UI
- **Service Status**: Container health and status information

## Troubleshooting

### Common Issues

1. **Services not starting**
   ```bash
   # Check service logs
   ./run-integration-tests.sh --logs --no-cleanup
   docker-compose -f docker-compose.integration.yml ps
   ```

2. **Authentication failures**
   - Check JWT_SECRET_KEY environment variable
   - Verify test user creation in logs
   - Check Core service authentication endpoints

3. **Port conflicts**
   ```bash
   # Check for port conflicts
   netstat -tlnp | grep ":8001\|:3001\|:27019\|:5674"
   
   # Stop conflicting services
   docker-compose -f docker-compose.yml down
   ```

4. **Network issues**
   ```bash
   # Reset Docker networks
   docker network prune -f
   docker-compose -f docker-compose.integration.yml down --volumes
   ```

### Debug Mode

```bash
# Keep containers running for investigation
./run-integration-tests.sh --no-cleanup

# Access Core API directly
curl http://localhost:8001/health
curl http://localhost:8001/docs

# Access Frontend
open http://localhost:3001

# Execute commands in containers
docker-compose -f docker-compose.integration.yml exec core-integration bash
docker-compose -f docker-compose.integration.yml exec frontend-integration sh
```

### Log Analysis

```bash
# Core service logs
docker-compose -f docker-compose.integration.yml logs -f core-integration

# Frontend build logs  
docker-compose -f docker-compose.integration.yml logs -f frontend-integration

# Management service logs
docker-compose -f docker-compose.integration.yml logs -f management-integration

# All service logs
docker-compose -f docker-compose.integration.yml logs -f
```

## Development Workflow

### Adding New Integration Tests

1. **Python Tests** (`tests/integration/test_frontend_core_integration.py`):
   ```python
   async def test_new_feature(self, auth_token):
       response = await IntegrationTestHelper.make_authenticated_request(
           "GET", "/api/new-endpoint", auth_token
       )
       assert response.status_code == 200
   ```

2. **Frontend Tests** (`Frontend/samfms/src/__tests__/integration/frontend-core.test.js`):
   ```javascript
   test('should handle new API feature', async () => {
       const result = await newApiFunction();
       expect(result).toBeDefined();
   });
   ```

### Updating Test Configuration

- **Service URLs**: Update `TEST_CONFIG` in test files
- **Docker Environment**: Modify `docker-compose.integration.yml`
- **GitHub Actions**: Update `.github/workflows/integration-tests.yml`

### Performance Considerations

- **Parallel Test Execution**: Tests run in parallel where possible
- **Resource Limits**: Docker containers have appropriate resource limits
- **Caching Strategy**: Aggressive caching for builds and dependencies
- **Timeout Management**: Appropriate timeouts for different operations

## Continuous Integration

### Branch Strategy
- **Main Branch**: Full integration tests on every push
- **Development Branch**: Full integration tests + additional validation
- **Feature Branches**: Smoke tests on pull requests
- **Release Branches**: Extended test suites with performance testing

### Quality Gates
1. All integration tests must pass
2. Service health checks must succeed
3. No critical authentication vulnerabilities
4. Frontend-backend compatibility verified
5. Error handling scenarios covered

## Monitoring and Alerting

The integration tests provide early detection of:
- **API Breaking Changes**: Incompatible API modifications
- **Authentication Issues**: Token management problems
- **Service Communication Failures**: RabbitMQ connectivity issues
- **Database Schema Changes**: MongoDB compatibility problems
- **Frontend Build Problems**: React compilation issues
- **Performance Regressions**: Slow API responses

## Contributing

When contributing to the integration test suite:

1. **Test Coverage**: Ensure new features have corresponding integration tests
2. **Error Scenarios**: Include negative test cases and error conditions
3. **Documentation**: Update this README for new test patterns
4. **Performance**: Consider test execution time and resource usage
5. **Compatibility**: Ensure tests work across different environments

## Security Considerations

- **Test Isolation**: Each test run uses fresh databases and clean environments
- **Credential Management**: Test credentials are isolated and rotated
- **Network Security**: Integration network is isolated from production
- **Data Privacy**: No real user data in integration tests
- **Secret Management**: Secrets are injected via environment variables

## Support

For issues with integration tests:
1. Check the troubleshooting section above
2. Review GitHub Actions workflow runs for detailed logs
3. Run tests locally with `--logs` flag for debugging
4. Check service-specific logs in the test results artifacts
5. Contact the development team with specific error messages and context