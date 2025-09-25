/**
 * Frontend Smoke Tests
 * Quick validation tests that don't require running services
 */

import { API_CONFIG } from '../../config/apiConfig';

describe('Frontend Smoke Tests', () => {
  test('API configuration is properly loaded', () => {
    expect(API_CONFIG).toBeDefined();
    expect(API_CONFIG.baseURL).toBeDefined();
    expect(typeof API_CONFIG.baseURL).toBe('string');
    expect(API_CONFIG.baseURL).toMatch(/^https?:\/\//);
  });

  test('Auth API functions can be imported', () => {
    expect(() => {
      require('../../backend/api/auth');
    }).not.toThrow();
  });

  test('Vehicle API functions can be imported', () => {
    expect(() => {
      require('../../backend/api/vehicles');
    }).not.toThrow();
  });

  test('Driver API functions can be imported', () => {
    expect(() => {
      require('../../backend/api/drivers');
    }).not.toThrow();
  });

  test('Analytics API functions can be imported', () => {
    expect(() => {
      require('../../backend/api/analytics');
    }).not.toThrow();
  });

  test('HTTP Client service can be imported', () => {
    expect(() => {
      require('../../backend/services/httpClient');
    }).not.toThrow();
  });
});