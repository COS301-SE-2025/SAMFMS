import { httpClient, HttpClient } from "../services/httpClient";
import { API_ENDPOINTS } from "../../config/apiConfig";

// Geofence API endpoints using centralized configuration
const GEOFENCES_ENDPOINTS = {
  list: API_ENDPOINTS.GEOFENCES.LIST,
  create: API_ENDPOINTS.GEOFENCES.CREATE,
  update: API_ENDPOINTS.GEOFENCES.UPDATE,
  delete: API_ENDPOINTS.GEOFENCES.DELETE
};

export const listGeofences = async () => {
  try {
    console.log("[Geofences API] Fetching all geofences from:", GEOFENCES_ENDPOINTS.list);
    return await httpClient.get(GEOFENCES_ENDPOINTS.list);
  } catch (error) {
    console.error('Error fetching Geofences: ', error);
    throw error;
  }
};

export const addGeofence = async geofencesData => {
  try {
    console.log("[Geofences API] Creating geofence. Payload:", geofencesData);
    console.log("[Geofences API] Endpoint:", GEOFENCES_ENDPOINTS.create);
    return await httpClient.post(GEOFENCES_ENDPOINTS.create, geofencesData);
  } catch (error) {
    console.error('Error creating geofence: ', error);
    throw error;
  }
};

export const updateGeofence = async (geofenceID, geofenceData) => {
  try {
    if (!geofenceID) {
      throw new Error('Geofence ID is required');
    }
    console.log(`[Geofences API] Updating geofence ${geofenceID}. Payload:`, geofenceData);
    console.log("[Geofences API] Endpoint:", GEOFENCES_ENDPOINTS.update(geofenceID));
    return await httpClient.put(GEOFENCES_ENDPOINTS.update(geofenceID), geofenceData);
  } catch (error) {
    console.error(`Error updating geofence ${geofenceID}:`, error);
    throw error;
  }
};

export const deleteGeofence = async geofenceID => {
  try {
    if (!geofenceID) {
      throw new Error('Geofence ID is required');
    }
    console.log(`[Geofences API] Deleting geofence ${geofenceID}`);
    console.log("[Geofences API] Endpoint:", GEOFENCES_ENDPOINTS.delete(geofenceID));
    return await httpClient.delete(GEOFENCES_ENDPOINTS.delete(geofenceID));
  } catch (error) {
    console.error(`Error deleting geofence ${geofenceID}:`, error);
    throw error;
  }
};
