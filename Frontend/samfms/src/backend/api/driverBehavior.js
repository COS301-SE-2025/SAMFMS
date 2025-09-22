/**
 * Driver Behavior API Service
 * Handles all driver behavior and history related API calls
 */
import { httpClient } from '../services/httpClient';
import { API_ENDPOINTS } from '../../config/apiConfig';

/**
 * Safely parse a numeric value, returning 0 if invalid
 * @param {any} value - Value to parse
 * @returns {number} Parsed number or 0
 */
const safeParseFloat = (value) => {
  const parsed = parseFloat(value);
  return isNaN(parsed) ? 0 : parsed;
};

/**
 * Safely format a score for display
 * @param {any} score - Score value to format
 * @param {number} decimals - Number of decimal places (default: 1)
 * @returns {string} Formatted score string
 */
export const formatScore = (score, decimals = 1) => {
  return safeParseFloat(score).toFixed(decimals);
};

// Driver behavior API endpoints
const DRIVER_BEHAVIOR_ENDPOINTS = {
  list: API_ENDPOINTS.DRIVER_BEHAVIOR.LIST,
  get: API_ENDPOINTS.DRIVER_BEHAVIOR.GET,
  summary: API_ENDPOINTS.DRIVER_BEHAVIOR.SUMMARY,
  riskDistribution: API_ENDPOINTS.DRIVER_BEHAVIOR.RISK_DISTRIBUTION,
  recentAlerts: API_ENDPOINTS.DRIVER_BEHAVIOR.RECENT_ALERTS,
  recalculate: API_ENDPOINTS.DRIVER_BEHAVIOR.RECALCULATE,
  update: API_ENDPOINTS.DRIVER_BEHAVIOR.UPDATE,
  trips: API_ENDPOINTS.DRIVER_BEHAVIOR.TRIPS,
};

/**
 * Transform backend driver history data to frontend format
 * @param {Object} backendDriver - Driver data from backend
 * @returns {Object} Frontend formatted driver data
 */
const transformDriverData = (backendDriver) => {
  return {
    id: backendDriver.driver_id,
    name: backendDriver.driver_name,
    employeeId: backendDriver.employee_id || backendDriver.driver_id,
    overallScore: safeParseFloat((backendDriver.driver_safety_score || 0) / 10), // Convert 0-100 to 0-10 as number
    speedingEvents: backendDriver.speeding_violations || 0,
    harshBraking: backendDriver.braking_violations || 0,
    rapidAcceleration: backendDriver.acceleration_violations || 0,
    distraction: backendDriver.phone_usage_violations || 0,
    totalViolations: (backendDriver.speeding_violations || 0) + 
                    (backendDriver.braking_violations || 0) + 
                    (backendDriver.acceleration_violations || 0) + 
                    (backendDriver.phone_usage_violations || 0),
    riskLevel: backendDriver.driver_risk_level || 'low',
    completionRate: backendDriver.trip_completion_rate || 0,
    totalTrips: backendDriver.completed_trips || 0,
    completedTrips: backendDriver.completed_trips || 0,
    cancelledTrips: backendDriver.cancelled_trips || 0,
    totalAssignedTrips: backendDriver.total_assigned_trips || 0,
    lastUpdated: backendDriver.last_updated,
  };
};

/**
 * Get all driver histories with pagination and filtering
 * @param {Object} params - Query parameters (skip, limit, risk_level)
 * @returns {Promise<Object>} Driver histories with pagination info
 */
export const getAllDriverHistories = async (params = {}) => {
  try {
    console.log('Fetching driver histories with params:', params);
    
    // Build query parameters
    const queryParams = new URLSearchParams();
    
    if (params.skip !== undefined) {
      queryParams.append('skip', parseInt(params.skip, 10).toString());
    }
    
    if (params.limit !== undefined) {
      queryParams.append('limit', parseInt(params.limit, 10).toString());
    }
    
    if (params.page !== undefined && params.limit !== undefined) {
      const skip = (parseInt(params.page, 10) - 1) * parseInt(params.limit, 10);
      queryParams.set('skip', skip.toString());
    }
    
    if (params.risk_level) {
      queryParams.append('risk_level', params.risk_level);
    }
    
    // Build URL with query parameters
    const url = queryParams.toString() 
      ? `${DRIVER_BEHAVIOR_ENDPOINTS.list}?${queryParams.toString()}`
      : DRIVER_BEHAVIOR_ENDPOINTS.list;
    
    const response = await httpClient.get(url);
    
    // Handle nested response structure from Core service
    const data = response.data?.data || response.data || response;
    
    if (!data.histories) {
      console.warn('No histories found in response:', data);
      return {
        drivers: [],
        pagination: { skip: 0, limit: 100, count: 0, has_more: false },
        totalCount: 0
      };
    }
    
    // Transform driver data to frontend format
    const transformedDrivers = data.histories.map(transformDriverData);
    
    return {
      drivers: transformedDrivers,
      pagination: data.pagination || { skip: 0, limit: 100, count: transformedDrivers.length, has_more: false },
      totalCount: transformedDrivers.length
    };
    
  } catch (error) {
    console.error('Error fetching driver histories:', error);
    throw error;
  }
};

/**
 * Get specific driver history and statistics
 * @param {string} driverId - Driver ID
 * @returns {Promise<Object>} Driver statistics and history
 */
export const getDriverHistory = async (driverId) => {
  try {
    console.log('Fetching driver history for:', driverId);
    
    const response = await httpClient.get(DRIVER_BEHAVIOR_ENDPOINTS.get(driverId));
    
    // Handle nested response structure from Core service
    const data = response.data?.data || response.data || response;
    
    return {
      success: true,
      driver: transformDriverData(data),
      statistics: data
    };
    
  } catch (error) {
    console.error('Error fetching driver history:', error);
    throw error;
  }
};

/**
 * Get driver summary (concise performance overview)
 * @param {string} driverId - Driver ID
 * @returns {Promise<Object>} Driver summary
 */
export const getDriverSummary = async (driverId) => {
  try {
    console.log('Fetching driver summary for:', driverId);
    
    const response = await httpClient.get(DRIVER_BEHAVIOR_ENDPOINTS.summary(driverId));
    
    // Handle nested response structure from Core service
    const data = response.data?.data || response.data || response;
    
    return {
      success: true,
      summary: {
        driver_id: data.driver_id,
        driver_name: data.driver_name,
        safety_score: (data.safety_score / 10).toFixed(1), // Convert to 0-10 scale
        risk_level: data.risk_level,
        completion_rate: data.completion_rate,
        total_trips: data.total_trips,
        total_violations: data.total_violations,
        last_updated: data.last_updated
      }
    };
    
  } catch (error) {
    console.error('Error fetching driver summary:', error);
    throw error;
  }
};

/**
 * Get risk level distribution analytics
 * @returns {Promise<Object>} Risk distribution data
 */
export const getRiskDistribution = async () => {
  try {
    console.log('Fetching risk distribution analytics');
    
    const response = await httpClient.get(DRIVER_BEHAVIOR_ENDPOINTS.riskDistribution);
    
    // Handle nested response structure from Core service
    const data = response.data?.data || response.data || response;
    
    return {
      success: true,
      totalDrivers: data.total_drivers || 0,
      distribution: data.distribution || { low: { count: 0, percentage: 0 }, medium: { count: 0, percentage: 0 }, high: { count: 0, percentage: 0 } }
    };
    
  } catch (error) {
    console.error('Error fetching risk distribution:', error);
    throw error;
  }
};

/**
 * Calculate dashboard metrics from driver data
 * @param {Array} drivers - Array of driver data
 * @returns {Object} Dashboard metrics
 */
export const calculateDashboardMetrics = (drivers) => {
  if (!drivers || drivers.length === 0) {
    return {
      totalDrivers: 0,
      averageScore: 0,
      totalSpeedingEvents: 0,
      totalHarshBraking: 0,
      riskDistribution: { high: 0, medium: 0, low: 0 }
    };
  }
  
  const metrics = {
    totalDrivers: drivers.length,
    averageScore: 0,
    totalSpeedingEvents: 0,
    totalHarshBraking: 0,
    totalRapidAcceleration: 0,
    totalDistraction: 0,
    riskDistribution: { high: 0, medium: 0, low: 0 }
  };
  
  let totalScore = 0;
  
  drivers.forEach(driver => {
    totalScore += safeParseFloat(driver.overallScore);
    metrics.totalSpeedingEvents += driver.speedingEvents || 0;
    metrics.totalHarshBraking += driver.harshBraking || 0;
    metrics.totalRapidAcceleration += driver.rapidAcceleration || 0;
    metrics.totalDistraction += driver.distraction || 0;
    
    // Calculate risk distribution based on safety score
    const score = safeParseFloat(driver.overallScore);
    if (score < 7) {
      metrics.riskDistribution.high++;
    } else if (score < 8.5) {
      metrics.riskDistribution.medium++;
    } else {
      metrics.riskDistribution.low++;
    }
  });
  
  metrics.averageScore = (totalScore / drivers.length).toFixed(1);
  
  return metrics;
};

/**
 * Get top performing drivers
 * @param {Array} drivers - Array of driver data
 * @param {number} limit - Number of top performers to return
 * @returns {Array} Top performing drivers sorted by safety score
 */
export const getTopPerformers = (drivers, limit = 5) => {
  if (!drivers || drivers.length === 0) return [];
  
  return drivers
    .sort((a, b) => safeParseFloat(b.overallScore) - safeParseFloat(a.overallScore))
    .slice(0, limit);
};

/**
 * Recalculate all driver histories
 * @returns {Promise<Object>} Recalculation results
 */
export const recalculateAllHistories = async () => {
  try {
    console.log('Triggering recalculation of all driver histories');
    
    const response = await httpClient.post(DRIVER_BEHAVIOR_ENDPOINTS.recalculate);
    
    // Handle nested response structure from Core service
    const data = response.data?.data || response.data || response;
    
    return {
      success: true,
      results: data
    };
    
  } catch (error) {
    console.error('Error recalculating driver histories:', error);
    throw error;
  }
};

/**
 * Update specific driver history
 * @param {string} driverId - Driver ID
 * @returns {Promise<Object>} Updated driver data
 */
export const updateDriverHistory = async (driverId) => {
  try {
    console.log('Updating driver history for:', driverId);
    
    const response = await httpClient.post(DRIVER_BEHAVIOR_ENDPOINTS.update(driverId));
    
    // Handle nested response structure from Core service
    const data = response.data?.data || response.data || response;
    
    return {
      success: true,
      driver: transformDriverData(data),
      statistics: data
    };
    
  } catch (error) {
    console.error('Error updating driver history:', error);
    throw error;
  }
};

/**
 * Get trip history for a specific driver
 * @param {string} driverId - Driver ID
 * @param {Object} params - Query parameters (skip, limit, status)
 * @returns {Promise<Object>} Trip history data
 */
export const getDriverTripHistory = async (driverId, params = {}) => {
  try {
    console.log('Fetching trip history for driver:', driverId, 'with params:', params);
    
    // Build query parameters
    const queryParams = new URLSearchParams();
    
    if (params.skip !== undefined) {
      queryParams.append('skip', parseInt(params.skip, 10).toString());
    }
    
    if (params.limit !== undefined) {
      queryParams.append('limit', parseInt(params.limit, 10).toString());
    }
    
    if (params.status) {
      queryParams.append('status', params.status);
    }
    
    const url = `${DRIVER_BEHAVIOR_ENDPOINTS.trips(driverId)}${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    
    console.log('Trip history API URL:', url);
    
    const response = await httpClient.get(url);
    
    // Handle nested response structure from Core service
    const data = response.data?.data || response.data || response;
    
    return {
      success: true,
      trips: data.trips || [],
      pagination: data.pagination || {},
      filters: data.filters || {}
    };
    
  } catch (error) {
    console.error('Error fetching trip history:', error);
    throw error;
  }
};

/**
 * Get recent driver alerts and violations
 * @param {Object} params - Query parameters (limit, hours_back)
 * @returns {Promise<Object>} Recent alerts data
 */
export const getRecentDriverAlerts = async (params = {}) => {
  try {
    console.log('Fetching recent driver alerts with params:', params);
    
    // Build query parameters
    const queryParams = new URLSearchParams();
    
    if (params.limit !== undefined) {
      queryParams.append('limit', parseInt(params.limit, 10).toString());
    }
    
    if (params.hours_back !== undefined) {
      queryParams.append('hours_back', parseInt(params.hours_back, 10).toString());
    }
    
    const url = `${DRIVER_BEHAVIOR_ENDPOINTS.recentAlerts}${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    
    console.log('Recent alerts API URL:', url);
    
    const response = await httpClient.get(url);
    
    // Handle nested response structure from Core service
    const data = response.data?.data || response.data || response;
    
    return {
      success: true,
      alerts: data.alerts || [],
      total_count: data.total_count || 0,
      time_range: data.time_range || {}
    };

  } catch (error) {
    console.error('Error fetching recent driver alerts:', error);
    
    return {
      success: false,
      alerts: [],
      total_count: 0,
      error: error.response?.data?.detail || error.message || 'Failed to fetch recent alerts'
    };
  }
};

const driverBehaviorAPI = {
  getAllDriverHistories,
  getDriverHistory,
  getDriverSummary,
  getRiskDistribution,
  calculateDashboardMetrics,
  getTopPerformers,
  recalculateAllHistories,
  updateDriverHistory,
  getDriverTripHistory,
  getRecentDriverAlerts,
  transformDriverData,
  formatScore
};

export default driverBehaviorAPI;