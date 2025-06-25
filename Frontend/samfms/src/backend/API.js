// Import all authentication-related functionality from the auth.js file
import {
  API_URL,
  AUTH_API as API,
  getToken,
  getCurrentUser,
  isAuthenticated,
  authFetch,
  login,
  signup,
  logout,
  logoutFromAllDevices,
  refreshAuthToken,
  changePassword,
  deleteAccount,
  updatePreferences,
  inviteUser,
  createUserManually, // Import the new function
  listUsers,
  updateUserPermissions,
  getRoles,
  verifyPermission,
  hasPermission,
  hasRole,
  hasAnyRole,
  getUserInfo,
  checkUserExistence,
  clearUserExistenceCache,
  updateUserProfile,
  uploadProfilePicture,
  clearUsersCache,
  clearRolesCache,
  clearAllAuthCache,
  fetchWithTimeout,
} from './api/auth';

// import the functions from analytics.js
import {
  getTotalVehicles,
  getFleetUtilization,
  getVehicleUsage,
  getAssignmentMetrics,
  getMaintenanceAnalytics,
  getDriverPerformance,
  getCostAnalytics,
  getStatusBreakdown,
  getIncidentStatistics,
  getDepartmentLocationAnalytics,
} from './api/analytics';

// Re-export the auth and analytics functions for backward compatibility
export {
  API_URL,
  API,
  getToken,
  getCurrentUser,
  isAuthenticated,
  authFetch,
  login,
  signup,
  logout,
  logoutFromAllDevices,
  refreshAuthToken,
  changePassword,
  deleteAccount,
  updatePreferences,
  inviteUser,
  createUserManually, // Export the new function
  listUsers,
  updateUserPermissions,
  getRoles,
  verifyPermission,
  hasPermission,
  hasRole,
  hasAnyRole,
  getUserInfo,
  checkUserExistence,
  updateUserProfile,
  uploadProfilePicture,
  clearUserExistenceCache,
  clearUsersCache,
  clearRolesCache,
  clearAllAuthCache,
  getTotalVehicles,
  getFleetUtilization,
  getVehicleUsage,
  getAssignmentMetrics,
  getMaintenanceAnalytics,
  getDriverPerformance,
  getCostAnalytics,
  getStatusBreakdown,
  getIncidentStatistics,
  getDepartmentLocationAnalytics,
};

// Driver API endpoints - Now served by Core Service
export const DRIVER_API = {
  drivers: `${API_URL}/vehicles/drivers`,
  createDriver: `${API_URL}/vehicles/drivers`,
  getDriver: id => `${API_URL}/vehicles/drivers/${id}`,
  updateDriver: id => `${API_URL}/vehicles/drivers/${id}`,
  deleteDriver: id => `${API_URL}/vehicles/drivers/${id}`,
  searchDrivers: query => `${API_URL}/vehicles/drivers/search/${query}`,
};

// Vehicle API endpoints
export const VEHICLE_API = {
  vehicles: `${API_URL}/vehicles`,
  createVehicle: `${API_URL}/vehicles`,
  getVehicle: id => `${API_URL}/vehicles/${id}`,
  updateVehicle: id => `${API_URL}/vehicles/${id}`,
  deleteVehicle: id => `${API_URL}/vehicles/${id}`,
  searchVehicles: query => `${API_URL}/vehicles/search/${query}`,
};

// Vehicle Assignment API endpoints
export const VEHICLE_ASSIGNMENT_API = {
  assignments: `${API_URL}/vehicle-assignments`,
  createAssignment: `${API_URL}/vehicle-assignments`,
  getAssignment: id => `${API_URL}/vehicle-assignments/${id}`,
  updateAssignment: id => `${API_URL}/vehicle-assignments/${id}`,
  deleteAssignment: id => `${API_URL}/vehicle-assignments/${id}`,
};

// Plugins API endpoints
export const PLUGIN_API = {
  plugins: `${API_URL}/service_presence`,
};

// Driver API functions
export const createDriver = async driverData => {
  const token = getToken();
  if (!token) {
    throw new Error('No authentication token found');
  }

  const response = await fetch(DRIVER_API.createDriver, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(driverData),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to create driver');
  }

  return response.json();
};

export const getDrivers = async (params = {}) => {
  const token = getToken();
  if (!token) {
    throw new Error('No authentication token found');
  }

  const queryParams = new URLSearchParams();
  if (params.skip) queryParams.append('skip', params.skip);
  if (params.limit) queryParams.append('limit', params.limit);
  if (params.status_filter) queryParams.append('status_filter', params.status_filter);
  if (params.department_filter) queryParams.append('department_filter', params.department_filter);

  const url = `${DRIVER_API.drivers}${queryParams.toString() ? '?' + queryParams.toString() : ''}`;

  const response = await fetch(url, {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to fetch drivers');
  }

  return response.json();
};

export const getDriver = async driverId => {
  const token = getToken();
  if (!token) {
    throw new Error('No authentication token found');
  }

  // Validate driver ID
  if (!driverId) {
    throw new Error('No driver ID provided');
  }

  // Use the provided ID (could be either MongoDB ObjectId or employee ID)
  const response = await fetch(DRIVER_API.getDriver(driverId), {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to fetch driver');
  }

  return response.json();
};

export const updateDriver = async (driverId, updateData) => {
  const token = getToken();
  if (!token) {
    throw new Error('No authentication token found');
  }

  // Validate driver ID
  if (!driverId) {
    throw new Error('No driver ID provided');
  }

  // Use the provided ID (could be either MongoDB ObjectId or employee ID)
  const response = await fetch(DRIVER_API.updateDriver(driverId), {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(updateData),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to update driver');
  }

  return response.json();
};

export const deleteDriver = async driverId => {
  const token = getToken();
  if (!token) {
    throw new Error('No authentication token found');
  }

  // Validate driver ID
  if (!driverId) {
    throw new Error('No driver ID provided');
  }

  // Use the provided ID (could be either MongoDB ObjectId or employee ID)
  const response = await fetch(DRIVER_API.deleteDriver(driverId), {
    method: 'DELETE',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to delete driver');
  }

  return response.json();
};

export const searchDrivers = async query => {
  const token = getToken();
  if (!token) {
    throw new Error('No authentication token found');
  }

  const response = await fetch(DRIVER_API.searchDrivers(encodeURIComponent(query)), {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to search drivers');
  }

  return response.json();
};

// Vehicle API functions
export const createVehicle = async vehicleData => {
  return await apiCallWithTokenRefresh(async () => {
    const token = getToken();
    if (!token) {
      throw new Error('No authentication token found');
    }

    const response = await fetch(VEHICLE_API.createVehicle, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(vehicleData),
    });

    if (!response.ok) {
      throw await handleErrorResponse(response);
    }

    return response.json();
  });
};

export const getVehicles = async (params = {}) => {
  return await apiCallWithTokenRefresh(async () => {
    const token = getToken();
    if (!token) {
      throw new Error('No authentication token found');
    }

    const queryParams = new URLSearchParams();
    if (params.skip) queryParams.append('skip', params.skip);
    if (params.limit) queryParams.append('limit', params.limit);
    if (params.status_filter) queryParams.append('status_filter', params.status_filter);
    if (params.make_filter) queryParams.append('make_filter', params.make_filter);

    const url = `${VEHICLE_API.vehicles}${queryParams.toString() ? '?' + queryParams.toString() : ''
      }`;

    const response = await fetch(url, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw await handleErrorResponse(response);
    }

    return response.json();
  });
};

export const getVehicle = async vehicleId => {
  const token = getToken();
  if (!token) {
    throw new Error('No authentication token found');
  }

  const response = await fetch(VEHICLE_API.getVehicle(vehicleId), {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to fetch vehicle');
  }

  return response.json();
};

export const updateVehicle = async (vehicleId, updateData) => {
  const token = getToken();
  if (!token) {
    throw new Error('No authentication token found');
  }

  const response = await fetch(VEHICLE_API.updateVehicle(vehicleId), {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(updateData),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to update vehicle');
  }

  return response.json();
};

export const deleteVehicle = async vehicleId => {
  const token = getToken();
  if (!token) {
    throw new Error('No authentication token found');
  }

  const response = await fetch(VEHICLE_API.deleteVehicle(vehicleId), {
    method: 'DELETE',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    try {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to delete vehicle');
    } catch (e) {
      throw new Error(`Failed to delete vehicle: ${response.statusText}`);
    }
  }
  // Try to parse JSON response, but don't fail if there's no content
  try {
    return await response.json();
  } catch (e) {
    // If no JSON is returned, return a success object
    return {success: true};
  }
};

export const searchVehicles = async query => {
  const token = getToken();
  if (!token) {
    throw new Error('No authentication token found');
  }

  const response = await fetch(VEHICLE_API.searchVehicles(encodeURIComponent(query)), {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    try {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to search vehicles');
    } catch (e) {
      throw new Error(`Failed to search vehicles: ${response.statusText}`);
    }
  }

  const result = await response.json();
  // Return the vehicles array or the whole result if it's already an array
  return result.vehicles || result || [];
};

// Invitation management functions
export const sendInvitation = async invitationData => {
  const response = await authFetch('/auth/invite-user', {
    method: 'POST',
    body: JSON.stringify(invitationData),
  });
  return response;
};

export const getPendingInvitations = async () => {
  const response = await authFetch('/auth/invitations');
  return response;
};

export const resendInvitation = async email => {
  const response = await authFetch('/auth/resend-invitation', {
    method: 'POST',
    body: JSON.stringify({email}),
  });
  return response;
};

export const cancelInvitation = async email => {
  const response = await authFetch(`/admin/cancel-invitation?email=${encodeURIComponent(email)}`, {
    method: 'DELETE',
  });
  return response;
};

// Public endpoints for user activation (no auth required)
export const verifyInvitationOTP = async (email, otp) => {
  const response = await fetchWithTimeout(`${API_URL}/auth/verify-otp`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({email, otp}),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to verify OTP');
  }

  return await response.json();
};

export const completeUserRegistration = async (email, otp, username, password) => {
  const response = await fetchWithTimeout(`${API_URL}/auth/complete-registration`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({email, otp, username, password}),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to complete registration');
  }

  return await response.json();
};

// Enhanced API call wrapper with automatic token refresh
const apiCallWithTokenRefresh = async (apiCall, maxRetries = 1) => {
  let retries = 0;

  while (retries <= maxRetries) {
    try {
      return await apiCall();
    } catch (error) {
      // Check if error is due to token expiration
      if (
        error.message.includes('401') ||
        error.message.includes('Unauthorized') ||
        error.message.includes('Token expired') ||
        error.message.includes('Invalid token')
      ) {
        if (retries < maxRetries) {
          try {
            // Attempt to refresh token
            await refreshAuthToken();
            retries++;
            continue; // Retry the API call
          } catch (refreshError) {
            // Token refresh failed, redirect to login
            console.error('Token refresh failed:', refreshError);
            logout();
            throw new Error('Session expired. Please log in again.');
          }
        }
      }

      // Re-throw the original error if not token-related or retries exceeded
      throw error;
    }
  }
};

// Enhanced error response handler
const handleErrorResponse = async response => {
  const contentType = response.headers.get('content-type');
  let errorData = {};

  try {
    if (contentType && contentType.includes('application/json')) {
      errorData = await response.json();
    } else {
      errorData = {message: (await response.text()) || 'Unknown error occurred'};
    }
  } catch (parseError) {
    errorData = {message: 'Failed to parse error response'};
  }

  // Standardized error structure
  const error = new Error(errorData.detail || errorData.message || 'Request failed');
  error.status = response.status;
  error.statusText = response.statusText;
  error.errorData = errorData;

  return error;
};

// Vehicle Assignment API functions
export const getVehicleAssignments = async (params = {}) => {
  const token = getToken();
  if (!token) {
    throw new Error('No authentication token found');
  }

  const queryParams = new URLSearchParams();
  if (params.skip) queryParams.append('skip', params.skip);
  if (params.limit) queryParams.append('limit', params.limit);
  if (params.vehicle_id) queryParams.append('vehicle_id', params.vehicle_id);
  if (params.driver_id) queryParams.append('driver_id', params.driver_id);

  const url = `${VEHICLE_ASSIGNMENT_API.assignments}${queryParams.toString() ? '?' + queryParams.toString() : ''}`;

  const response = await fetch(url, {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw await handleErrorResponse(response);
  }

  return response.json();
};

export const createVehicleAssignment = async assignmentData => {
  const token = getToken();
  if (!token) {
    throw new Error('No authentication token found');
  }

  const response = await fetch(VEHICLE_ASSIGNMENT_API.createAssignment, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(assignmentData),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to create vehicle assignment');
  }

  return response.json();
};

export const updateVehicleAssignment = async (assignmentId, updateData) => {
  const token = getToken();
  if (!token) {
    throw new Error('No authentication token found');
  }

  const response = await fetch(VEHICLE_ASSIGNMENT_API.updateAssignment(assignmentId), {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(updateData),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to update vehicle assignment');
  }

  return response.json();
};

export const deleteVehicleAssignment = async assignmentId => {
  const token = getToken();
  if (!token) {
    throw new Error('No authentication token found');
  }

  const response = await fetch(VEHICLE_ASSIGNMENT_API.deleteAssignment(assignmentId), {
    method: 'DELETE',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    try {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to delete vehicle assignment');
    } catch (e) {
      throw new Error(`Failed to delete vehicle assignment: ${response.statusText}`);
    }
  }

  try {
    return await response.json();
  } catch (e) {
    return {success: true};
  }
};

// uses the services_presence endpoint in plugins
export const getPlugins = async () => {
  const token = getToken();
  if (!token) {
    throw new Error('No authentication token found');
  }

  const response = await fetch(PLUGIN_API.plugins, {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to fetch plugins');
  }

  return response.json();
};

// RBAC and Admin Functions have been moved to ./api/auth.js
