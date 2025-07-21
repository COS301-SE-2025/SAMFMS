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
        config.baseURL = `https://${host}`;
        config.wsURL = `wss://${host}/ws`;
      }
      // For HTTP deployments (behind nginx HTTP proxy)
      else if (protocol === 'http:' && host !== 'localhost' && host !== '127.0.0.1') {
        config.baseURL = `http://${host}`;
        config.wsURL = `ws://${host}/ws`;
      }
      // For local development - connect directly to core service
      else {
        const corePort = process.env.REACT_APP_CORE_PORT || '21004';
        config.baseURL = `http://localhost:${corePort}`;
        config.wsURL = `ws://localhost:${corePort}/ws`;
      }
    } else {
      // Default fallback for server-side rendering or edge cases
      config.baseURL = 'http://localhost:21004';
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
    LIST: '/api/vehicles',
    CREATE: '/api/vehicles',
    GET: id => `/api/vehicles/${id}`,
    UPDATE: id => `/api/vehicles/${id}`,
    DELETE: id => `/api/vehicles/${id}`,
    SEARCH: query => `/api/vehicles/search/${query}`,
  },

  // Driver Management
  DRIVERS: {
    LIST: '/api/vehicles/drivers',
    CREATE: '/api/vehicles/drivers',
    GET: id => `/api/vehicles/drivers/${id}`,
    UPDATE: id => `/api/vehicles/drivers/${id}`,
    DELETE: id => `/api/vehicles/drivers/${id}`,
    SEARCH: query => `/api/vehicles/drivers/search/${query}`,
  },

  // Vehicle Assignments
  ASSIGNMENTS: {
    LIST: '/api/assignments',
    CREATE: '/api/assignments',
    UPDATE: id => `/api/assignments/${id}`,
    DELETE: id => `/api/assignments/${id}`,
    COMPLETE: id => `/api/assignments/${id}/complete`,
    CANCEL: id => `/api/assignments/${id}/cancel`,
  },

  // GPS and Tracking
  GPS: {
    LOCATIONS: '/api/gps/locations',
    CREATE_LOCATION: '/api/gps/locations',
  },

  // Trip Planning
  TRIPS: {
    LIST: '/api/trips',
    CREATE: '/api/trips',
  },

  // Maintenance
  MAINTENANCE: {
    RECORDS: {
      LIST: '/api/maintenance/records',
      CREATE: '/api/maintenance/records',
      GET: id => `/api/maintenance/records/${id}`,
      UPDATE: id => `/api/maintenance/records/${id}`,
      DELETE: id => `/api/maintenance/records/${id}`,
      BY_VEHICLE: vehicleId => `/api/maintenance/records/vehicle/${vehicleId}`,
      OVERDUE: '/api/maintenance/records/overdue',
    },
    SCHEDULES: {
      LIST: '/api/maintenance/schedules',
      CREATE: '/api/maintenance/schedules',
      GET: id => `/api/maintenance/schedules/${id}`,
      UPDATE: id => `/api/maintenance/schedules/${id}`,
      DELETE: id => `/api/maintenance/schedules/${id}`,
    },
    LICENSES: {
      LIST: '/api/maintenance/licenses',
      CREATE: '/api/maintenance/licenses',
      GET: id => `/api/maintenance/licenses/${id}`,
      UPDATE: id => `/api/maintenance/licenses/${id}`,
      DELETE: id => `/api/maintenance/licenses/${id}`,
      EXPIRING: '/api/maintenance/licenses/expiring',
    },
    VENDORS: {
      LIST: '/api/maintenance/vendors',
      CREATE: '/api/maintenance/vendors',
      GET: id => `/api/maintenance/vendors/${id}`,
      UPDATE: id => `/api/maintenance/vendors/${id}`,
      DELETE: id => `/api/maintenance/vendors/${id}`,
    },
    ANALYTICS: {
      DASHBOARD: '/api/maintenance/analytics/dashboard',
      COSTS: '/api/maintenance/analytics/costs',
      OVERVIEW: '/api/maintenance/analytics',
    },
    NOTIFICATIONS: {
      LIST: '/api/maintenance/notifications',
      MARK_READ: id => `/api/maintenance/notifications/${id}/read`,
      DELETE: id => `/api/maintenance/notifications/${id}`,
    },
  },

  // Analytics (updated for management service)
  ANALYTICS: {
    DASHBOARD: '/api/analytics/dashboard',
    FLEET_UTILIZATION: '/api/analytics/fleet-utilization',
    VEHICLE_USAGE: '/api/analytics/vehicle-usage',
    ASSIGNMENT_METRICS: '/api/analytics/assignment-metrics',
    MAINTENANCE: '/api/analytics/maintenance',
    DRIVER_PERFORMANCE: '/api/analytics/driver-performance',
    COSTS: '/api/analytics/costs',
    STATUS_BREAKDOWN: '/api/analytics/status-breakdown',
    INCIDENTS: '/api/analytics/incidents',
    DEPARTMENT_LOCATION: '/api/analytics/department-location',
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
