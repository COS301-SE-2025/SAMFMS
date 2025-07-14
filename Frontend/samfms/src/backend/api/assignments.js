/**
 * Vehicle Assignment Management API
 * All vehicle assignment-related API endpoints and functions
 */
import { httpClient } from '../services/httpClient';
import { API_ENDPOINTS } from '../../config/apiConfig';

// Vehicle Assignment API endpoints using centralized configuration
const ASSIGNMENT_ENDPOINTS = {
  list: API_ENDPOINTS.ASSIGNMENTS.LIST,
  create: API_ENDPOINTS.ASSIGNMENTS.CREATE,
  update: API_ENDPOINTS.ASSIGNMENTS.UPDATE,
  delete: API_ENDPOINTS.ASSIGNMENTS.DELETE,
};

/**
 * Get list of vehicle assignments with optional filters
 * @param {Object} params - Query parameters (skip, limit, vehicle_id, driver_id)
 * @returns {Promise<Object>} Assignments list with pagination info
 */
export const getVehicleAssignments = async (params = {}) => {
  try {
    const queryParams = new URLSearchParams();
    if (params.skip) queryParams.append('skip', params.skip);
    if (params.limit) queryParams.append('limit', params.limit);
    if (params.vehicle_id) queryParams.append('vehicle_id', params.vehicle_id);
    if (params.driver_id) queryParams.append('driver_id', params.driver_id);

    const endpoint = `${ASSIGNMENT_ENDPOINTS.list}${
      queryParams.toString() ? '?' + queryParams.toString() : ''
    }`;

    return await httpClient.get(endpoint);
  } catch (error) {
    console.error('Error fetching vehicle assignments:', error);
    throw error;
  }
};

/**
 * Create a new vehicle assignment
 * @param {Object} assignmentData - Assignment data to create
 * @returns {Promise<Object>} Created assignment data
 */
export const createVehicleAssignment = async assignmentData => {
  try {
    return await httpClient.post(ASSIGNMENT_ENDPOINTS.create, assignmentData);
  } catch (error) {
    console.error('Error creating vehicle assignment:', error);
    throw error;
  }
};

/**
 * Update a vehicle assignment
 * @param {string} assignmentId - Assignment ID
 * @param {Object} updateData - Data to update
 * @returns {Promise<Object>} Updated assignment data
 */
export const updateVehicleAssignment = async (assignmentId, updateData) => {
  try {
    if (!assignmentId) {
      throw new Error('Assignment ID is required');
    }

    return await httpClient.put(ASSIGNMENT_ENDPOINTS.update(assignmentId), updateData);
  } catch (error) {
    console.error(`Error updating vehicle assignment ${assignmentId}:`, error);
    throw error;
  }
};

/**
 * Delete a vehicle assignment
 * @param {string} assignmentId - Assignment ID
 * @returns {Promise<Object>} Deletion confirmation
 */
export const deleteVehicleAssignment = async assignmentId => {
  try {
    if (!assignmentId) {
      throw new Error('Assignment ID is required');
    }

    return await httpClient.delete(ASSIGNMENT_ENDPOINTS.delete(assignmentId));
  } catch (error) {
    console.error(`Error deleting vehicle assignment ${assignmentId}:`, error);
    throw error;
  }
};
