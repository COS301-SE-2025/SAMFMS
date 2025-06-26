import { getApiHostname, authFetch } from './auth';

// Use the API base URL directly (should include protocol and /api)
export const API_URL = getApiHostname();

const ANALYTICS_API = {
  fleetUtilization: `${API_URL}/analytics/fleet-utilization`,
  vehicleUsage: `${API_URL}/analytics/vehicle-usage`,
  assignmentMetrics: `${API_URL}/analytics/assignment-metrics`,
  maintenance: `${API_URL}/analytics/maintenance`,
  driverPerformance: `${API_URL}/analytics/driver-performance`,
  costAnalytics: `${API_URL}/analytics/costs`,
  statusBreakdown: `${API_URL}/analytics/status-breakdown`,
  incidentStatistics: `${API_URL}/analytics/incidents`,
  departmentLocation: `${API_URL}/analytics/department-location`,
};

const handleResponse = async (response, errorMessage) => {
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`${errorMessage}: ${response.status} ${response.statusText} - ${text}`);
  }
  return response.json();
};
 


export const getFleetUtilization = async () => {/*
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