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
  upcommingtrips: API_ENDPOINTS.TRIPS.UPCOMMINGTRIPS,
  recenttrips: API_ENDPOINTS.TRIPS.RECENTTRIPS,
  ANALYTICS: {
    DRIVERSTATS: API_ENDPOINTS.TRIPS.ANALYTICS.DRiVERSTATS,
    TOTALTRIPSDRIVER: API_ENDPOINTS.TRIPS.ANALYTICS.TOTALTRIPSDRIVER,
    COMPLETIONRATEDRIVERS: API_ENDPOINTS.TRIPS.ANALYTICS.COMPLETIONRATEDRIVERS,
    AVGTRIPSPERDAYDRIVERS: API_ENDPOINTS.TRIPS.ANALYTICS.AVGTRIPSPERDAYDRIVERS,

    TOTALTRIPSVEHICLES: API_ENDPOINTS.TRIPS.ANALYTICS.TOTALTRIPSVEHICLES,
    COMPLETIONRATEVEHICLES: API_ENDPOINTS.TRIPS.ANALYTICS.COMPLETIONRATEVEHICLES,
    AVGTRIPSPERDAYVEHICLES: API_ENDPOINTS.TRIPS.ANALYTICS.AVGTRIPSPERDAYVEHICLES,
  },
};

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

export const finishTrip = async tripData => {
  try {
    if (!tripData) {
      throw new Error('Trip Data is required');
    }

    console.log(`Finishing trip. Payload:`, tripData);
    return await httpClient.post(TRIPS_ENDPOINTS.finish(), tripData);
  } catch (error) {
    console.error(`Error finishing trip:`, error);
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
};

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
        name: trip.driver_name,
      },
      vehicle: {
        id: trip.vehicle_id,
      },
      status: determineStatus(trip.scheduled_end_time, trip.estimated_end_time),
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

export const getDriverAnalytics = async (timeframe = 'week') => {
  try {
    console.log(`[DriverAnalytics] Fetching data for timeframe: ${timeframe}`);

    // Fetch all metrics in parallel using query parameters
    const [driverStatsResponse, totalTripsResponse, completionRateResponse, avgTripsResponse] =
      await Promise.all([
        httpClient.get(`${TRIPS_ENDPOINTS.ANALYTICS.DRIVERSTATS}`, {
          params: { timeframe },
        }),
        httpClient.get(`${TRIPS_ENDPOINTS.ANALYTICS.TOTALTRIPSDRIVER}`, {
          params: { timeframe },
        }),
        httpClient.get(`${TRIPS_ENDPOINTS.ANALYTICS.COMPLETIONRATEDRIVERS}`, {
          params: { timeframe },
        }),
        httpClient.get(`${TRIPS_ENDPOINTS.ANALYTICS.AVGTRIPSPERDAYDRIVERS}`, {
          params: { timeframe },
        }),
      ]);

    console.log('trips stats response', driverStatsResponse);

    const totalTrips = totalTripsResponse.data.data.total;
    const completionRate = completionRateResponse.data.data.rate;
    const avgTripsPerDay = avgTripsResponse.data.data.average;

    // Transform driver data to match chart expectations
    const transformedDrivers = driverStatsResponse.data.data.total.map(driver => ({
      driverName: driver.driver_name,
      completedTrips: driver.completed_trips,
      cancelledTrips: driver.cancelled_trips,
    }));

    // Combine and transform the data
    const transformedData = {
      drivers: transformedDrivers,
      timeframeSummary: {
        totalTrips: Number(totalTrips || 0),
        completionRate: Number(completionRate || 0),
        averageTripsPerDay: Number(avgTripsPerDay || 0),
      },
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

    // Fetch all metrics in parallel using query parameters
    const [totalTripsResponse, completionRateResponse, avgTripsResponse] = await Promise.all([
      httpClient.get(`${TRIPS_ENDPOINTS.ANALYTICS.TOTALTRIPSVEHICLES}`, {
        params: { timeframe },
      }),
      httpClient.get(`${TRIPS_ENDPOINTS.ANALYTICS.COMPLETIONRATEVEHICLES}`, {
        params: { timeframe },
      }),
      httpClient.get(`${TRIPS_ENDPOINTS.ANALYTICS.AVGTRIPSPERDAYVEHICLES}`, {
        params: { timeframe },
      }),
    ]);

    // Combine and transform the data
    const transformedData = {
      vehicles: (totalTripsResponse.data?.vehicles || []).map(vehicle => ({
        vehicleName: vehicle.vehicle_name || vehicle.name || 'Unknown',
        totalTrips: Number(vehicle.total_trips || 0),
        totalDistance: Number(vehicle.total_distance || 0),
      })),
      timeframeSummary: {
        totalDistance: Number(totalTripsResponse.data?.total_distance || 0),
      },
    };

    console.log('[VehicleAnalytics] Combined data:', transformedData);
    return transformedData;
  } catch (error) {
    console.error('Error fetching vehicle analytics:', error);
    throw error;
  }
};

// Get upcoming trips for a specific driver
// Get upcoming trips for a specific driver
export const getUpcomingTrips = async (driverId) => {
  try {
    console.log(`Fetching upcoming trips for driver: ${driverId}`);
    const response = await httpClient.get(TRIPS_ENDPOINTS.upcommingtrips(driverId));
    console.log("Response for upcoming trips: ", response);
    
    // Extract the trips data from the nested response structure
    // Based on your log structure: response.data.data is an array
    let trips = [];
    
    if (Array.isArray(response?.data?.data)) {
      trips = response.data.data;
    } else if (Array.isArray(response?.data?.data?.data)) {
      trips = response.data.data.data;
    } else if (Array.isArray(response?.data)) {
      trips = response.data;
    }
    
    console.log("Extracted trips array:", trips); // Debug log
    console.log("Number of trips found:", trips.length); // Debug log
    
    // Transform the data to match your frontend expectations
    const transformedTrips = trips.map(trip => ({
      id: trip.id,
      name: trip.name,
      description: trip.description,
      scheduledStartTime: trip.scheduled_start_time,
      scheduledEndTime: trip.scheduled_end_time,
      actualStartTime: trip.actual_start_time,
      actualEndTime: trip.actual_end_time,
      origin: {
        name: trip.origin.name,
        coordinates: trip.origin.location.coordinates,
        address: trip.origin.address
      },
      destination: {
        name: trip.destination.name,
        coordinates: trip.destination.location.coordinates,
        address: trip.destination.address
      },
      waypoints: trip.waypoints,
      status: trip.status,
      priority: trip.priority,
      estimatedEndTime: trip.estimated_end_time,
      estimatedDistance: trip.estimated_distance,
      driverAssignment: trip.driver_assignment,
      vehicleId: trip.vehicle_id,
      constraints: trip.constraints,
      createdBy: trip.created_by,
      createdAt: trip.created_at,
      updatedAt: trip.updated_at,
      customFields: trip.custom_fields
    }));

    return {
      data: {
        trips: transformedTrips,
        count: transformedTrips.length,
        message: response?.data?.data?.message || response?.data?.message || 'Upcoming trips retrieved successfully'
      },
      status: response?.data?.status || response?.status || 'success'
    };

  } catch (error) {
    console.error('Error fetching upcoming trips:', error);
    // Return fallback data for development
    return {
      data: {
        trips: [],
        count: 0,
      },
      message: 'No upcoming trips found',
    };
  }
};

// Get recent trips for a specific driver
export const getRecentTrips = async (driverId) => {
  try {
    const response = await httpClient.get(TRIPS_ENDPOINTS.recenttrips(driverId));
    console.log("Response for recent trips: ", response)

    let trips = [];
    
    if (Array.isArray(response?.data?.data)) {
      trips = response.data.data;
    } else if (Array.isArray(response?.data?.data?.data)) {
      trips = response.data.data.data;
    } else if (Array.isArray(response?.data)) {
      trips = response.data;
    }
    
    console.log("Extracted trips array:", trips); // Debug log
    console.log("Number of trips found:", trips.length); // Debug log
    
    // Transform the data to match your frontend expectations
    const transformedTrips = trips.map(trip => ({
      id: trip.id,
      name: trip.name,
      description: trip.description,
      scheduledStartTime: trip.scheduled_start_time,
      scheduledEndTime: trip.scheduled_end_time,
      actualStartTime: trip.actual_start_time,
      actualEndTime: trip.actual_end_time,
      origin: {
        name: trip.origin.name,
        coordinates: trip.origin.location.coordinates,
        address: trip.origin.address
      },
      destination: {
        name: trip.destination.name,
        coordinates: trip.destination.location.coordinates,
        address: trip.destination.address
      },
      waypoints: trip.waypoints,
      status: trip.status,
      priority: trip.priority,
      estimatedEndTime: trip.estimated_end_time,
      estimatedDistance: trip.estimated_distance,
      driverAssignment: trip.driver_assignment,
      vehicleId: trip.vehicle_id,
      constraints: trip.constraints,
      createdBy: trip.created_by,
      createdAt: trip.created_at,
      updatedAt: trip.updated_at,
      customFields: trip.custom_fields
    }));

    return {
      data: {
        trips: transformedTrips,
        count: transformedTrips.length,
        message: response?.data?.data?.message || response?.data?.message || 'Upcoming trips retrieved successfully'
      },
      status: response?.data?.status || response?.status || 'success'
    };

  } catch (error) {
    console.error('Error fetching recent trips:', error);
    // Return fallback data for development
    return {
      data: {
        trips: [],
        count: 0,
      },
      message: 'No recent trips found',
    };
  }
};
