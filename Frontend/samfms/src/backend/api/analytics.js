import {
    getApiHostname,
    authFetch
} from './auth';

const hostname = getApiHostname(); // Core service port
export const API_URL = `http://${hostname}`;

// Define your analytics endpoints
const ANALYTICS_API = {
    totalVehicles: `${API_URL}/analytics/fleet`,
    // vehiclesInMaintenance: `${API_URL}/analytics/vehicles-in-maintenance`,
    // fleetUtilization: `${API_URL}/analytics/fleet-utilization`,
    // distanceCovered: (period = 'week') => `${API_URL}/analytics/distance-covered?period=${period}`,
};

export const getTotalVehicles = async () => {
    try {
        const response = await authFetch(ANALYTICS_API.totalVehicles, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        if (!response.ok) {
            throw new Error('Failed to fetch total vehicles');
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching total vehicles:', error);
        throw error;
    }
}

// export const getVehiclesInMaintenance = async () => {
//     try {
//         const response = await fetch(ANALYTICS_API.vehiclesInMaintenance);
//         if (!response.ok) {
//             throw new Error('Failed to fetch vehicles in maintenance');
//         }
//         return await response.json();
//     } catch (error) {
//         console.error('Error fetching vehicles in maintenance:', error);
//         throw error;
//     }
// };

// export const getFleetUtilization = async () => {
//     try {
//         const response = await fetch(ANALYTICS_API.fleetUtilization);
//         if (!response.ok) {
//             throw new Error('Failed to fetch fleet utilization');
//         }
//         return await response.json();
//     } catch (error) {
//         console.error('Error fetching fleet utilization:', error);
//         throw error;
//     }
// }