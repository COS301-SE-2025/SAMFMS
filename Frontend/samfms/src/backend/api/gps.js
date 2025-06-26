import { getApiHostname, authFetch } from "./auth";

export const API_URL = getApiHostname();

const GPS_API = {
  circleGeofence: `${API_URL}/geofences/circle`
}

const handleResponse = async (response, errorMessage) => {
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`${errorMessage}: ${response.status} ${response.statusText} - ${text}`);
  }
  return response.json();
}; 