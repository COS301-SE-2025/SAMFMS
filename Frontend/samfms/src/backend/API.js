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
} from './api/auth';

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
};

// Driver API endpoints - Now served by Management Service
export const DRIVER_API = {
  drivers: `http://localhost:8007/api/v1/vehicles/drivers`,
  createDriver: `http://localhost:8007/api/v1/vehicles/drivers`,
  getDriver: id => `http://localhost:8007/api/v1/vehicles/drivers/${id}`,
  updateDriver: id => `http://localhost:8007/api/v1/vehicles/drivers/${id}`,
  deleteDriver: id => `http://localhost:8007/api/v1/vehicles/drivers/${id}`,
  searchDrivers: query => `http://localhost:8007/api/v1/vehicles/drivers/search/${query}`,
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
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to create vehicle');
  }

  return response.json();
};

export const getVehicles = async (params = {}) => {
  const token = getToken();
  if (!token) {
    throw new Error('No authentication token found');
  }

  const queryParams = new URLSearchParams();
  if (params.skip) queryParams.append('skip', params.skip);
  if (params.limit) queryParams.append('limit', params.limit);
  if (params.status_filter) queryParams.append('status_filter', params.status_filter);
  if (params.make_filter) queryParams.append('make_filter', params.make_filter);

  const url = `${VEHICLE_API.vehicles}${
    queryParams.toString() ? '?' + queryParams.toString() : ''
  }`;

  const response = await fetch(url, {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to fetch vehicles');
  }

  return response.json();
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
    return { success: true };
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

// RBAC and Admin Functions have been moved to ./api/auth.js
