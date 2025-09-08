import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Configure your API base URL here
const API_BASE_URL = 'http://localhost:8000'; // Update with your SAMFMS API URL

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  async (config) => {
    const token = await AsyncStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      await AsyncStorage.removeItem('authToken');
      // Navigate to login screen
    }
    return Promise.reject(error);
  }
);

export const apiService = {
  // Authentication
  login: async (username: string, password: string) => {
    const response = await api.post('/auth/login', {
      username,
      password,
    });
    return response.data;
  },

  getCurrentUser: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },

  // Trips
  getActiveTrips: async () => {
    const response = await api.get('/trips/active');
    return response.data;
  },

  getTripHistory: async () => {
    const response = await api.get('/trips/history');
    return response.data;
  },

  startTrip: async (tripId: string) => {
    const response = await api.post(`/trips/${tripId}/start`);
    return response.data;
  },

  endTrip: async (tripId: string, endLocation: any) => {
    const response = await api.post(`/trips/${tripId}/end`, {
      endLocation,
    });
    return response.data;
  },

  updateTripLocation: async (tripId: string, location: any) => {
    const response = await api.post(`/trips/${tripId}/location`, {
      location,
    });
    return response.data;
  },

  // Vehicle Management
  getVehicleInfo: async (vehicleId: string) => {
    const response = await api.get(`/vehicles/${vehicleId}`);
    return response.data;
  },

  submitVehicleInspection: async (vehicleId: string, inspectionData: any) => {
    const response = await api.post(`/vehicles/${vehicleId}/inspection`, inspectionData);
    return response.data;
  },

  reportMaintenanceIssue: async (vehicleId: string, issueData: any) => {
    const response = await api.post(`/vehicles/${vehicleId}/maintenance-issue`, issueData);
    return response.data;
  },

  // Notifications
  getNotifications: async () => {
    const response = await api.get('/notifications');
    return response.data;
  },

  markNotificationRead: async (notificationId: string) => {
    const response = await api.put(`/notifications/${notificationId}/read`);
    return response.data;
  },

  // Location tracking
  updateDriverLocation: async (location: any) => {
    const response = await api.post('/location/update', {
      location,
    });
    return response.data;
  },
};
