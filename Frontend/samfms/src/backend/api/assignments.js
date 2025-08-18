/**
 * Vehicle Assignment Management API
 * All vehicle assignment-related API endpoints and functions
 * Enhanced integration with Management Service and standardized error handling
 */
import { httpClient } from '../services/httpClient';
import { API_ENDPOINTS, buildApiUrl } from '../../config/apiConfig';
import {
  withRetry,
  handleApiResponse,
  parseApiError,
  validateRequiredFields,
  ERROR_TYPES,
} from '../../utils/errorHandler';

// Vehicle Assignment API endpoints using centralized configuration
const ASSIGNMENT_ENDPOINTS = {
  list: API_ENDPOINTS.ASSIGNMENTS.LIST,
  create: API_ENDPOINTS.ASSIGNMENTS.CREATE,
  update: API_ENDPOINTS.ASSIGNMENTS.UPDATE,
  delete: API_ENDPOINTS.ASSIGNMENTS.DELETE,
  metrics: buildApiUrl('/analytics/assignment-metrics'),
  complete: API_ENDPOINTS.ASSIGNMENTS.COMPLETE,
  cancel: API_ENDPOINTS.ASSIGNMENTS.CANCEL,
};

/**
 * Get list of vehicle assignments with optional filters
 * @param {Object} params - Query parameters (skip, limit, vehicle_id, driver_id)
 * @returns {Promise<Object>} Assignments list with pagination info
 */
export const getVehicleAssignments = async (params = {}) => {
  return withRetry(async () => {
    const queryParams = new URLSearchParams();
    if (params.skip) queryParams.append('skip', params.skip);
    if (params.limit) queryParams.append('limit', params.limit);
    if (params.vehicle_id) queryParams.append('vehicle_id', params.vehicle_id);
    if (params.driver_id) queryParams.append('driver_id', params.driver_id);

    const endpoint = `${ASSIGNMENT_ENDPOINTS.list}${
      queryParams.toString() ? '?' + queryParams.toString() : ''
    }`;

    const response = await httpClient.get(endpoint);
    return handleApiResponse(response);
  });
};

/**
 * Create a new vehicle assignment
 * @param {Object} assignmentData - Assignment data to create
 * @returns {Promise<Object>} Created assignment data
 */
export const createVehicleAssignment = async assignmentData => {
  validateRequiredFields(assignmentData, ['vehicle_id', 'driver_id']);

  return withRetry(
    async () => {
      const response = await httpClient.post(ASSIGNMENT_ENDPOINTS.create, assignmentData);
      return handleApiResponse(response);
    },
    { maxRetries: 1 }
  );
};

/**
 * Update a vehicle assignment
 * @param {string} assignmentId - Assignment ID
 * @param {Object} updateData - Data to update
 * @returns {Promise<Object>} Updated assignment data
 */
export const updateVehicleAssignment = async (assignmentId, updateData) => {
  if (!assignmentId) {
    throw parseApiError({
      response: {
        status: 400,
        data: { message: 'Assignment ID is required', error_code: ERROR_TYPES.VALIDATION },
      },
    });
  }

  return withRetry(
    async () => {
      const response = await httpClient.put(ASSIGNMENT_ENDPOINTS.update(assignmentId), updateData);
      return handleApiResponse(response);
    },
    { maxRetries: 1 }
  );
};

/**
 * Delete a vehicle assignment
 * @param {string} assignmentId - Assignment ID
 * @returns {Promise<Object>} Deletion confirmation
 */
export const deleteVehicleAssignment = async assignmentId => {
  if (!assignmentId) {
    throw parseApiError({
      response: {
        status: 400,
        data: { message: 'Assignment ID is required', error_code: ERROR_TYPES.VALIDATION },
      },
    });
  }

  return withRetry(
    async () => {
      const response = await httpClient.delete(ASSIGNMENT_ENDPOINTS.delete(assignmentId));
      return handleApiResponse(response);
    },
    { maxRetries: 1 }
  );
};

/**
 * Complete a vehicle assignment
 * @param {string} assignmentId - Assignment ID to complete
 * @param {Object} completionData - Completion data (notes, completion time, etc.)
 * @returns {Promise<Object>} Updated assignment data
 */
export const completeVehicleAssignment = async (assignmentId, completionData = {}) => {
  if (!assignmentId) {
    throw parseApiError({
      response: {
        status: 400,
        data: { message: 'Assignment ID is required', error_code: ERROR_TYPES.VALIDATION },
      },
    });
  }

  return withRetry(
    async () => {
      const endpoint = ASSIGNMENT_ENDPOINTS.complete(assignmentId);
      const response = await httpClient.put(endpoint, completionData);
      return handleApiResponse(response);
    },
    { maxRetries: 1 }
  );
};

/**
 * Cancel a vehicle assignment
 * @param {string} assignmentId - Assignment ID to cancel
 * @param {Object} cancellationData - Cancellation data (reason, cancellation time, etc.)
 * @returns {Promise<Object>} Updated assignment data
 */
export const cancelVehicleAssignment = async (assignmentId, cancellationData = {}) => {
  if (!assignmentId) {
    throw parseApiError({
      response: {
        status: 400,
        data: { message: 'Assignment ID is required', error_code: ERROR_TYPES.VALIDATION },
      },
    });
  }

  return withRetry(
    async () => {
      const endpoint = ASSIGNMENT_ENDPOINTS.cancel(assignmentId);
      const response = await httpClient.put(endpoint, cancellationData);
      return handleApiResponse(response);
    },
    { maxRetries: 1 }
  );
};

/**
 * Get assignment metrics and analytics
 * @param {boolean} useCache - Whether to use cached data
 * @returns {Promise<Object>} Assignment metrics data
 */
export const getAssignmentAnalytics = async (useCache = true) => {
  return withRetry(async () => {
    const url = `${ASSIGNMENT_ENDPOINTS.metrics}?use_cache=${useCache}`;
    const response = await httpClient.get(url);
    return handleApiResponse(response);
  });
};

/**
 * Get assignments for a specific vehicle
 * @param {string} vehicleId - Vehicle ID
 * @param {string} status - Optional status filter
 * @returns {Promise<Object>} Vehicle assignments
 */
export const getVehicleAssignmentsByVehicle = async (vehicleId, status = null) => {
  if (!vehicleId) {
    throw parseApiError({
      response: {
        status: 400,
        data: { message: 'Vehicle ID is required', error_code: ERROR_TYPES.VALIDATION },
      },
    });
  }

  const params = { vehicle_id: vehicleId };
  if (status) params.status = status;

  return await getVehicleAssignments(params);
};

/**
 * Get assignments for a specific driver
 * @param {string} driverId - Driver ID
 * @param {string} status - Optional status filter
 * @returns {Promise<Object>} Driver assignments
 */
export const getVehicleAssignmentsByDriver = async (driverId, status = null) => {
  if (!driverId) {
    throw parseApiError({
      response: {
        status: 400,
        data: { message: 'Driver ID is required', error_code: ERROR_TYPES.VALIDATION },
      },
    });
  }

  const params = { driver_id: driverId };
  if (status) params.status = status;

  return await getVehicleAssignments(params);
};
