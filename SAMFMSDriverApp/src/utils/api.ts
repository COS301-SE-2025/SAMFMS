import AsyncStorage from '@react-native-async-storage/async-storage';

// API Configuration
export const API_URL = 'https://samfms.co.za/api'; // Production SAMFMS API
// For local development: export const API_URL = 'http://10.0.2.2:8000';

// NOTE: This implementation includes mock data fallbacks for development.
// When the API calls fail (404, authentication issues, etc.), the functions
// will return mock data so the app can be tested without a working backend.

// Storage keys
const STORAGE_KEYS = {
  TOKEN: 'auth_token',
  REFRESH_TOKEN: 'refresh_token',
  USER: 'user_data',
  PERMISSIONS: 'permissions',
  PREFERENCES: 'preferences',
};

// HTTP request utility with timeout
const fetchWithTimeout = async (url: string, options: RequestInit = {}, timeout = 8000) => {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    clearTimeout(timeoutId);
    return response;
  } catch (error) {
    clearTimeout(timeoutId);
    throw error;
  }
};

// Token management
export const getToken = async (): Promise<string | null> => {
  try {
    return await AsyncStorage.getItem(STORAGE_KEYS.TOKEN);
  } catch (error) {
    console.error('Error getting token:', error);
    return null;
  }
};

export const setToken = async (token: string): Promise<void> => {
  try {
    await AsyncStorage.setItem(STORAGE_KEYS.TOKEN, token);
  } catch (error) {
    console.error('Error setting token:', error);
  }
};

export const removeToken = async (): Promise<void> => {
  try {
    await AsyncStorage.removeItem(STORAGE_KEYS.TOKEN);
  } catch (error) {
    console.error('Error removing token:', error);
  }
};

// User data management
export const setUserData = async (userData: any): Promise<void> => {
  try {
    await AsyncStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(userData));
  } catch (error) {
    console.error('Error setting user data:', error);
  }
};

export const getUserData = async (): Promise<any | null> => {
  try {
    const userData = await AsyncStorage.getItem(STORAGE_KEYS.USER);
    return userData ? JSON.parse(userData) : null;
  } catch (error) {
    console.error('Error getting user data:', error);
    return null;
  }
};

// Auth check
export const isAuthenticated = async (): Promise<boolean> => {
  const token = await getToken();
  return !!token;
};

// Login function
export const login = async (email: string, password: string) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    throw new Error('Invalid email format');
  }

  try {
    console.log('Attempting login with email:', email);
    console.log('API URL:', `${API_URL}/auth/login`);

    const response = await fetchWithTimeout(
      `${API_URL}/auth/login`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email,
          password,
        }),
      },
      10000
    );

    console.log('Response status:', response.status);
    console.log('Response headers:', response.headers);

    if (!response.ok) {
      const errorText = await response.text();
      console.log('Error response:', errorText);

      let errorData;
      try {
        errorData = JSON.parse(errorText);
      } catch (e) {
        throw new Error(`Login failed: ${response.status} ${response.statusText}`);
      }

      throw new Error(errorData.detail || errorData.message || 'Login failed');
    }

    const data = await response.json();
    console.log('Login response data:', data);

    // Store tokens
    await setToken(data.access_token);

    // Store refresh token if available
    if (data.refresh_token) {
      await AsyncStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, data.refresh_token);
    }

    // Store user data
    const userData = {
      id: data.user_id,
      email: email,
      role: data.role,
    };
    await setUserData(userData);

    // Store permissions and preferences
    if (data.permissions) {
      await AsyncStorage.setItem(STORAGE_KEYS.PERMISSIONS, JSON.stringify(data.permissions));
    }
    if (data.preferences) {
      await AsyncStorage.setItem(STORAGE_KEYS.PREFERENCES, JSON.stringify(data.preferences));
    }

    return data;
  } catch (error) {
    console.error('Login error:', error);
    throw error;
  }
};

// Logout function
export const logout = async (): Promise<void> => {
  try {
    // Clear all stored data
    await AsyncStorage.multiRemove([
      STORAGE_KEYS.TOKEN,
      STORAGE_KEYS.REFRESH_TOKEN,
      STORAGE_KEYS.USER,
      STORAGE_KEYS.PERMISSIONS,
      STORAGE_KEYS.PREFERENCES,
    ]);
    console.log('Logged out successfully');
  } catch (error) {
    console.error('Error during logout:', error);
  }
};

// Check if user has specific role
export const hasRole = async (role: string): Promise<boolean> => {
  try {
    const userData = await getUserData();
    return userData?.role === role;
  } catch (error) {
    console.error('Error checking role:', error);
    return false;
  }
};

// Role constants
export const ROLES = {
  ADMIN: 'admin',
  DRIVER: 'driver',
  MANAGER: 'manager',
};

// API helper function with authentication
const apiRequest = async (endpoint: string, options: RequestInit = {}) => {
  const token = await getToken();

  const defaultHeaders = {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
  };

  const response = await fetchWithTimeout(
    `${API_URL}${endpoint}`,
    {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
    },
    10000
  );

  if (!response.ok) {
    const errorText = await response.text();
    let errorData;
    try {
      errorData = JSON.parse(errorText);
    } catch (e) {
      throw new Error(`Request failed: ${response.status} ${response.statusText}`);
    }
    throw new Error(errorData.detail || errorData.message || 'Request failed');
  }

  return response.json();
};

// Driver API functions
export const getDriverEMPID = async (security_id: string) => {
  try {
    const data = await apiRequest(`/drivers/empid/${security_id}`);
    return data;
  } catch (error) {
    console.error('Error fetching driver EMP ID:', error);

    // Fallback to mock data for development
    console.log('Falling back to mock driver EMP ID');
    return {
      data: `EMP${security_id?.slice(-3) || '001'}`, // Generate a mock employee ID
      status: 'success',
    };
  }
};

export const getDriverActiveTrips = async (driver_id: string) => {
  try {
    const data = await apiRequest(`/trips/driver-active/${driver_id}`);
    return data.data || data;
  } catch (error) {
    console.error('Error fetching active trips:', error);

    // Fallback to mock data for development
    console.log('Falling back to mock active trips');
    const mockTrip = {
      id: 'mock-trip-1',
      _id: 'mock-trip-1',
      name: 'Airport Transfer',
      description: 'Transport passengers to O.R. Tambo Airport',
      origin: {
        id: '1',
        location: {
          coordinates: [28.2293, -25.7461], // Pretoria coordinates
          type: 'Point',
        },
        address: 'University of Pretoria, Hatfield, Pretoria',
        name: 'UP Campus',
        arrival_time: null,
        departure_time: new Date().toISOString(),
        stop_duration: null,
        order: 0,
      },
      destination: {
        id: '2',
        location: {
          coordinates: [28.246, -26.1392], // OR Tambo coordinates
          type: 'Point',
        },
        address: 'O.R. Tambo International Airport',
        name: 'OR Tambo Airport',
        arrival_time: null,
        departure_time: null,
        stop_duration: null,
        order: 1,
      },
      estimated_distance: 45000, // 45km in meters
      estimated_duration: 45, // 45 minutes
      status: 'in-progress',
      scheduled_start_time: new Date().toISOString(),
      actual_start_time: new Date().toISOString(),
      priority: 'normal',
      vehicle_id: 'vehicle-123',
      vehicleId: 'vehicle-123',
      driver_assignment: driver_id,
    };

    return [mockTrip];
  }
};

export const getUpcomingTrips = async (driver_id: string) => {
  try {
    const data = await apiRequest(`/trips/upcoming/${driver_id}`);
    return data;
  } catch (error) {
    console.error('Error fetching upcoming trips:', error);

    // Fallback to mock data for development
    console.log('Falling back to mock upcoming trips');
    const now = new Date();
    const mockTrips = [
      {
        id: 'upcoming-1',
        _id: 'upcoming-1',
        name: 'Morning Commute',
        description: 'Pick up employees from residential areas',
        origin: {
          location: {
            coordinates: [28.2293, -25.7461],
            type: 'Point',
          },
          address: 'Hatfield, Pretoria',
          name: 'Residential Area A',
        },
        destination: {
          location: {
            coordinates: [28.2335, -25.7545],
            type: 'Point',
          },
          address: 'University of Pretoria, Hatfield Campus',
          name: 'UP Campus',
        },
        estimated_distance: 5000,
        estimated_duration: 15,
        status: 'scheduled',
        scheduled_start_time: new Date(now.getTime() + 5 * 60000).toISOString(), // 5 minutes from now
        priority: 'high',
        vehicle_id: 'vehicle-456',
        driver_assignment: driver_id,
      },
      {
        id: 'upcoming-2',
        _id: 'upcoming-2',
        name: 'Lunch Break Transport',
        description: 'Transport staff to shopping center',
        origin: {
          location: {
            coordinates: [28.2335, -25.7545],
            type: 'Point',
          },
          address: 'University of Pretoria, Hatfield Campus',
          name: 'UP Campus',
        },
        destination: {
          location: {
            coordinates: [28.24, -25.76],
            type: 'Point',
          },
          address: 'Brooklyn Mall, Pretoria',
          name: 'Brooklyn Mall',
        },
        estimated_distance: 8000,
        estimated_duration: 20,
        status: 'scheduled',
        scheduled_start_time: new Date(now.getTime() + 2 * 3600000).toISOString(), // 2 hours from now
        priority: 'normal',
        vehicle_id: 'vehicle-789',
        driver_assignment: driver_id,
      },
    ];

    return {
      data: {
        trips: mockTrips,
        count: mockTrips.length,
      },
      status: 'success',
    };
  }
};

export const finishTrip = async (tripId: string, tripData: any) => {
  try {
    const data = await apiRequest(`/trips/finish/${tripId}`, {
      method: 'POST',
      body: JSON.stringify(tripData),
    });
    return data;
  } catch (error) {
    console.error('Error finishing trip:', error);

    // Fallback to mock success for development
    console.log('Falling back to mock finish trip success');
    return {
      data: {
        id: tripId,
        status: 'completed',
        actual_end_time: tripData.actual_end_time,
        message: 'Trip finished successfully (mock)',
      },
      status: 'success',
    };
  }
};

export const updateTrip = async (tripId: string, tripData: any) => {
  try {
    const data = await apiRequest(`/trips/${tripId}`, {
      method: 'PATCH',
      body: JSON.stringify(tripData),
    });
    return data;
  } catch (error) {
    console.error('Error updating trip:', error);

    // Fallback to mock success for development
    console.log('Falling back to mock update trip success');
    return {
      data: {
        id: tripId,
        ...tripData,
        message: 'Trip updated successfully (mock)',
      },
      status: 'success',
    };
  }
};

export const TripFinishedStatus = async (employeeId: string) => {
  try {
    const data = await apiRequest(`/drivers/trip-finished-status/${employeeId}`);
    return data.finished || data.data || false;
  } catch (error) {
    console.error('Error checking trip finished status:', error);

    // Fallback to mock status for development
    console.log('Falling back to mock trip finished status');
    // Simulate that the trip can be finished after some time
    return Math.random() > 0.7; // 30% chance the trip can be finished
  }
};

export const getLocation = async (vehicleId: string) => {
  try {
    const data = await apiRequest(`/vehicles/location/${vehicleId}`);
    return data;
  } catch (error) {
    console.error('Error fetching vehicle location:', error);

    // Fallback to mock location data for development
    console.log('Falling back to mock vehicle location');
    const mockLocation = {
      data: {
        latitude: -25.7461 + (Math.random() - 0.5) * 0.01, // Slight random movement around Pretoria
        longitude: 28.2293 + (Math.random() - 0.5) * 0.01,
        speed: 45 + Math.random() * 20, // 45-65 km/h
        heading: Math.random() * 360,
        timestamp: new Date().toISOString(),
      },
      status: 'success',
    };

    return mockLocation;
  }
};

export const getVehiclePolyline = async (vehicleId: string) => {
  try {
    const data = await apiRequest(`/vehicles/polyline/${vehicleId}`);
    return data;
  } catch (error) {
    console.error('Error fetching vehicle polyline:', error);

    // Fallback to mock polyline data for development
    console.log('Falling back to mock vehicle polyline');
    const mockPolyline = {
      data: {
        data: [
          { latitude: -25.7461, longitude: 28.2293 }, // Start point (Pretoria)
          { latitude: -25.75, longitude: 28.235 },
          { latitude: -25.76, longitude: 28.24 },
          { latitude: -25.78, longitude: 28.25 },
          { latitude: -25.8, longitude: 28.26 },
          { latitude: -25.9, longitude: 28.27 },
          { latitude: -26.0, longitude: 28.28 },
          { latitude: -26.1, longitude: 28.29 },
          { latitude: -26.1392, longitude: 28.246 }, // End point (OR Tambo)
        ],
      },
      status: 'success',
    };

    return mockPolyline;
  }
};

// Helper function to get current user ID
export const getCurrentUserId = async () => {
  try {
    const userData = await getUserData();
    const userId = userData?.id || userData?._id || userData?.userId;

    if (!userId) {
      // Fallback to mock user ID for development
      console.log('No user data found, falling back to mock user ID');
      return 'mock-driver-123';
    }

    return userId;
  } catch (error) {
    console.error('Error getting current user ID:', error);
    // Fallback to mock user ID for development
    return 'mock-driver-123';
  }
};
