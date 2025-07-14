/**
 * Driver Management API
 * All driver-related API endpoints and functions
 */
import { httpClient } from '../services/httpClient';
import { API_ENDPOINTS } from '../../config/apiConfig';

// Driver API endpoints using centralized configuration
const DRIVER_ENDPOINTS = {
  list: API_ENDPOINTS.DRIVERS.LIST,
  create: API_ENDPOINTS.DRIVERS.CREATE,
  get: API_ENDPOINTS.DRIVERS.GET,
  update: API_ENDPOINTS.DRIVERS.UPDATE,
  delete: API_ENDPOINTS.DRIVERS.DELETE,
};

/**
 * Create a new driver
 * @param {Object} driverData - Driver data to create
 * @returns {Promise<Object>} Created driver data
 */
export const createDriver = async driverData => {
  try {
    return await httpClient.post(DRIVER_ENDPOINTS.create, driverData);
  } catch (error) {
    console.error('Error creating driver:', error);
    throw error;
  }
};

/**
 * Get list of drivers with optional filters
 * @param {Object} params - Query parameters (skip, limit, status_filter, department_filter)
 * @returns {Promise<Object>} Drivers list with pagination info
 */
export const getDrivers = async (params = {}) => {
  try {
    const queryParams = new URLSearchParams();
    if (params.skip) queryParams.append('skip', params.skip);
    if (params.limit) queryParams.append('limit', params.limit);
    if (params.status_filter) queryParams.append('status_filter', params.status_filter);
    if (params.department_filter) queryParams.append('department_filter', params.department_filter);

    const endpoint = `${DRIVER_ENDPOINTS.list}${
      queryParams.toString() ? '?' + queryParams.toString() : ''
    }`;

    return await httpClient.get(endpoint);
  } catch (error) {
    console.error('Error fetching drivers:', error);
    throw error;
  }
};

/**
 * Get a specific driver by ID
 * @param {string} driverId - Driver ID (can be MongoDB ObjectId or employee ID)
 * @returns {Promise<Object>} Driver data
 */
export const getDriver = async driverId => {
  try {
    if (!driverId) {
      throw new Error('Driver ID is required');
    }

    return await httpClient.get(DRIVER_ENDPOINTS.get(driverId));
  } catch (error) {
    console.error(`Error fetching driver ${driverId}:`, error);
    throw error;
  }
};

/**
 * Update a driver
 * @param {string} driverId - Driver ID
 * @param {Object} updateData - Data to update
 * @returns {Promise<Object>} Updated driver data
 */
export const updateDriver = async (driverId, updateData) => {
  try {
    if (!driverId) {
      throw new Error('Driver ID is required');
    }

    return await httpClient.put(DRIVER_ENDPOINTS.update(driverId), updateData);
  } catch (error) {
    console.error(`Error updating driver ${driverId}:`, error);
    throw error;
  }
};

/**
 * Delete a driver
 * @param {string} driverId - Driver ID
 * @returns {Promise<Object>} Deletion confirmation
 */
export const deleteDriver = async driverId => {
  try {
    if (!driverId) {
      throw new Error('Driver ID is required');
    }

    return await httpClient.delete(DRIVER_ENDPOINTS.delete(driverId));
  } catch (error) {
    console.error(`Error deleting driver ${driverId}:`, error);
    throw error;
  }
};

/**
 * Search drivers by query
 * @param {string} query - Search query
 * @returns {Promise<Array>} Array of matching drivers
 */
export const searchDrivers = async query => {
  try {
    if (!query) {
      throw new Error('Search query is required');
    }

    // Note: This endpoint might need to be added to API_ENDPOINTS if it doesn't exist
    const searchEndpoint = `/drivers/search/${encodeURIComponent(query)}`;
    return await httpClient.get(searchEndpoint);
  } catch (error) {
    console.error(`Error searching drivers with query "${query}":`, error);
    throw error;
  }
};
