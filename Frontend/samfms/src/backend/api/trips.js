import { httpClient } from '../services/httpClient';
import { API_ENDPOINTS } from '../../config/apiConfig';

const TRIPS_ENDPOINTS = {
  list: API_ENDPOINTS.TRIPS.LIST,
  create: API_ENDPOINTS.TRIPS.CREATE,
  update: API_ENDPOINTS.TRIPS.UPDATE,
  delete: API_ENDPOINTS.TRIPS.DELETE,
  ACTIVE: API_ENDPOINTS.TRIPS.ACTIVE,
  HISTORY: API_ENDPOINTS.TRIPS.HISTORY,
  ANALYTICS: {
    DRIVERS: API_ENDPOINTS.TRIPS.ANALYTICS.DRIVERS,
    VEHICLES: API_ENDPOINTS.TRIPS.ANALYTICS.VEHICLES
  }
}

export const listTrips = async () => {
  try {
    console.log('Fetching all trips');
    return await httpClient.get(TRIPS_ENDPOINTS.list);
  } catch (error) {
    console.log('Error fetching Trips: ', error);
    throw error;
  }
};

export const createTrip = async tripData => {
  try {
    console.log('Creating trip. Payload: ', tripData);
    return await httpClient.post(TRIPS_ENDPOINTS.create, tripData);
  } catch (error) {
    console.log('Error creating Trip: ', error);
    throw error;
  }
};

export const updateTrip = async (tripID, tripData) => {
  try {
    if (!tripID) {
      throw new Error('Trip ID is required');
    }
    console.log(`Updating trip ${tripID}. Payload:`, tripData);
    return await httpClient.put(TRIPS_ENDPOINTS.update(tripID), tripData);
  } catch (error) {
    console.error(`Error updating trip ${tripID}:`, error);
    throw error;
  }
};

export const deleteGeofence = async tripID => {
  try {
    if (!tripID) {
      throw new Error('Trip ID is required');
    }
    console.log(`Deleting trip ${tripID}`);
    console.log('Endpoint:', TRIPS_ENDPOINTS.delete(tripID));
    return await httpClient.delete(TRIPS_ENDPOINTS.delete(tripID));
  } catch (error) {
    console.error(`Error deleting trip ${tripID}:`, error);
    throw error;
  }
}

// Replace your getActiveTrips function with this:
export const getActiveTrips = async () => {
  try {
    const response = await httpClient.get(TRIPS_ENDPOINTS.ACTIVE);
    
    // Debug: Check what the API is actually returning
    console.log('API Response:', response);
    console.log('Response data:', response.data);
    
    // Handle different possible response structures
    let tripsArray;
    if (Array.isArray(response.data)) {
      tripsArray = response.data;
    } else if (response.data && Array.isArray(response.data.trips)) {
      tripsArray = response.data.trips;
    } else if (response.data && Array.isArray(response.data.data)) {
      tripsArray = response.data.data;
    } else {
      console.error('Unexpected API response structure:', response.data);
      return { trips: [] }; // Return empty array as fallback
    }
    
    const transformedTrips = tripsArray.map(trip => ({
      id: trip._id,
      name: trip.name,
      startTime: trip.start_time,
      estimatedEndTime: trip.estimated_end_time,
      scheduledEndTime: trip.scheduled_end_time,
      driver: {
        id: trip.driver_id,
        name: trip.driver_name
      },
      vehicle: {
        id: trip.vehicle_id
      },
      status: determineStatus(trip.scheduled_end_time, trip.estimated_end_time)
    }));
    
    return { trips: transformedTrips };
  } catch (error) {
    console.error('Error fetching active trips:', error);
    throw error;
  }
};

const determineStatus = (scheduledEnd, estimatedEnd) => {
  if (!scheduledEnd || !estimatedEnd) return 'in_progress';
  
  const scheduled = new Date(scheduledEnd);
  const estimated = new Date(estimatedEnd);
  
  if (estimated > scheduled) {
    return 'delayed';
  }
  return 'on_time';
};

// Get trips history with pagination
export const getTripsHistory = async (page = 1, limit = 10) => {
  try {
    return await httpClient.get(`${TRIPS_ENDPOINTS.HISTORY}?page=${page}&limit=${limit}`);
  } catch (error) {
    console.error('Error fetching trips history:', error);
    throw error;
  }
};

// Get driver analytics
// Get driver analytics
export const getDriverAnalytics = async (timeframe = 'week') => {
  try {
    console.log(`[DriverAnalytics] Fetching data for timeframe: ${timeframe}`);
    const response = await httpClient.get(`${TRIPS_ENDPOINTS.ANALYTICS.DRIVERS}?timeframe=${timeframe}`);
    
    console.log('[DriverAnalytics] Raw response from backend:', response.data);

    // Transform/validate the response data
    const transformedData = {
      drivers: (response.data?.drivers || []).map(driver => ({
        driverId: driver.driverId || driver.driver_id || driver._id,
        driverName: driver.driverName || driver.driver_name || driver.name,
        completedTrips: Number(driver.completedTrips || 0),
        cancelledTrips: Number(driver.cancelledTrips || 0),
        totalHours: Number(driver.totalHours || 0)
      })),
      timeframeSummary: {
        totalTrips: Number(response.data?.timeframeSummary?.totalTrips || 0),
        completionRate: Number(response.data?.timeframeSummary?.completionRate || 0),
        averageTripsPerDay: Number(response.data?.timeframeSummary?.averageTripsPerDay || 0)
      }
    };

    console.log('[DriverAnalytics] Transformed data:', transformedData);

    return transformedData;
  } catch (error) {
    console.error('Error fetching driver analytics:', error);
    throw error;
  }
};

// Get vehicle analytics
export const getVehicleAnalytics = async (timeframe = 'week') => {
  try {
    console.log(`[VehicleAnalytics] Fetching data for timeframe: ${timeframe}`);
    const response = await httpClient.get(`${TRIPS_ENDPOINTS.ANALYTICS.VEHICLES}?timeframe=${timeframe}`);
    
    console.log('[VehicleAnalytics] Raw response from backend:', response.data);

    // Transform/validate the response data
    const transformedData = {
      vehicles: (response.data?.vehicles || []).map(vehicle => ({
        vehicleId: vehicle.vehicleId || vehicle.vehicle_id || vehicle._id,
        vehicleName: vehicle.vehicleName || vehicle.vehicle_name || vehicle.name,
        totalTrips: Number(vehicle.totalTrips || 0),
        totalDistance: Number(vehicle.totalDistance || 0)
      })),
      timeframeSummary: {
        totalDistance: Number(response.data?.timeframeSummary?.totalDistance || 0)
      }
    };

    console.log('[VehicleAnalytics] Transformed data:', transformedData);

    return transformedData;
  } catch (error) {
    console.error('Error fetching vehicle analytics:', error);
    throw error;
  }
};
