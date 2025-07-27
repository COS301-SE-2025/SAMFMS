import { httpClient } from "../services/httpClient";
import { API_ENDPOINTS } from "../../config/apiConfig";

const LOCATIONS_ENDPOINTS = {
  list: API_ENDPOINTS.LOCATIONS.LIST,
  create: API_ENDPOINTS.LOCATIONS.CREATE,
  get: API_ENDPOINTS.LOCATIONS.GET,
  update: API_ENDPOINTS.LOCATIONS.UPDATE
};

export const listLocations = async () => {
  try {
    console.log("Fetching all locations from ", LOCATIONS_ENDPOINTS.list);
    return await httpClient.get(LOCATIONS_ENDPOINTS.list);
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

export const createLocation = async locationData => {
  try {
    return await httpClient.post(LOCATIONS_ENDPOINTS.create(locationData));
  } catch (error){
    console.log('Error creating location: ', error);
    throw error;
  }
}

export const updateLocation = async (locationID, locationData) => {
  try {
    return await httpClient.put(LOCATIONS_ENDPOINTS.update(locationID,locationData));
  } catch (error){
    console.log("Error updating location: ", error);
    throw error;
  }
}
