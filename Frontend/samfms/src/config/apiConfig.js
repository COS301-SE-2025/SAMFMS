/**
 * Centralized API Configuration for SAMFMS Frontend
 * Handles all API endpoint configuration and environment detection
 */

// Environment detection and API base URL configuration
const getApiConfig = () => {
  const config = {
    baseURL: '',
    wsURL: '',
    timeout: 30000,
    retries: 3,
    environment: 'production',
  };

  // Use environment variable if available (set in docker-compose or .env)
  const apiBaseUrl = process.env.REACT_APP_API_BASE_URL;
  const wsTarget = process.env.REACT_APP_WS_TARGET;
  const nodeEnv = process.env.NODE_ENV;

  if (apiBaseUrl) {
    console.log('Using API_BASE_URL from environment:', apiBaseUrl);
    config.baseURL = apiBaseUrl;
  } else {
    // Fallback logic for development
    if (typeof window !== 'undefined') {
      const protocol = window.location.protocol;
      const host = window.location.hostname;
      const port = window.location.port;

      // For production/staging with HTTPS - use nginx proxy path
      if (protocol === 'https:') {
        config.baseURL = `https://${host}/api`;
        config.wsURL = `wss://${host}/ws`;
      }
      // For HTTP deployments (behind nginx HTTP proxy)
      else if (protocol === 'http:' && host !== 'localhost' && host !== '127.0.0.1') {
        config.baseURL = `http://${host}/api`;
        config.wsURL = `ws://${host}/ws`;
      }
      // For local development - connect directly to core service
      else {
        const corePort = process.env.REACT_APP_CORE_PORT || '21004';
        config.baseURL = `http://localhost:${corePort}/api`;
        config.wsURL = `ws://localhost:${corePort}/ws`;
      }
    } else {
      // Default fallback for server-side rendering or edge cases
      config.baseURL = 'http://localhost:21004/api';
      config.wsURL = 'ws://localhost:21004/ws';
    }
  }

  // WebSocket URL configuration
  if (wsTarget) {
    config.wsURL = wsTarget;
  }

  // Environment detection
  if (nodeEnv) {
    config.environment = nodeEnv;
  } else if (config.baseURL.includes('localhost')) {
    config.environment = 'development';
  }

  return config;
};

export const API_CONFIG = getApiConfig();

// Debug logging
if (API_CONFIG.environment === 'development') {
  console.log('=== SAMFMS API Configuration ===');
  console.log('Environment Variables:');
  console.log('- REACT_APP_API_BASE_URL:', process.env.REACT_APP_API_BASE_URL);
  console.log('- REACT_APP_CORE_PORT:', process.env.REACT_APP_CORE_PORT);
  console.log('- REACT_APP_WS_TARGET:', process.env.REACT_APP_WS_TARGET);
  console.log('- NODE_ENV:', process.env.NODE_ENV);

  if (typeof window !== 'undefined') {
    console.log('Window location:', {
      protocol: window.location.protocol,
      hostname: window.location.hostname,
      port: window.location.port,
      href: window.location.href,
    });
  }

  console.log('Calculated API Config:', API_CONFIG);
  console.log('================================');
}

// API Endpoints configuration
export const API_ENDPOINTS = {
  // Authentication
  AUTH: {
    LOGIN: '/auth/login',
    SIGNUP: '/auth/signup',
    LOGOUT: '/auth/logout',
    REFRESH: '/auth/refresh',
    VERIFY: '/auth/verify-token',
    USER_EXISTS: '/auth/user-exists',
    PROFILE: '/auth/update-profile',
    CHANGE_PASSWORD: '/auth/change-password',
    UPLOAD_PICTURE: '/auth/upload-profile-picture',
  },

  // Vehicle Management
  VEHICLES: {
    LIST: '/vehicles',
    CREATE: '/vehicles',
    GET: id => `/vehicles/${id}`,
    UPDATE: id => `/vehicles/${id}`,
    DELETE: id => `/vehicles/${id}`,
    SEARCH: query => `/vehicles/search/${query}`,
  },

  // Driver Management
  DRIVERS: {
    LIST: '/vehicles/drivers',
    CREATE: '/vehicles/drivers',
    GET: id => `/vehicles/drivers/${id}`,
    UPDATE: id => `/vehicles/drivers/${id}`,
    DELETE: id => `/vehicles/drivers/${id}`,
  },

  // Vehicle Assignments
  ASSIGNMENTS: {
    LIST: '/vehicle-assignments',
    CREATE: '/vehicle-assignments',
    UPDATE: id => `/vehicle-assignments/${id}`,
    DELETE: id => `/vehicle-assignments/${id}`,
  },

  // GPS and Tracking
  GPS: {
    LOCATIONS: '/gps/locations',
    CREATE_LOCATION: '/gps/locations',
  },

  // Trip Planning
  TRIPS: {
    LIST: '/trips',
    CREATE: '/trips',
  },

  // Maintenance
  MAINTENANCE: {
    LIST: '/maintenance',
    CREATE: '/maintenance',
  },

  // Analytics
  ANALYTICS: {
    FLEET_UTILIZATION: '/analytics/fleet-utilization',
    VEHICLE_USAGE: '/analytics/vehicle-usage',
    ASSIGNMENT_METRICS: '/analytics/assignment-metrics',
    MAINTENANCE: '/analytics/maintenance',
    DRIVER_PERFORMANCE: '/analytics/driver-performance',
    COSTS: '/analytics/costs',
    STATUS_BREAKDOWN: '/analytics/status-breakdown',
    INCIDENTS: '/analytics/incidents',
    DEPARTMENT_LOCATION: '/analytics/department-location',
  },

  // WebSocket
  WEBSOCKET: {
    VEHICLES: '/ws/vehicles',
  },
};

// Helper function to build full URL
export const buildApiUrl = endpoint => {
  return `${API_CONFIG.baseURL}${endpoint}`;
};

// Helper function to build WebSocket URL
export const buildWsUrl = endpoint => {
  return `${API_CONFIG.wsURL}${endpoint}`;
};

// Request configuration defaults
export const REQUEST_DEFAULTS = {
  timeout: API_CONFIG.timeout,
  headers: {
    'Content-Type': 'application/json',
  },
  retries: API_CONFIG.retries,
};

export default API_CONFIG;
