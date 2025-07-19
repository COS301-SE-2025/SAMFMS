/**
 * Test Setup for Frontend API Testing
 * Configures Jest and testing environment for API tests
 */
import { configure } from '@testing-library/react';
import '@testing-library/jest-dom';

// Configure testing library
configure({
  testIdAttribute: 'data-testid',
});

// Mock environment variables for testing
process.env.REACT_APP_API_BASE_URL = 'http://localhost:8004';
process.env.REACT_APP_WS_TARGET = 'ws://localhost:8004';
process.env.NODE_ENV = 'test';

// Mock window.location for API config tests
delete window.location;
window.location = {
  protocol: 'http:',
  hostname: 'localhost',
  port: '3000',
  origin: 'http://localhost:3000',
};

// Mock fetch for API testing
global.fetch = jest.fn();

// Mock console methods to reduce noise in tests
global.console = {
  ...console,
  log: jest.fn(),
  warn: jest.fn(),
  error: jest.fn(),
};

// Setup and teardown for fetch mocks
beforeEach(() => {
  fetch.mockClear();
});

afterEach(() => {
  jest.clearAllMocks();
});

// Global test utilities
global.mockFetch = (response, options = {}) => {
  const { status = 200, ok = true, headers = {} } = options;

  fetch.mockImplementationOnce(() =>
    Promise.resolve({
      ok,
      status,
      headers: new Headers(headers),
      json: () => Promise.resolve(response),
      text: () => Promise.resolve(JSON.stringify(response)),
    })
  );
};

global.mockFetchError = error => {
  fetch.mockImplementationOnce(() => Promise.reject(error));
};

// Mock cookie functions
jest.mock('../../lib/cookies', () => ({
  getCookie: jest.fn(),
  setCookie: jest.fn(),
  eraseCookie: jest.fn(),
}));

// Mock API config
jest.mock('../../config/apiConfig', () => ({
  API_CONFIG: {
    baseURL: 'http://localhost:8004',
    wsURL: 'ws://localhost:8004',
    timeout: 30000,
    retries: 3,
    environment: 'test',
  },
  API_ENDPOINTS: {
    AUTH: {
      LOGIN: '/auth/login',
      SIGNUP: '/auth/register',
      LOGOUT: '/auth/logout',
      REFRESH: '/auth/refresh',
      CHANGE_PASSWORD: '/auth/change-password',
      USER_EXISTS: '/auth/user-exists',
      PROFILE: '/auth/profile',
      UPLOAD_PICTURE: '/auth/upload-picture',
    },
    VEHICLES: {
      LIST: '/api/vehicles',
      CREATE: '/api/vehicles',
      GET: '/api/vehicles',
      UPDATE: '/api/vehicles',
      DELETE: '/api/vehicles',
      SEARCH: '/api/vehicles/search',
    },
    DRIVERS: {
      LIST: '/api/drivers',
      CREATE: '/api/drivers',
      GET: '/api/drivers',
      UPDATE: '/api/drivers',
      DELETE: '/api/drivers',
    },
    MAINTENANCE: {
      LIST: '/api/maintenance',
      CREATE: '/api/maintenance',
      GET: '/api/maintenance',
      UPDATE: '/api/maintenance',
      DELETE: '/api/maintenance',
      SCHEDULE: '/api/maintenance/schedule',
      ANALYTICS: '/api/maintenance/analytics',
    },
    ASSIGNMENTS: {
      LIST: '/api/assignments',
      CREATE: '/api/assignments',
      GET: '/api/assignments',
      UPDATE: '/api/assignments',
      DELETE: '/api/assignments',
    },
  },
  buildApiUrl: jest.fn(endpoint => `http://localhost:8004${endpoint}`),
}));
