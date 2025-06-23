import {API_URL, authFetch} from './API';

// Define your analytics endpoints
const ANALYTICS_API = {
    totalVehicles: `${API_URL}/api/analytics/total-vehicles`,
    vehiclesInMaintenance: `${API_URL}/api/analytics/vehicles-in-maintenance`,
    fleetUtilization: `${API_URL}/api/analytics/fleet-utilization`,
    distanceCovered: (period = 'week') => `${API_URL}/api/analytics/distance-covered?period=${period}`,
};

// Analytics functions using authFetch
export const getTotalVehicles = async () => {
    const response = await authFetch(ANALYTICS_API.totalVehicles);
    return response.json();
};

export const getVehiclesInMaintenance = async () => {
    const response = await authFetch(ANALYTICS_API.vehiclesInMaintenance);
    return response.json();
};

export const getFleetUtilization = async () => {
    const response = await authFetch(ANALYTICS_API.fleetUtilization);
    return response.json();
};

export const getDistanceCovered = async (period = 'week') => {
    const response = await authFetch(ANALYTICS_API.distanceCovered(period));
    return response.json();
};