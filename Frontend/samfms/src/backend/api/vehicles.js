/**
 * Vehicle Management API
 * All vehicle-related API endpoints and functions
 */
import { httpClient } from '../services/httpClient';
import { buildApiUrl, API_ENDPOINTS } from '../../config/apiConfig';

// Vehicle API endpoints using centralized configuration
const VEHICLE_ENDPOINTS = {
  list: API_ENDPOINTS.VEHICLES.LIST,
  create: API_ENDPOINTS.VEHICLES.CREATE,
  get: API_ENDPOINTS.VEHICLES.GET,
  update: API_ENDPOINTS.VEHICLES.UPDATE,
  delete: API_ENDPOINTS.VEHICLES.DELETE,
  search: API_ENDPOINTS.VEHICLES.SEARCH,
};

/**
 * Create a new vehicle
 * @param {Object} vehicleData - Vehicle data to create
 * @returns {Promise<Object>} Created vehicle data
 */
export const createVehicle = async (vehicleData) => {
  try {
    return await httpClient.post(VEHICLE_ENDPOINTS.create, vehicleData);
  } catch (error) {
    console.error('Error creating vehicle:', error);
    throw error;
  }
};

/**
 * Get list of vehicles with optional filters
 * @param {Object} params - Query parameters (skip, limit, status_filter, make_filter)
 * @returns {Promise<Object>} Vehicles list with pagination info
 */
export const getVehicles = async (params = {}) => {
  try {
    const queryParams = new URLSearchParams();
    if (params.skip) queryParams.append('skip', params.skip);
    if (params.limit) queryParams.append('limit', params.limit);
    if (params.status_filter) queryParams.append('status_filter', params.status_filter);
    if (params.make_filter) queryParams.append('make_filter', params.make_filter);

    const endpoint = `${VEHICLE_ENDPOINTS.list}${
      queryParams.toString() ? '?' + queryParams.toString() : ''
    }`;

    return await httpClient.get(endpoint);
  } catch (error) {
    console.error('Error fetching vehicles:', error);
    throw error;
  }
};

/**
 * Get a specific vehicle by ID
 * @param {string} vehicleId - Vehicle ID
 * @returns {Promise<Object>} Vehicle data
 */
export const getVehicle = async (vehicleId) => {
  try {
    if (!vehicleId) {
      throw new Error('Vehicle ID is required');
    }

    return await httpClient.get(VEHICLE_ENDPOINTS.get(vehicleId));
  } catch (error) {
    console.error(`Error fetching vehicle ${vehicleId}:`, error);
    throw error;
  }
};

/**
 * Update a vehicle
 * @param {string} vehicleId - Vehicle ID
 * @param {Object} updateData - Data to update
 * @returns {Promise<Object>} Updated vehicle data
 */
export const updateVehicle = async (vehicleId, updateData) => {
  try {
    if (!vehicleId) {
      throw new Error('Vehicle ID is required');
    }

    return await httpClient.put(VEHICLE_ENDPOINTS.update(vehicleId), updateData);
  } catch (error) {
    console.error(`Error updating vehicle ${vehicleId}:`, error);
    throw error;
  }
};

/**
 * Delete a vehicle
 * @param {string} vehicleId - Vehicle ID
 * @returns {Promise<Object>} Deletion confirmation
 */
export const deleteVehicle = async (vehicleId) => {
  try {
    if (!vehicleId) {
      throw new Error('Vehicle ID is required');
    }

    return await httpClient.delete(VEHICLE_ENDPOINTS.delete(vehicleId));
  } catch (error) {
    console.error(`Error deleting vehicle ${vehicleId}:`, error);
    throw error;
  }
};

/**
 * Search vehicles by query
 * @param {string} query - Search query
 * @returns {Promise<Array>} Array of matching vehicles
 */
export const searchVehicles = async (query) => {
  try {
    if (!query) {
      throw new Error('Search query is required');
    }

    const result = await httpClient.get(VEHICLE_ENDPOINTS.search(encodeURIComponent(query)));
    
    // Return the vehicles array or the whole result if it's already an array
    return result.vehicles || result || [];
  } catch (error) {
    console.error(`Error searching vehicles with query "${query}":`, error);
    throw error;
  }
};
