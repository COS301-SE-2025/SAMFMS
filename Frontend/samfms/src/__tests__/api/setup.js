/**
 * Jest Setup for API Integration Tests
 * Configures the test environment for Frontend-Core integration testing
 */

// Polyfill for AbortSignal.timeout if not available
if (!global.AbortSignal || !global.AbortSignal.timeout) {
  global.AbortSignal = {
    timeout: (ms) => {
      const controller = new AbortController();
      setTimeout(() => controller.abort(), ms);
      return controller.signal;
    }
  };
}

// Mock console methods to reduce noise in tests
const originalConsole = { ...console };

beforeEach(() => {
  // Suppress console.log during tests unless explicitly needed
  if (process.env.VERBOSE_TESTS !== 'true') {
    console.log = jest.fn();
    console.info = jest.fn();
  }
});

afterEach(() => {
  // Restore console methods
  if (process.env.VERBOSE_TESTS !== 'true') {
    console.log = originalConsole.log;
    console.info = originalConsole.info;
  }
});

// Global test timeout
jest.setTimeout(60000);

// Mock localStorage for auth tests
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
  writable: true,
});

// Setup fetch mock if needed
if (!global.fetch) {
  const { default: fetch } = require('node-fetch');
  global.fetch = fetch;
}

// Dummy test to prevent "no tests" error
test('setup configuration is loaded', () => {
  expect(true).toBe(true);
});

console.log('API Integration Test Setup Complete');