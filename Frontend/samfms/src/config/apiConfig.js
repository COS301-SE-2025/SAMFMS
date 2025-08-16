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
    LIST: '/management/vehicles',
    CREATE: '/management/vehicles',
    GET: id => `/management/vehicles/${id}`,
    UPDATE: id => `/management/vehicles/${id}`,
    DELETE: id => `/management/vehicles/${id}`,
    SEARCH: query => `/management/vehicles/search/${query}`,
    ASSIGN: '/management/vehicles/assign-driver',
    USAGE: id => `/management/vehicles/${id}/usage`,
  },

  // Driver Management
  DRIVERS: {
    LIST: '/management/drivers',
    CREATE: '/management/drivers',
    GET: id => `/management/drivers/${id}`,
    UPDATE: id => `/management/drivers/${id}`,
    DELETE: id => `/management/drivers/${id}`,
    SEARCH: query => `/management/drivers/search/${query}`,
    ACTIVATE: id => `/management/${id}/activate`,
    ASSIGN: '/management/assign-vehicle',
    EMPID: id => `/management/drivers/employee/${id}`,
    // Trip Planning Service - Get All Drivers from drivers collection
    TRIP_PLANNING_LIST: '/trips/drivers',
  },

  // Vehicle Assignments
  ASSIGNMENTS: {
    LIST: '/management/assignments',
    CREATE: '/management/assignments',
    UPDATE: id => `/management/assignments/${id}`,
    DELETE: id => `/management/assignments/${id}`,
    COMPLETE: id => `/management/assignments/${id}/complete`,
    CANCEL: id => `/management/assignments/${id}/cancel`,
  },

  LOCATIONS: {
    LIST: '/gps/locations',
    GET: id => `/gps/locations/${id}`,
    CREATE: '/gps/locations',
    UPDATE: '/gps/locations/update',
    DELETE: id => `/gps/locations/${id}`,
  },

  GEOFENCES: {
    LIST: '/gps/geofences',
    CREATE: '/gps/geofences',
    UPDATE: id => `/gps/geofences/${id}`,
    DELETE: id => `/gps/geofences/${id}`,
  },

  // Trip Planning
  TRIPS: {
    LIST: '/trips/trips',
    CREATE: '/trips/trips/create',
    UPDATE: id => `/trips/trips/${id}`,
    DELETE: id => `/trips/trips/${id}`,
    ACTIVE: '/trips/trips/active',
    HISTORY: '/trips/history',
    FINISHED: 'trips/trips/completed',
    UPCOMMINGTRIPSALL: '/trips/trips/upcomming',
    UPCOMMINGTRIPS: id => `/trips/trips/upcomming/${id}`,
    RECENTTRIPS: id => `/trips/trips/recent/${id}`,
    RECENTTRIPSALL: '/trips/recent',
    VEHICLEPOLYLINE: id => `/trips/trips/polyline/${id}`,
    ANALYTICS: {
      // Trip History Statistics
      HISTORY_STATS: '/trips/analytics/trips/history-stats',

      // Driver analytics with timeframe
      DRiVERSTATS: '/trips/analytics/drivers/stats',
      TOTALTRIPSDRIVER: '/trips/analytics/drivers/totaltrips',
      COMPLETIONRATEDRIVERS: '/trips/analytics/drivers/completionrate',
      AVGTRIPSPERDAYDRIVERS: '/trips/analytics/drivers/averagedaytrips',

      // Vehicle analytics with timeframe
      TOTALTRIPSVEHICLES: '/trips/analytics/vehicles/totaltrips',
      COMPLETIONRATEVEHICLES: '/trips/analytics/vehicles/completionrate',
      AVGTRIPSPERDAYVEHICLES: '/trips/analytics/vehicles/averagedaytrips',
    },
  },

  PLUGINSTATUS: {
    STATUS: '/health/healthy-services',
  },

  // Maintenance
  MAINTENANCE: {
    RECORDS: {
      LIST: '/maintenance/records',
      CREATE: '/maintenance/records',
      GET: id => `/maintenance/records/${id}`,
      UPDATE: id => `/maintenance/records/${id}`,
      DELETE: id => `/maintenance/records/${id}`,
      BY_VEHICLE: vehicleId => `/maintenance/records/vehicle/${vehicleId}`,
      OVERDUE: '/maintenance/records/overdue',
    },
    SCHEDULES: {
      LIST: '/maintenance/schedules',
      CREATE: '/maintenance/schedules',
      GET: id => `/maintenance/schedules/${id}`,
      UPDATE: id => `/maintenance/schedules/${id}`,
      DELETE: id => `/maintenance/schedules/${id}`,
    },
    LICENSES: {
      LIST: '/maintenance/licenses',
      CREATE: '/maintenance/licenses',
      GET: id => `/maintenance/licenses/${id}`,
      UPDATE: id => `/maintenance/licenses/${id}`,
      DELETE: id => `/maintenance/licenses/${id}`,
      EXPIRING: '/maintenance/licenses/expiring',
    },
    VENDORS: {
      LIST: '/maintenance/vendors',
      CREATE: '/maintenance/vendors',
      GET: id => `/maintenance/vendors/${id}`,
      UPDATE: id => `/maintenance/vendors/${id}`,
      DELETE: id => `/maintenance/vendors/${id}`,
    },
    ANALYTICS: {
      DASHBOARD: '/maintenance/analytics/dashboard',
      COSTS: '/maintenance/analytics/costs',
      OVERVIEW: '/maintenance/analytics',
    },
    NOTIFICATIONS: {
      LIST: '/maintenance/notifications',
      MARK_READ: id => `/maintenance/notifications/${id}/read`,
      DELETE: id => `/maintenance/notifications/${id}`,
    },
  },

  // Analytics (updated for management service)
  ANALYTICS: {
    DASHBOARD: '/management/analytics/dashboard',
    FLEET_UTILIZATION: '/management/analytics/fleet-utilization',
    VEHICLE_USAGE: '/management/analytics/vehicle-usage',
    ASSIGNMENT_METRICS: '/management/analytics/assignment-metrics',
    // MAINTENANCE: '/management/analytics/maintenance',
    DRIVER_PERFORMANCE: '/management/analytics/driver-performance',
    DRIVER_PERFORMANCE_BY_ID: '/management/analytics/driver-performance',
    // COSTS: '/management/analytics/costs',
    // STATUS_BREAKDOWN: '/management/analytics/status-breakdown',
    // INCIDENTS: '/management/analytics/incidents',
    // DEPARTMENT_LOCATION: '/management/analytics/department-location',
    REFRESH: '/management/analytics/refresh',
    DELETE: '/management/analytics/delete',
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
