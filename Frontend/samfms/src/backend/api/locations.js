import { httpClient } from "../services/httpClient";
import { API_ENDPOINTS } from "../../config/apiConfig";

const LOCATIONS_ENDPOINTS = {
  list: API_ENDPOINTS.LOCATIONS.LIST,
  create: API_ENDPOINTS.LOCATIONS.CREATE,
  get: API_ENDPOINTS.LOCATIONS.GET,
  update: API_ENDPOINTS.LOCATIONS.UPDATE,
  delete: API_ENDPOINTS.LOCATIONS.DELETE,
  vehicleLoc: API_ENDPOINTS.LOCATIONS.VEHICLELOC,
};

export const listLocations = async () => {
  try {
    const response = httpClient.get(LOCATIONS_ENDPOINTS.list);
    //console.log("Fetched all locations from ", response);
    return response;
  } catch (error) {
    console.error('Error fetching locations: ', error)
    throw error;
  }
};

export const getLocation = async (locationID) => {
  try {
    return await httpClient.get(LOCATIONS_ENDPOINTS.get(locationID));
  } catch (error) {
    console.log('Error fetchin location : ', error);
    throw error;
  }
};

export const getVehicleLocation = async (vehicle_id) => {
  try {
    console.log("Received id: ", vehicle_id)
    const response = await httpClient.get(LOCATIONS_ENDPOINTS.vehicleLoc(vehicle_id));
    console.log("Vehicle location resposne: ",response);

    return response.data.data
  } catch (error) {
    console.log("Error fetching vehicle location: ", error);
    throw error;
  }
}

export const createLocation = async locationData => {
  try {
    return await httpClient.post(LOCATIONS_ENDPOINTS.create(locationData));
  } catch (error) {
    console.log('Error creating location: ', error);
    throw error;
  }
}

export const updateLocation = async (locationData) => {
  try {
    return await httpClient.post(LOCATIONS_ENDPOINTS.update(locationData));
  } catch (error) {
    console.log("Error updating location: ", error);
    throw error;
  }
}

export const deleteLocation = async vehicleID => {
  try {
    if (!vehicleID) {
      throw new Error('Vehicle ID is required');
    }
    console.log(`[Geofences API] Deleting location of vehicle ${vehicleID}`);
    console.log("[Geofences API] Endpoint:", LOCATIONS_ENDPOINTS.delete(vehicleID));
    return await httpClient.delete(LOCATIONS_ENDPOINTS.delete(vehicleID));
  } catch (error) {
    console.error(`Error deleting vehicle location ${vehicleID}:`, error);
    throw error;
  }
}
