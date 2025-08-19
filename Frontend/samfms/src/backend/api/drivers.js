/**
 * Driver Management API
 * All driver-related API endpoints and functions
 */
import {httpClient} from '../services/httpClient';
import {API_ENDPOINTS} from '../../config/apiConfig';

// Driver API endpoints using centralized configuration
const DRIVER_ENDPOINTS = {
  list: API_ENDPOINTS.DRIVERS.LIST,
  create: API_ENDPOINTS.DRIVERS.CREATE,
  get: API_ENDPOINTS.DRIVERS.GET,
  update: API_ENDPOINTS.DRIVERS.UPDATE,
  delete: API_ENDPOINTS.DRIVERS.DELETE,
  assign: API_ENDPOINTS.DRIVERS.ASSIGN,
  empid: API_ENDPOINTS.DRIVERS.EMPID,
  driverASS: API_ENDPOINTS.ASSIGNMENTS.GETDRIVERASSIGNMENT,
  vehicLoct: API_ENDPOINTS.LOCATIONS.GET,
  vehicEndLoc: API_ENDPOINTS.TRIPS.VEHICLETRIP,
  TRIP_PLANNING_LIST: API_ENDPOINTS.DRIVERS.TRIP_PLANNING_LIST,
  count: API_ENDPOINTS.DRIVERS.COUNT,
  finishtrip: API_ENDPOINTS.TRIPS.FINISHTRIP,
};

/**
 * Create a new driver
 * @param {Object} driverData - Driver data to create
 * @returns {Promise<Object>} Created driver data
 */
export const createDriver = async driverData => {
  try {
    const response = await httpClient.post(DRIVER_ENDPOINTS.create, driverData);
    console.log('Response for create driver: ', response);
    return response;
  } catch (error) {
    console.error('Error creating driver:', error);
    throw error;
  }
};

/**
 * Get all drivers from the trip planning service drivers collection
 * @param {Object} params - Query parameters (status, department, skip, limit)
 * @returns {Promise<Object>} Drivers list from trip planning service
 */
export const getTripPlanningDrivers = async (params = {}) => {
  try {
    console.log('Fetching drivers from trip planning service...');

    // Build query parameters
    const queryParams = {};
    if (params.status) {
      queryParams.status = params.status;
    }
    if (params.department) {
      queryParams.department = params.department;
    }
    if (params.skip !== undefined) {
      queryParams.skip = parseInt(params.skip);
    }
    if (params.limit !== undefined) {
      queryParams.limit = parseInt(params.limit);
    }

    console.log('Sending query params to trip planning drivers:', queryParams);

    const response = await httpClient.get(DRIVER_ENDPOINTS.TRIP_PLANNING_LIST, {
      params: queryParams,
    });

    console.log('Response from trip planning service:', response);

    // The trip planning service returns data in a nested structure
    if (response.data && response.data.data) {
      return response.data.data; // This contains { drivers, total, skip, limit, has_more }
    }

    return response;
  } catch (error) {
    console.error('Error fetching drivers from trip planning service:', error);
    throw error;
  }
};

export const getAllDrivers = async (filters = {}) => {
  try {
    // Ensure numeric parameters are integers
    const queryParams = {
      ...filters,
      limit: Number.parseInt(filters.limit || 100), // Ensure integer
      skip: Number.parseInt(filters.skip || 0), // Ensure integer
    };

    console.log('Sending query params to getAllDrivers:', queryParams);
    const response = await httpClient.get(DRIVER_ENDPOINTS.list, {params: queryParams});
    console.log('Response received from backend:', response);
    return response;
  } catch (error) {
    console.error('Error fetching all drivers:', error);
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

export const assignVehicle = async data => {
  try {
    console.log('Vehicle and driver data', data);
    return await httpClient.post(DRIVER_ENDPOINTS.assign, data);
  } catch (error) {
    console.error('Error assigning vehicle to driver: ', error);
    throw error;
  }
};

export const getNumberOfDrivers = async (data) => {
  try {
    const response = await httpClient.post(DRIVER_ENDPOINTS.count, data);
    return response;
  } catch (error) {
    console.error('Error fetching number of drivers:', error);
    throw error;
  }
};

export const getDriverEMPID = async security_id => {
  try {
    if (!security_id) {
      throw new Error('Security ID is required');
    }
    console.log('Security_id:', security_id);

    // FIXED: Added return statement and fixed variable name
    const response = await httpClient.get(DRIVER_ENDPOINTS.empid(security_id));
    return response; // Return the response
  } catch (error) {
    console.error('Error fetching driver employee ID:', error);
    throw error;
  }
};

export const TripFinishedStatus = async employee_id => {
  try {
    const response = await httpClient.get(DRIVER_ENDPOINTS.driverASS(employee_id));
    console.log("Response for current driver-vehicle-ass: ", response);

    const vehicle_id = response.data.data[0].vehicle_id;
    console.log("Vehicle id: ", vehicle_id);

    const current_location_response = await httpClient.get(DRIVER_ENDPOINTS.vehicLoct(vehicle_id));
    console.log("current location response: ", current_location_response);

    const end_location_response = await httpClient.get(DRIVER_ENDPOINTS.vehicEndLoc(vehicle_id));
    console.log("End location response: ", end_location_response);

    // Extract coordinates (note: coordinates are [longitude, latitude] in GeoJSON format)
    const current_location = current_location_response.data.data.location.coordinates;
    const end_location = end_location_response.data.data[0].destination.location.coordinates;

    console.log("Current location: ", current_location); // [27.985173301345533, -26.09811415363004]
    console.log("End location: ", end_location); // [27.9444444, -26.1336111]

    // Calculate distance between two points using Haversine formula
    const distance = calculateDistance(
      current_location[1], // latitude
      current_location[0], // longitude
      end_location[1],     // latitude
      end_location[0]      // longitude
    );

    console.log(`Distance to destination: ${distance.toFixed(2)} meters`);

    // Consider trip finished if within 100 meters of destination
    const ARRIVAL_THRESHOLD_METERS = 100;
    const hasArrived = distance <= ARRIVAL_THRESHOLD_METERS;

    console.log(`Has arrived at destination: ${hasArrived}`);
    return hasArrived;

  } catch (error) {
    console.error('Error fetching driver trip status:', error);
    throw error;
  }
};

/**
 * Calculate the distance between two points on Earth using the Haversine formula
 * @param {number} lat1 - Latitude of the first point
 * @param {number} lon1 - Longitude of the first point
 * @param {number} lat2 - Latitude of the second point
 * @param {number} lon2 - Longitude of the second point
 * @returns {number} Distance in meters
 */
function calculateDistance(lat1, lon1, lat2, lon2) {
  const R = 6371000; // Earth's radius in meters

  const φ1 = lat1 * Math.PI / 180; // φ, λ in radians
  const φ2 = lat2 * Math.PI / 180;
  const Δφ = (lat2 - lat1) * Math.PI / 180;
  const Δλ = (lon2 - lon1) * Math.PI / 180;

  const a = Math.sin(Δφ / 2) * Math.sin(Δφ / 2) +
    Math.cos(φ1) * Math.cos(φ2) *
    Math.sin(Δλ / 2) * Math.sin(Δλ / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

  const distance = R * c; // Distance in meters
  return distance;
}

// Alternative: Simpler but less accurate distance calculation for small distances
function calculateDistanceSimple(lat1, lon1, lat2, lon2) {
  const R = 6371000; // Earth's radius in meters
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = dLat * dLat + Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * dLon * dLon;
  return R * Math.sqrt(a);
}
