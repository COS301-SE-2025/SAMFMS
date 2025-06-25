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
// import {
//   getTotalVehicles,
//   // getVehiclesInMaintenance,
//   // getFleetUtilization,
//   // getDistanceCovered,
// } from './api/analytics';

// Re-export the auth functions for backward compatibility
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
};

// Driver API endpoints - Now served by Core Service
export const DRIVER_API = {
  drivers: `${API_URL}/api/vehicles/drivers`,
  createDriver: `${API_URL}/api/vehicles/drivers`,
  getDriver: id => `${API_URL}/api/vehicles/drivers/${id}`,
  updateDriver: id => `${API_URL}/api/vehicles/drivers/${id}`,
  deleteDriver: id => `${API_URL}/api/vehicles/drivers/${id}`,
  searchDrivers: query => `${API_URL}/api/vehicles/drivers/search/${query}`,
};

// Vehicle API endpoints
export const VEHICLE_API = {
  vehicles: `${API_URL}/api/vehicles`, // has drivers variable and total variable
  createVehicle: `${API_URL}/api/vehicles`, // post version of /vehicles
  getVehicle: id => `${API_URL}/api/vehicles/${id}`,
  updateVehicle: id => `${API_URL}/api/vehicles/${id}`,
  deleteVehicle: id => `${API_URL}/api/vehicles/${id}`,
  searchVehicles: query => `${API_URL}/api/vehicles/search/${query}`,
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
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to search vehicles');
  }

  return response.json();
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

// RBAC and Admin Functions have been moved to ./api/auth.js
