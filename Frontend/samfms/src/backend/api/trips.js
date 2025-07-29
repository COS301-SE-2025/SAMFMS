import { httpClient, HttpClient } from "../services/httpClient";
import { API_ENDPOINTS } from "../../config/apiConfig";

const TRIPS_ENDPOINTS = {
  list: API_ENDPOINTS.TRIPS.LIST,
  create: API_ENDPOINTS.TRIPS.CREATE
}

export const listTrips = async () => {
  try {
    console.log("Fetching all trips");
    return await httpClient.get(TRIPS_ENDPOINTS.list);
  } catch (error) {
    console.log("Error fetching Trips: ", error);
    throw error;
  }
}

export const createTrip = async tripData => {
  try {
    console.log("Creating trip. Payload: ", tripData);
    return await httpClient.post(TRIPS_ENDPOINTS.create, tripData);
  } catch (error) {
    console.log("Error creating Trip: ", error);
    throw error;
  }
}