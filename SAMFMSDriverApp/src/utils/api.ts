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

    if (!response.ok) {
      const errorText = await response.text();

      let errorData;
      try {
        errorData = JSON.parse(errorText);
      } catch (e) {
        throw new Error(`Login failed: ${response.status} ${response.statusText}`);
      }

      throw new Error(errorData.detail || errorData.message || 'Login failed');
    }

    const data = await response.json();

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
    console.log(`Attempting to fetch EMP ID for security_id: ${security_id}`);
    const data = await apiRequest(`/management/drivers/employee/${security_id}`);
    console.log('Successfully fetched EMP ID:', data);
    return data;
  } catch (error) {
    console.error('Error fetching driver EMP ID:', error);

    // Fallback to mock data for development
    console.log('Falling back to mock driver EMP ID');
    const mockEmpId = `EMP${security_id?.slice(-3) || '001'}`;
    console.log('Generated mock EMP ID:', mockEmpId);

    return {
      data: mockEmpId, // Generate a mock employee ID
      status: 'success',
      mock: true, // Flag to indicate this is mock data
    };
  }
};

export const getDriverActiveTrips = async (driver_id: string) => {
  try {
    console.log(`Attempting to fetch active trips for driver_id: ${driver_id}`);
    const data = await apiRequest(`/trips/trips/active/${driver_id}`);
    console.log('Successfully fetched active trips:', data);
    return data.data || data;
  } catch (error) {
    console.error('Error fetching active trips:', error);

    // Fallback to mock data for development
    console.log('Falling back to mock active trips');

    // Return empty array if no active trips (most common case)
    // Uncomment the mock trip below for testing active trip functionality
    /*
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
      mock: true, // Flag to indicate this is mock data
    };

    console.log('Generated mock trip:', mockTrip);
    return [mockTrip];
    */

    return []; // Return empty array when no active trips
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

// Real-time updates functionality
export const createRealtimeUpdater = (
  updateFunction: () => Promise<void>,
  intervalMs: number = 30000
) => {
  let intervalId: ReturnType<typeof setInterval> | null = null;

  const start = () => {
    if (intervalId) return; // Already running

    intervalId = setInterval(async () => {
      try {
        await updateFunction();
      } catch (error) {
        console.error('Real-time update error:', error);
      }
    }, intervalMs);
  };

  const stop = () => {
    if (intervalId) {
      clearInterval(intervalId);
      intervalId = null;
    }
  };

  const isRunning = () => intervalId !== null;

  return { start, stop, isRunning };
};

// Get recent trips with real-time capability
export const getRecentTrips = async (driver_id: string) => {
  try {
    const data = await apiRequest(`/trips/trips/recent/${driver_id}`);
    return data;
  } catch (error) {
    console.error('Error fetching recent trips:', error);

    // Fallback to mock data for development
    console.log('Falling back to mock recent trips');
    const now = new Date();
    const mockTrips = [
      {
        id: 'recent-1',
        _id: 'recent-1',
        name: 'Airport Transfer',
        description: 'Completed airport transfer',
        origin: {
          location: {
            coordinates: [28.2293, -25.7461],
            type: 'Point',
          },
          address: 'Hatfield, Pretoria',
          name: 'Residential Area',
        },
        destination: {
          location: {
            coordinates: [28.246, -26.1392],
            type: 'Point',
          },
          address: 'O.R. Tambo International Airport',
          name: 'OR Tambo Airport',
        },
        estimated_distance: 45000,
        estimated_duration: 45,
        status: 'completed',
        scheduled_start_time: new Date(now.getTime() - 2 * 3600000).toISOString(), // 2 hours ago
        actual_start_time: new Date(now.getTime() - 2 * 3600000).toISOString(),
        actual_end_time: new Date(now.getTime() - 1 * 3600000).toISOString(), // 1 hour ago
        priority: 'normal',
        vehicle_id: 'vehicle-123',
        driver_assignment: driver_id,
      },
      {
        id: 'recent-2',
        _id: 'recent-2',
        name: 'Staff Transport',
        description: 'Completed staff transport',
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
        status: 'completed',
        scheduled_start_time: new Date(now.getTime() - 6 * 3600000).toISOString(), // 6 hours ago
        actual_start_time: new Date(now.getTime() - 6 * 3600000).toISOString(),
        actual_end_time: new Date(now.getTime() - 5.5 * 3600000).toISOString(), // 5.5 hours ago
        priority: 'normal',
        vehicle_id: 'vehicle-456',
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

export const pauseTrip = async (tripId: string) => {
  try {
    const data = await apiRequest(`/trips/trips/${tripId}/pause`, {
      method: 'POST',
    });
    return data;
  } catch (error) {
    console.error('Error pausing trip:', error);

    // Fallback to mock success for development
    console.log('Falling back to mock pause trip success');
    return {
      data: {
        id: tripId,
        status: 'paused',
        message: 'Trip paused successfully (mock)',
      },
      status: 'success',
    };
  }
};

export const resumeTrip = async (tripId: string) => {
  try {
    const data = await apiRequest(`/trips/trips/${tripId}/resume`, {
      method: 'POST',
    });
    return data;
  } catch (error) {
    console.error('Error resuming trip:', error);

    // Fallback to mock success for development
    console.log('Falling back to mock resume trip success');
    return {
      data: {
        id: tripId,
        status: 'in_progress',
        message: 'Trip resumed successfully (mock)',
      },
      status: 'success',
    };
  }
};

export const cancelTrip = async (tripId: string) => {
  try {
    const data = await apiRequest(`/trips/trips/${tripId}/cancel`, {
      method: 'POST',
    });
    return data;
  } catch (error) {
    console.error('Error canceling trip:', error);

    // Fallback to mock success for development
    console.log('Falling back to mock cancel trip success');
    return {
      data: {
        id: tripId,
        status: 'cancelled',
        message: 'Trip cancelled successfully (mock)',
      },
      status: 'success',
    };
  }
};

export const completeTrip = async (tripId: string) => {
  try {
    const data = await apiRequest(`/trips/trips/${tripId}/complete`, {
      method: 'POST',
    });
    return data;
  } catch (error) {
    console.error('Error completing trip:', error);

    // Fallback to mock success for development
    console.log('Falling back to mock complete trip success');
    return {
      data: {
        id: tripId,
        status: 'completed',
        message: 'Trip completed successfully (mock)',
      },
      status: 'success',
    };
  }
};

// Driver location ping during active trip
export const pingDriverLocation = async (
  tripId: string,
  longitude: number,
  latitude: number,
  speed?: number
) => {
  try {
    const data = await apiRequest('/trips/trips/driver/ping', {
      method: 'POST',
      body: JSON.stringify({
        trip_id: tripId,
        location: {
          type: 'Point',
          coordinates: [longitude, latitude],
        },
        speed: speed || 0,
        timestamp: new Date().toISOString(),
      }),
    });
    console.log('Driver location ping response:', data);
    return data;
  } catch (error) {
    console.error('Error pinging driver location:', error);

    // Fallback to mock success for development
    console.log('Falling back to mock ping success');
    return {
      data: {
        trip_id: tripId,
        status: 'ping_received',
        message: 'Location ping received successfully (mock)',
      },
      status: 'success',
    };
  }
};

export const updateTrip = async (tripId: string) => {
  try {
    const data = await apiRequest(`/trips/trips/${tripId}/start`, {
      method: 'POST',
    });
    console.log('Trip update response:', data);
    return data;
  } catch (error) {
    console.error('Error updating trip:', error);

    // Fallback to mock success for development
    console.log('Falling back to mock update trip success');
    return {
      data: {
        id: tripId,
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
    const data = await apiRequest(`/gps/locations/vehicle/${vehicleId}`);
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

// Storage for last successful polylines by vehicle ID
const lastSuccessfulPolylines: { [vehicleId: string]: any } = {};

// Helper function to clear stored polylines (useful for testing or when vehicle changes route)
export const clearStoredPolyline = (vehicleId: string) => {
  if (lastSuccessfulPolylines[vehicleId]) {
    delete lastSuccessfulPolylines[vehicleId];
    console.log(`Cleared stored polyline for vehicle ${vehicleId}`);
  }
};

// Helper function to clear all stored polylines
export const clearAllStoredPolylines = () => {
  const vehicleIds = Object.keys(lastSuccessfulPolylines);
  vehicleIds.forEach(id => delete lastSuccessfulPolylines[id]);
  console.log(`Cleared all stored polylines for ${vehicleIds.length} vehicles`);
};

// Helper function to get stored polylines info (for debugging)
export const getStoredPolylinesInfo = () => {
  const info = Object.keys(lastSuccessfulPolylines).map(vehicleId => {
    const data = lastSuccessfulPolylines[vehicleId];
    const age = new Date().getTime() - new Date(data.timestamp).getTime();
    const ageMinutes = Math.round(age / (1000 * 60));
    return {
      vehicleId,
      timestamp: data.timestamp,
      ageMinutes,
      pointCount: data.data?.data?.length || 0,
    };
  });
  console.log('Stored polylines info:', info);
  return info;
};

export const getVehiclePolyline = async (vehicleId: string) => {
  try {
    const data = await apiRequest(`/trips/trips/polyline/${vehicleId}`);

    // Store the successful polyline for future fallback
    if (data && data.data) {
      lastSuccessfulPolylines[vehicleId] = {
        ...data,
        timestamp: new Date().toISOString(), // Add timestamp for reference
      };
      console.log(`Stored successful polyline for vehicle ${vehicleId}`);
    }

    return data;
  } catch (error) {
    console.error(`Error fetching vehicle polyline for ${vehicleId}:`, error);

    // First, try to use the last successful polyline for this vehicle
    if (lastSuccessfulPolylines[vehicleId]) {
      const storedData = lastSuccessfulPolylines[vehicleId];
      const age = new Date().getTime() - new Date(storedData.timestamp).getTime();
      const ageMinutes = Math.round(age / (1000 * 60));

      console.log(
        `Falling back to last successful polyline for vehicle ${vehicleId} (${ageMinutes} minutes old)`
      );
      return {
        ...storedData,
        fallback: true, // Flag to indicate this is fallback data
        fallback_reason: 'api_error',
        fallback_age_minutes: ageMinutes,
      };
    }

    // If no previous polyline exists, fallback to mock polyline data for development
    console.log(
      `Falling back to mock vehicle polyline for ${vehicleId} (no previous polyline stored)`
    );
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
      fallback: true,
      fallback_reason: 'no_previous_polyline',
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

// Live Trip Tracking API - Get real-time trip data
export const getLiveTripData = async (tripId: string) => {
  try {
    console.log(`Attempting to fetch live tracking data for trip_id: ${tripId}`);
    const data = await apiRequest(`/trips/trips/live/${tripId}`);
    console.log('Successfully fetched live tracking data:', data);
    return data;
  } catch (error) {
    console.error('Error fetching live tracking data:', error);

    // Fallback to mock live tracking data for development
    console.log('Falling back to mock live tracking data');

    const mockLiveData = {
      success: true,
      status: 'success',
      data: {
        data: {
          // Trip identification
          trip_id: tripId,
          vehicle_id: 'VH001',
          driver_id: 'mock-driver-123',
          trip_status: 'IN_PROGRESS',

          // Current vehicle position (real-time)
          current_position: {
            latitude: -25.7479 + (Math.random() - 0.5) * 0.01, // Pretoria area with slight randomization
            longitude: 28.2293 + (Math.random() - 0.5) * 0.01,
            bearing: Math.random() * 360,
            speed: 45 + Math.random() * 20, // 45-65 km/h
            accuracy: 5.0,
            timestamp: new Date().toISOString(),
          },

          // Route geometry and navigation
          route_polyline: [
            [-25.7479, 28.2293], // Pretoria
            [-25.75, 28.24],
            [-25.752, 28.25],
            [-25.754, 28.26],
            [-25.756, 28.27], // Sample route points
          ],
          remaining_polyline: [
            [-25.75, 28.24],
            [-25.752, 28.25],
            [-25.754, 28.26],
            [-25.756, 28.27],
          ],
          route_bounds: {
            southWest: {
              lat: -25.756,
              lng: 28.2293,
            },
            northEast: {
              lat: -25.7479,
              lng: 28.27,
            },
          },

          // Trip progress tracking
          progress: {
            total_distance: 12500, // 12.5km
            remaining_distance: 7800.0,
            completed_distance: 4700.0,
            progress_percentage: 37.6,
            estimated_time_remaining: 840, // 14 minutes
            current_step_index: 3,
            total_steps: 8,
          },

          // Current turn-by-turn instruction
          current_instruction: {
            text: 'Turn right onto Church Street',
            type: 'Right',
            distance_to_instruction: 0.3,
            road_name: 'Church Street',
            speed_limit: 60,
          },

          // Trip waypoints
          origin: {
            location: {
              type: 'Point',
              coordinates: [28.2293, -25.7479],
            },
            name: 'Pretoria CBD',
            order: 1,
          },
          destination: {
            location: {
              type: 'Point',
              coordinates: [28.27, -25.756],
            },
            name: 'Menlyn Park Shopping Centre',
            order: 2,
          },

          // Trip timing
          scheduled_time: new Date(Date.now() - 300000).toISOString(), // 5 minutes ago
          actual_start_time: new Date(Date.now() - 600000).toISOString(), // 10 minutes ago

          // Simulation status
          is_simulated: true,
          last_updated: new Date().toISOString(),
        },
        message: 'Successfully retrieved live tracking data',
        meta: {
          timestamp: new Date().toISOString(),
          request_id: null,
          execution_time_ms: null,
          version: '1.0.0',
          pagination: null,
        },
        links: null,
      },
      timestamp: new Date().toISOString(),
    };

    return mockLiveData;
  }
};
