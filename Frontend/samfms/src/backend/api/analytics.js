import { authFetch } from './auth';
import { buildApiUrl, API_ENDPOINTS } from '../../config/apiConfig';

// Analytics API endpoints using centralized configuration
const ANALYTICS_API = {
  dashboard: buildApiUrl(API_ENDPOINTS.ANALYTICS.DASHBOARD),
  fleetUtilization: buildApiUrl(API_ENDPOINTS.ANALYTICS.FLEET_UTILIZATION),
  vehicleUsage: buildApiUrl(API_ENDPOINTS.ANALYTICS.VEHICLE_USAGE),
  assignmentMetrics: buildApiUrl(API_ENDPOINTS.ANALYTICS.ASSIGNMENT_METRICS),
  maintenance: buildApiUrl(API_ENDPOINTS.ANALYTICS.MAINTENANCE),
  driverPerformance: buildApiUrl(API_ENDPOINTS.ANALYTICS.DRIVER_PERFORMANCE),
  driverPerformanceById: buildApiUrl(API_ENDPOINTS.ANALYTICS.DRIVER_PERFORMANCE_BY_ID),
  costAnalytics: buildApiUrl(API_ENDPOINTS.ANALYTICS.COSTS),
  statusBreakdown: buildApiUrl(API_ENDPOINTS.ANALYTICS.STATUS_BREAKDOWN),
  incidentStatistics: buildApiUrl(API_ENDPOINTS.ANALYTICS.INCIDENTS),
  departmentLocation: buildApiUrl(API_ENDPOINTS.ANALYTICS.DEPARTMENT_LOCATION),
};

const handleResponse = async (response, errorMessage) => {
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`${errorMessage}: ${response.status} ${response.statusText} - ${text}`);
  }
  return response.json();
};

/**
 * Get dashboard analytics summary
 * @param {boolean} useCache - Whether to use cached data
 * @returns {Promise<Object>} Dashboard analytics data
 */
export const getDashboardAnalytics = async (useCache = true) => {
  try {
    const url = `${ANALYTICS_API.dashboard}?use_cache=${useCache}`;
    const response = await authFetch(url);
    return await handleResponse(response, 'Failed to fetch dashboard analytics');
  } catch (err) {
    console.error('Error in getDashboardAnalytics:', err);
    throw err;
  }
};

/**
 * Get fleet utilization metrics
 * @param {boolean} useCache - Whether to use cached data
 * @returns {Promise<Object>} Fleet utilization data
 */
export const getFleetUtilization = async (useCache = true) => {
  try {
    const url = `${ANALYTICS_API.fleetUtilization}?use_cache=${useCache}`;
    const response = await authFetch(url);
    return await handleResponse(response, 'Failed to fetch fleet utilization');
  } catch (err) {
    console.error('Error in getFleetUtilization:', err);
    throw err;
  }
};

export const getVehicleUsage = async (useCache = true) => {
  try {
    const url = `${ANALYTICS_API.vehicleUsage}?use_cache=${useCache}`;
    const response = await authFetch(url);
    return await handleResponse(response, 'Failed to fetch vehicle usage statistics');
  } catch (err) {
    console.error('Error in getVehicleUsage:', err);
    throw err;
  }
};

export const getAssignmentMetrics = async (useCache = true) => {
  try {
    console.log('Access getAssignmentMetrics from Dashboard');
    const url = `${ANALYTICS_API.assignmentMetrics}?use_cache=${useCache}`;
    const response = await authFetch(url);
    return await handleResponse(response, 'Failed to fetch assignment metrics');
  } catch (err) {
    console.error('Error in getAssignmentMetrics:', err);
    throw err;
  }
};

export const getMaintenanceAnalytics = async (useCache = true) => {
  try {
    const url = `${ANALYTICS_API.maintenance}?use_cache=${useCache}`;
    const response = await authFetch(url);
    return await handleResponse(response, 'Failed to fetch maintenance analytics');
  } catch (err) {
    console.error('Error in getMaintenanceAnalytics:', err);
    throw err;
  }
};

export const getDriverPerformance = async (useCache = true) => {
  try {
    const url = `${ANALYTICS_API.driverPerformance}?use_cache=${useCache}`;
    const response = await authFetch(url);
    return await handleResponse(response, 'Failed to fetch driver performance metrics');
  } catch (err) {
    console.error('Error in getDriverPerformance:', err);
    throw err;
  }
};

/**
 * Get performance analytics for a specific driver
 * @param {string} driverId - The driver ID
 * @param {boolean} useCache - Whether to use cached data
 * @returns {Promise<Object>} Driver performance data
 */
export const getDriverPerformanceById = async (driverId, useCache = true) => {
  try {
    if (!driverId) {
      throw new Error('Driver ID is required');
    }

    const url = `${ANALYTICS_API.driverPerformanceById}/${driverId}?use_cache=${useCache}`;
    const response = await authFetch(url);
    return await handleResponse(
      response,
      `Failed to fetch driver performance metrics for driver ${driverId}`
    );
  } catch (err) {
    console.error(`Error in getDriverPerformanceById for driver ${driverId}:`, err);
    throw err;
  }
};

export const getCostAnalytics = async (useCache = true) => {
  try {
    const url = `${ANALYTICS_API.costAnalytics}?use_cache=${useCache}`;
    const response = await authFetch(url);
    return await handleResponse(response, 'Failed to fetch cost analytics');
  } catch (err) {
    console.error('Error in getCostAnalytics:', err);
    throw err;
  }
};

export const getStatusBreakdown = async (useCache = true) => {
  try {
    const url = `${ANALYTICS_API.statusBreakdown}?use_cache=${useCache}`;
    const response = await authFetch(url);
    return await handleResponse(response, 'Failed to fetch status breakdown');
  } catch (err) {
    console.error('Error in getStatusBreakdown:', err);
    throw err;
  }
};

export const getIncidentStatistics = async (useCache = true) => {
  try {
    const url = `${ANALYTICS_API.incidentStatistics}?use_cache=${useCache}`;
    const response = await authFetch(url);
    return await handleResponse(response, 'Failed to fetch incident statistics');
  } catch (err) {
    console.error('Error in getIncidentStatistics:', err);
    throw err;
  }
};

export const getDepartmentLocationAnalytics = async (useCache = true) => {
  try {
    const url = `${ANALYTICS_API.departmentLocation}?use_cache=${useCache}`;
    const response = await authFetch(url);
    return await handleResponse(response, 'Failed to fetch department location analytics');
  } catch (err) {
    console.error('Error in getDepartmentLocationAnalytics:', err);
    throw err;
  }
};

// Legacy function aliases for backward compatibility
export const getTotalVehicles = async (useCache = true) => {
  const fleetData = await getFleetUtilization(useCache);
  return fleetData?.total_assignments || 0;
};

// Additional legacy aliases for backward compatibility
export const getFleetUtilizationData = getFleetUtilization;
export const getVehicleUsageData = getVehicleUsage;
export const getAssignmentMetricsData = getAssignmentMetrics;
export const getMaintenanceAnalyticsData = getMaintenanceAnalytics;
export const getDriverPerformanceData = getDriverPerformance;
export const getDriverPerformanceByIdData = getDriverPerformanceById;
export const getCostAnalyticsData = getCostAnalytics;
export const getStatusBreakdownData = getStatusBreakdown;
