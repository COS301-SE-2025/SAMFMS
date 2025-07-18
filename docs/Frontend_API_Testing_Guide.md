# Frontend API Testing Documentation

## Overview

This document describes the comprehensive testing infrastructure for the SAMFMS Frontend API layer. The testing framework includes unit tests, integration tests, and container-based testing with coverage reporting.

## Test Structure

```
Frontend/samfms/src/__tests__/
├── api/
│   ├── setup.js              # Test setup and configuration
│   ├── auth.test.js          # Authentication API tests
│   ├── vehicles.test.js      # Vehicle management API tests
│   ├── drivers.test.js       # Driver management API tests
│   ├── maintenance.test.js   # Maintenance API tests
│   ├── assignments.test.js   # Assignment API tests
│   └── integration.test.js   # Container integration tests
├── components/               # Component tests (existing)
└── utils/                   # Utility function tests
```

## Test Categories

### 1. **Unit Tests**

- Test individual API functions in isolation
- Mock external dependencies (fetch, cookies, etc.)
- Focus on function logic and error handling
- Run without requiring backend services

### 2. **Integration Tests**

- Test API functions with running backend containers
- Verify actual HTTP communication
- Test end-to-end workflows
- Require Docker containers to be running

### 3. **Coverage Tests**

- Measure code coverage for API functions
- Generate HTML and LCOV reports
- Enforce coverage thresholds (70% minimum)

## Running Tests

### Prerequisites

1. **Node.js Dependencies**:

   ```bash
   cd Frontend/samfms
   npm install
   ```

2. **Backend Containers** (for integration tests):

   ```bash
   # Start backend containers
   docker-compose -f docker-compose.test-enhanced.yml up -d

   # Verify services are running
   curl http://localhost:8004/health  # Core service
   curl http://localhost:8001/health  # Security service
   curl http://localhost:8002/health  # Management service
   curl http://localhost:8003/health  # Maintenance service
   ```

### Test Commands

#### **Quick Test Scripts**

**Linux/macOS:**

```bash
# Run all frontend API tests
./run-frontend-tests.sh

# Run with custom coverage threshold
./run-frontend-tests.sh --coverage-threshold=80
```

**Windows:**

```powershell
# Run all frontend API tests
.\run-frontend-tests.ps1

# Run with custom parameters
.\run-frontend-tests.ps1 -CoverageThreshold 80 -Timeout 180
```

#### **Manual Test Commands**

```bash
cd Frontend/samfms

# Run all API tests
npm test -- --testPathPattern="__tests__/api"

# Run specific test file
npm test -- auth.test.js

# Run unit tests only (exclude integration)
npm test -- --testPathPattern="__tests__/api" --testNamePattern="(?!Integration)"

# Run integration tests only
npm test -- integration.test.js

# Run with coverage
npm test -- --coverage --testPathPattern="__tests__/api"

# Run in CI mode
npm run test:ci
```

## Test Configuration

### **Jest Configuration** (`jest.config.js`)

```javascript
module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/src/__tests__/api/setup.js'],
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 70,
      lines: 70,
      statements: 70,
    },
  },
  // ... additional configuration
};
```

### **Test Setup** (`setup.js`)

- Configures testing environment
- Mocks global dependencies (fetch, cookies)
- Sets up test utilities
- Configures API endpoints for testing

## Test Coverage

### **Coverage Targets**

- **Branches**: 70% minimum
- **Functions**: 70% minimum
- **Lines**: 70% minimum
- **Statements**: 70% minimum

### **Coverage Reports**

After running tests, coverage reports are available in:

- `coverage/unit/` - Unit test coverage
- `coverage/integration/` - Integration test coverage
- `coverage/combined/` - Combined coverage report
- `coverage/combined/lcov-report/index.html` - Interactive HTML report

## Test Scenarios

### **Authentication Tests**

```javascript
describe('Authentication API', () => {
  test('should login successfully', async () => {
    const mockResponse = { success: true, data: { token: 'mock-token' } };
    global.mockFetch(mockResponse);

    const result = await login({ email: 'test@example.com', password: 'password' });
    expect(result).toEqual(mockResponse);
  });
});
```

### **Vehicle Management Tests**

```javascript
describe('Vehicles API', () => {
  test('should create vehicle successfully', async () => {
    const vehicleData = { make: 'Toyota', model: 'Camry', year: 2023 };
    const mockResponse = { success: true, data: { id: 1, ...vehicleData } };

    global.mockFetch(mockResponse);
    const result = await createVehicle(vehicleData);
    expect(result).toEqual(mockResponse);
  });
});
```

### **Integration Tests**

```javascript
describe('Frontend API Integration Tests', () => {
  test('should perform end-to-end workflow', async () => {
    // Login
    const loginResult = await login({ email: 'admin@samfms.com', password: 'admin123' });
    expect(loginResult.success).toBe(true);

    // Create vehicle
    const vehicle = await createVehicle({ make: 'Toyota', model: 'Camry' });
    expect(vehicle.success).toBe(true);

    // Verify vehicle exists
    const vehicles = await getVehicles();
    expect(vehicles.data).toContain(expect.objectContaining({ id: vehicle.data.id }));
  });
});
```

## Mock Strategy

### **Global Mocks**

- **Fetch API**: Mocked globally for consistent HTTP testing
- **Cookies**: Mocked for authentication testing
- **Environment Variables**: Set for testing configuration
- **Console**: Suppressed for cleaner test output

### **Test Utilities**

```javascript
// Mock successful API response
global.mockFetch({ success: true, data: { id: 1 } });

// Mock API error
global.mockFetchError(new Error('API Error'));

// Mock cookies
getCookie.mockReturnValue('mock-token');
```

## Best Practices

### **Test Writing**

1. **Use descriptive test names** that explain what is being tested
2. **Test both success and error cases** for each API function
3. **Mock external dependencies** appropriately
4. **Assert on specific values** rather than just existence
5. **Clean up after tests** to avoid state leakage

### **Error Handling**

```javascript
test('should handle API errors gracefully', async () => {
  const mockError = new Error('Network error');
  global.mockFetchError(mockError);

  await expect(getVehicles()).rejects.toThrow('Network error');
});
```

### **Async Testing**

```javascript
test('should handle async operations', async () => {
  const mockResponse = { success: true, data: [] };
  global.mockFetch(mockResponse);

  const result = await getVehicles();
  expect(result).toEqual(mockResponse);
});
```

## Troubleshooting

### **Common Issues**

1. **Tests failing with "fetch is not defined"**

   - Ensure `setup.js` is properly configured
   - Check that `global.fetch` is mocked

2. **Integration tests failing**

   - Verify backend containers are running
   - Check service health endpoints
   - Ensure correct API URLs in configuration

3. **Coverage not meeting threshold**

   - Review untested code paths
   - Add tests for error scenarios
   - Check for unused code that can be removed

4. **Tests running slowly**
   - Reduce test timeout values
   - Optimize mock implementations
   - Consider parallel test execution

### **Debugging Tests**

```bash
# Run tests with verbose output
npm test -- --verbose

# Run specific test file with debugging
npm test -- --testPathPattern="auth.test.js" --verbose

# Run tests without coverage for faster execution
npm test -- --testPathPattern="__tests__/api" --watchAll=false
```

## Continuous Integration

### **GitHub Actions Integration**

```yaml
name: Frontend API Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install dependencies
        run: cd Frontend/samfms && npm install
      - name: Run tests
        run: cd Frontend/samfms && npm run test:ci
```

### **Docker Integration**

```dockerfile
# Frontend testing in Docker
FROM node:18-alpine
WORKDIR /app
COPY Frontend/samfms/package*.json ./
RUN npm install
COPY Frontend/samfms/ .
CMD ["npm", "run", "test:ci"]
```

## Performance Considerations

### **Test Execution Time**

- Unit tests: ~30 seconds
- Integration tests: ~60 seconds (with containers)
- Coverage generation: ~10 seconds additional

### **Optimization Tips**

1. **Use `--watchAll=false`** for CI environments
2. **Limit test parallelization** to avoid resource contention
3. **Mock heavy operations** like file uploads
4. **Use test data factories** for consistent test setup

## Maintenance

### **Regular Tasks**

1. **Update test dependencies** monthly
2. **Review and update mocks** when API changes
3. **Maintain coverage thresholds** as codebase grows
4. **Add tests for new API endpoints**
5. **Clean up obsolete test files**

### **Test Data Management**

```javascript
// Test data factory
const createTestVehicle = (overrides = {}) => ({
  make: 'Toyota',
  model: 'Camry',
  year: 2023,
  license_plate: 'TEST123',
  status: 'active',
  ...overrides,
});
```

This comprehensive testing infrastructure ensures high-quality API integration and provides confidence in the frontend application's reliability.
