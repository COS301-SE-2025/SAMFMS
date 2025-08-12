import { httpClient } from '../services/httpClient';
import { API_ENDPOINTS } from '../../config/apiConfig';

const TRIPS_ENDPOINTS = {
  list: API_ENDPOINTS.TRIPS.LIST,
  create: API_ENDPOINTS.TRIPS.CREATE,
  update: API_ENDPOINTS.TRIPS.UPDATE,
  delete: API_ENDPOINTS.TRIPS.DELETE,
  ACTIVE: API_ENDPOINTS.TRIPS.ACTIVE,
  HISTORY: API_ENDPOINTS.TRIPS.HISTORY,
  finish: API_ENDPOINTS.TRIPS.FINISHED,
  ANALYTICS: {
    TOTALTRIPSDRIVER: API_ENDPOINTS.TRIPS.ANALYTICS.TOTALTRIPSDRIVER,
    COMPLETIONRATEDRIVERS: API_ENDPOINTS.TRIPS.ANALYTICS.COMPLETIONRATEDRIVERS,
    AVGTRIPSPERDAYDRIVERS: API_ENDPOINTS.TRIPS.ANALYTICS.AVGTRIPSPERDAYDRIVERS,
    TOTALTRIPSVEHICLES: API_ENDPOINTS.TRIPS.ANALYTICS.TOTALTRIPSVEHICLES,
    COMPLETIONRATEVEHICLES: API_ENDPOINTS.TRIPS.ANALYTICS.COMPLETIONRATEVEHICLES,
    AVGTRIPSPERDAYVEHICLES: API_ENDPOINTS.TRIPS.ANALYTICS.AVGTRIPSPERDAYVEHICLES
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

export const finishTrip = async (tripData) => {
  try {
    if(!tripData){
      throw new Error('Trip Data is required');
    }

    console.log(`Finishing trip. Payload:`, tripData);
    return await httpClient.post(TRIPS_ENDPOINTS.finish(), tripData);

  } catch (error) {
    console.error(`Error finishing trip:`, error);
    throw error;
  }
}

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

// Get driver analytics by combining separate metrics
export const getDriverAnalytics = async (timeframe = 'week') => {
  try {
    console.log(`[DriverAnalytics] Fetching data for timeframe: ${timeframe}`);
    
    // Fetch all metrics in parallel
    const [totalTripsResponse, completionRateResponse, avgTripsResponse] = await Promise.all([
      httpClient.get(`${TRIPS_ENDPOINTS.ANALYTICS.TOTALTRIPSDRIVER}?timeframe=${timeframe}`),
      httpClient.get(`${TRIPS_ENDPOINTS.ANALYTICS.COMPLETIONRATEDRIVERS}?timeframe=${timeframe}`),
      httpClient.get(`${TRIPS_ENDPOINTS.ANALYTICS.AVGTRIPSPERDAYDRIVERS}?timeframe=${timeframe}`)
    ]);

    // Combine and transform the data
    const transformedData = {
      drivers: (totalTripsResponse.data?.drivers || []).map(driver => ({
        driverName: driver.driver_name || driver.name || 'Unknown',
        completedTrips: Number(driver.completed_trips || 0),
        cancelledTrips: Number(driver.cancelled_trips || 0)
      })),
      timeframeSummary: {
        totalTrips: Number(totalTripsResponse.data?.total || 0),
        completionRate: Number(completionRateResponse.data?.rate || 0),
        averageTripsPerDay: Number(avgTripsResponse.data?.average || 0)
      }
    };

    console.log('[DriverAnalytics] Combined data:', transformedData);
    return transformedData;

  } catch (error) {
    console.error('Error fetching driver analytics:', error);
    throw error;
  }
};

// Get vehicle analytics by combining separate metrics
export const getVehicleAnalytics = async (timeframe = 'week') => {
  try {
    console.log(`[VehicleAnalytics] Fetching data for timeframe: ${timeframe}`);
    
    // Fetch all metrics in parallel
    const [totalTripsResponse, completionRateResponse, avgTripsResponse] = await Promise.all([
      httpClient.get(`${TRIPS_ENDPOINTS.ANALYTICS.TOTALTRIPSVEHICLES}?timeframe=${timeframe}`),
      httpClient.get(`${TRIPS_ENDPOINTS.ANALYTICS.COMPLETIONRATEVEHICLES}?timeframe=${timeframe}`),
      httpClient.get(`${TRIPS_ENDPOINTS.ANALYTICS.AVGTRIPSPERDAYVEHICLES}?timeframe=${timeframe}`)
    ]);

    // Combine and transform the data
    const transformedData = {
      vehicles: (totalTripsResponse.data?.vehicles || []).map(vehicle => ({
        vehicleName: vehicle.vehicle_name || vehicle.name || 'Unknown',
        totalTrips: Number(vehicle.total_trips || 0),
        totalDistance: Number(vehicle.total_distance || 0)
      })),
      timeframeSummary: {
        totalDistance: Number(totalTripsResponse.data?.total_distance || 0)
      }
    };

    console.log('[VehicleAnalytics] Combined data:', transformedData);
    return transformedData;

  } catch (error) {
    console.error('Error fetching vehicle analytics:', error);
    throw error;
  }
};


