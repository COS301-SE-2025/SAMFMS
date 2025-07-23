import { httpClient, HttpClient} from "../services/httpClient";
import { API_ENDPOINTS } from "../../config/apiConfig";

// Geofence API endpoints using centralized configuration
const GEOFENCES_ENDPOINTS = {
  list: API_ENDPOINTS.GEOFENCES.LIST,
  create: API_ENDPOINTS.GEOFENCES.CREATE,
};

export const listGeofences = async () => {
  try {
    return await httpClient.get(GEOFENCES_ENDPOINTS.list);
  } catch (error) {
    console.error('Error fetching Geofences: ', error);
    throw error;
  }
};

export const addGeofence = async geofencesData => {
  try {
    return await httpClient.post(GEOFENCES_ENDPOINTS.create, geofencesData);
  } catch (error) {
    console.error('Error creating geofence: ',error);
    throw error;
  }
}