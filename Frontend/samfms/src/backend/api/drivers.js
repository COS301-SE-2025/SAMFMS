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
  assign: API_ENDPOINTS.DRIVERS.ASSIGN,
};

/**
 * Create a new driver
 * @param {Object} driverData - Driver data to create
 * @returns {Promise<Object>} Created driver data
 */
export const createDriver = async driverData => {
  try {
    const response = await httpClient.post(DRIVER_ENDPOINTS.create, driverData);
    console.log("Response for create driver: ", response)
    return response
  } catch (error) {
    console.error('Error creating driver:', error);
    throw error;
  }
};

/**
 * Get list of drivers with optional filters
 * Uses the auth/users endpoint and filters for users with driver role
 * @param {Object} params - Query parameters (skip, limit, status_filter, department_filter)
 * @returns {Promise<Object>} Drivers list with pagination info
 */
export const getDrivers = async (params = {}) => {
  try {
    console.log('Fetching drivers using auth/users endpoint...');

    // Get all users from the auth service directly
    const allUsers = await httpClient.get('/auth/users');

    // Filter for users with 'driver' role
    const drivers = allUsers.filter(user => user.role === 'driver');
    console.log(drivers);

    console.log(`Found ${drivers.length} drivers out of ${allUsers.length} total users`);

    // Apply optional filters if provided
    let filteredDrivers = drivers;

    if (params.status_filter) {
      // Convert status filter to match auth service data structure
      const isActiveFilter = params.status_filter.toLowerCase() === 'active';
      filteredDrivers = filteredDrivers.filter(driver => driver.is_active === isActiveFilter);
    }

    if (params.department_filter) {
      filteredDrivers = filteredDrivers.filter(
        driver => driver.details?.department === params.department_filter
      );
    }

    // Apply pagination if provided
    const skip = parseInt(params.skip) || 0;
    const limit = parseInt(params.limit) || filteredDrivers.length;

    const paginatedDrivers = filteredDrivers.slice(skip, skip + limit);

    // Return in the expected format with pagination info
    return {
      drivers: paginatedDrivers,
      total: filteredDrivers.length,
      skip: skip,
      limit: limit,
      has_more: skip + limit < filteredDrivers.length,
    };
  } catch (error) {
    console.error('Error fetching drivers:', error);
    throw error;
  }
};

/**
 * Get a specific driver by ID
 * Uses the auth service to find a user with driver role by ID
 * @param {string} driverId - Driver ID (user ID)
 * @returns {Promise<Object>} Driver data
 */
export const getDriver = async driverId => {
  try {
    if (!driverId) {
      throw new Error('Driver ID is required');
    }

    console.log(`Fetching driver ${driverId} using auth/users endpoint...`);

    // Get all users from the auth service directly
    const allUsers = await httpClient.get('/auth/users');

    // Find the specific driver by ID
    const driver = allUsers.find(user => user.id === driverId && user.role === 'driver');

    if (!driver) {
      throw new Error(`Driver with ID ${driverId} not found`);
    }

    console.log(`Found driver: ${driver.full_name}`);
    return driver;
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
 * Uses the auth service and filters drivers by name, email, etc.
 * @param {string} query - Search query
 * @returns {Promise<Array>} Array of matching drivers
 */
export const searchDrivers = async query => {
  try {
    if (!query) {
      throw new Error('Search query is required');
    }

    console.log(`Searching drivers for query: "${query}"`);

    // Get all users from the auth service directly
    const allUsers = await httpClient.get('/auth/users');

    // Filter for drivers first
    const drivers = allUsers.filter(user => user.role === 'driver');

    // Search within drivers by name, email, etc.
    const searchTerm = query.toLowerCase();
    const matchingDrivers = drivers.filter(
      driver =>
        driver.full_name?.toLowerCase().includes(searchTerm) ||
        driver.email?.toLowerCase().includes(searchTerm) ||
        driver.phoneNo?.includes(searchTerm)
    );

    console.log(`Found ${matchingDrivers.length} drivers matching "${query}"`);
    return matchingDrivers;
  } catch (error) {
    console.error(`Error searching drivers with query "${query}":`, error);
    throw error;
  }
};


export const assignVehicle = async (data) => {
  try {
    console.log("Vehicle and driver data",data);
    return await httpClient.post(DRIVER_ENDPOINTS.assign, data);
  } catch (error) {
    console.error('Error assigning vehicle to driver: ', error);
    throw error;
  }
}
