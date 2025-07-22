import { httpClient } from '../services/httpClient';
import { API_ENDPOINTS } from '../../config/apiConfig';

// Define the endpoint for creating a trip
const TRIP_ENDPOINTS = {
  create: API_ENDPOINTS.TRIPS.CREATE, // e.g., '/trips/trips'
  active: API_ENDPOINTS.TRIPS.ACTIVE,
};

/**
 * Create a new trip
 * @param {Object} tripData - Trip data to create
 * @returns {Promise<Object>} Created trip data or error
 */
export const createTrip = async (tripData) => {
  try {
    return await httpClient.post(TRIP_ENDPOINTS.create, tripData);
  } catch (error) {
    console.error('Error creating trip:', error);
    throw error;
  }
};

/**
 * Fetch all active trips for the logged-in driver
 * @returns {Promise<Array>} List of active trips
 */
export const getActiveTrips = async () => {
  try {
    return await httpClient.get(TRIP_ENDPOINTS.active);
  } catch (error) {
    console.error('Error fetching active trips:', error);
    throw error;
  }
};