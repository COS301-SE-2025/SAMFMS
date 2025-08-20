import { API_ENDPOINTS } from '../../config/apiConfig';
import { httpClient } from '../services/httpClient';

// Geofence API endpoints using centralized configuration
const GEOFENCES_ENDPOINTS = {
  list: API_ENDPOINTS.GEOFENCES.LIST,
  create: API_ENDPOINTS.GEOFENCES.CREATE,
  update: API_ENDPOINTS.GEOFENCES.UPDATE,
  delete: API_ENDPOINTS.GEOFENCES.DELETE,
};

export const listGeofences = async () => {
  try {
    console.log('[Geofences API] Fetching all geofences from:', GEOFENCES_ENDPOINTS.list);
    const response =  await httpClient.get(GEOFENCES_ENDPOINTS.list);
    console.log("Geofences list response: ", response)
    return response;
  } catch (error) {
    console.error('Error fetching Geofences: ', error);
    throw error;
  }
};

export const getGeofence = async (geofence_id) => {
  try {
    console.log(`[Geofences API] Fetching geofence with ID: ${geofence_id}`);
    
    // Await the listGeofences call to get the actual data
    const geofencesResponse = await listGeofences();
    
    // Extract the geofences array from the nested response structure
    const geofences = geofencesResponse?.data?.data || [];
    
    // Filter to find the geofence with matching ID
    const targetGeofence = geofences.find(geofence => geofence.id === geofence_id);
    
    if (targetGeofence) {
      console.log(`Found geofence:`, targetGeofence);
      return targetGeofence;
    } else {
      console.log(`No geofence found with ID: ${geofence_id}`);
      return null;
    }
    
  } catch (error) {
    console.error(`Error fetching geofence for ${geofence_id}: `, error);
    throw error;
  }
};

export const addGeofence = async geofencesData => {
  try {
    console.log('[Geofences API] Creating geofence. Payload:', geofencesData);
    console.log('[Geofences API] Endpoint:', GEOFENCES_ENDPOINTS.create);
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
    console.log('[Geofences API] Endpoint:', GEOFENCES_ENDPOINTS.update(geofenceID));
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
    console.log('[Geofences API] Endpoint:', GEOFENCES_ENDPOINTS.delete(geofenceID));
    return await httpClient.delete(GEOFENCES_ENDPOINTS.delete(geofenceID));
  } catch (error) {
    console.error(`Error deleting geofence ${geofenceID}:`, error);
    throw error;
  }
};
