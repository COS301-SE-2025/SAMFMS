import { authFetch } from './auth';
import { buildApiUrl } from '../../config/apiConfig';

// Analytics API endpoints using centralized configuration
const ANALYTICS_API = {
  fleetUtilization: buildApiUrl('/analytics/fleet-utilization'),
  vehicleUsage: buildApiUrl('/analytics/vehicle-usage'),
  assignmentMetrics: buildApiUrl('/analytics/assignment-metrics'),
  maintenance: buildApiUrl('/analytics/maintenance'),
  driverPerformance: buildApiUrl('/analytics/driver-performance'),
  costAnalytics: buildApiUrl('/analytics/costs'),
  statusBreakdown: buildApiUrl('/analytics/status-breakdown'),
  incidentStatistics: buildApiUrl('/analytics/incidents'),
  departmentLocation: buildApiUrl('/analytics/department-location'),
};

const handleResponse = async (response, errorMessage) => {
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`${errorMessage}: ${response.status} ${response.statusText} - ${text}`);
  }
  return response.json();
};

export const getFleetUtilization = async () => {
  /*
  try {
    const response = await authFetch(ANALYTICS_API.fleetUtilization);
    return await handleResponse(response, 'Failed to fetch fleet utilization');
  } catch (err) {
    console.error('Error in getFleetUtilization:', err);
    throw err;
  }*/
};

export const getVehicleUsage = async () => {
  try {
    const response = await authFetch(ANALYTICS_API.vehicleUsage);
    return await handleResponse(response, 'Failed to fetch vehicle usage statistics');
  } catch (err) {
    console.error('Error in getVehicleUsage:', err);
    throw err;
  }
};

export const getAssignmentMetrics = async () => {
  try {
    const response = await authFetch(ANALYTICS_API.assignmentMetrics);
    return await handleResponse(response, 'Failed to fetch assignment metrics');
  } catch (err) {
    console.error('Error in getAssignmentMetrics:', err);
    throw err;
  }
};

export const getMaintenanceAnalytics = async () => {
  try {
    const response = await authFetch(ANALYTICS_API.maintenance);
    return await handleResponse(response, 'Failed to fetch maintenance analytics');
  } catch (err) {
    console.error('Error in getMaintenanceAnalytics:', err);
    throw err;
  }
};

export const getDriverPerformance = async () => {
  try {
    const response = await authFetch(ANALYTICS_API.driverPerformance);
    return await handleResponse(response, 'Failed to fetch driver performance metrics');
  } catch (err) {
    console.error('Error in getDriverPerformance:', err);
    throw err;
  }
};

export const getCostAnalytics = async () => {
  try {
    const response = await authFetch(ANALYTICS_API.costAnalytics);
    return await handleResponse(response, 'Failed to fetch cost analytics');
  } catch (err) {
    console.error('Error in getCostAnalytics:', err);
    throw err;
  }
};

export const getStatusBreakdown = async () => {
  try {
    const response = await authFetch(ANALYTICS_API.statusBreakdown);
    return await handleResponse(response, 'Failed to fetch status breakdown');
  } catch (err) {
    console.error('Error in getStatusBreakdown:', err);
    throw err;
  }
};

export const getIncidentStatistics = async () => {
  try {
    const response = await authFetch(ANALYTICS_API.incidentStatistics);
    return await handleResponse(response, 'Failed to fetch incident statistics');
  } catch (err) {
    console.error('Error in getIncidentStatistics:', err);
    throw err;
  }
};

export const getDepartmentLocationAnalytics = async () => {
  try {
    const response = await authFetch(ANALYTICS_API.departmentLocation);
    return await handleResponse(response, 'Failed to fetch department/location analytics');
  } catch (err) {
    console.error('Error in getDepartmentLocationAnalytics:', err);
    throw err;
  }
};
