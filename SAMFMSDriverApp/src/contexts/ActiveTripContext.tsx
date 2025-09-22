import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useNavigation } from '@react-navigation/native';
import { AppState } from 'react-native';
import { getDriverActiveTrips, getUserData, API_URL, getToken } from '../utils/api';

interface ActiveTrip {
  id: string;
  name: string;
  status: string;
  origin: any;
  destination: any;
  scheduled_start_time: string;
  actual_start_time?: string;
  vehicle_id: string;
  [key: string]: any;
}

interface ActiveTripContextType {
  hasActiveTrip: boolean;
  activeTrip: ActiveTrip | null;
  isCheckingActiveTrip: boolean;
  checkForActiveTrip: () => Promise<void>;
  clearActiveTrip: () => void;
  error: string | null;
}

const ActiveTripContext = createContext<ActiveTripContextType | undefined>(undefined);

export const useActiveTripContext = () => {
  const context = useContext(ActiveTripContext);
  if (!context) {
    throw new Error('useActiveTripContext must be used within an ActiveTripProvider');
  }
  return context;
};

interface ActiveTripProviderProps {
  children: React.ReactNode;
}

export const ActiveTripProvider: React.FC<ActiveTripProviderProps> = ({ children }) => {
  const [hasActiveTrip, setHasActiveTrip] = useState(false);
  const [activeTrip, setActiveTrip] = useState<ActiveTrip | null>(null);
  const [isCheckingActiveTrip, setIsCheckingActiveTrip] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastCheckTime, setLastCheckTime] = useState<number>(0);

  const navigation = useNavigation();

  // Get employee ID for a driver
  const getEmployeeID = useCallback(async (securityId: string): Promise<string | null> => {
    try {
      const token = await getToken();
      if (!token) return null;

      const response = await fetch(`${API_URL}/management/drivers/employee/${securityId}`, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Employee ID API response (ActiveTripContext):', data);

        // Handle nested structure: {"status":"success","data":{"data":"EMP139"}}
        let empId = null;
        if (data.status === 'success') {
          if (data.data && typeof data.data === 'object' && data.data.data) {
            empId = data.data.data;
          } else if (data.data && typeof data.data === 'string') {
            empId = data.data;
          }
        }

        return empId;
      }
    } catch (fetchError) {
      console.error('Error fetching employee ID:', fetchError);
    }
    return null;
  }, []);

  // Check for active trips
  const checkForActiveTrip = useCallback(async () => {
    // Prevent too frequent checks (minimum 60 seconds between checks) - increased from 30s
    const now = Date.now();
    if (now - lastCheckTime < 60000) {
      return;
    }

    try {
      setIsCheckingActiveTrip(true);
      setError(null);
      setLastCheckTime(now);

      const userData = await getUserData();
      if (!userData?.id) {
        console.log('No user data found for active trip check');
        setHasActiveTrip(false);
        setActiveTrip(null);
        return;
      }

      const employeeId = await getEmployeeID(userData.id);
      if (!employeeId) {
        console.log('No employee ID found for active trip check');
        setHasActiveTrip(false);
        setActiveTrip(null);
        return;
      }

      console.log('Checking for active trips for employee:', employeeId);
      const tripsResponse = await getDriverActiveTrips(employeeId);

      // Handle different response structures
      let trips = [];
      if (Array.isArray(tripsResponse)) {
        trips = tripsResponse;
      } else if (tripsResponse?.data?.data && Array.isArray(tripsResponse.data.data)) {
        // Handle nested structure: {status: 'success', data: {data: [trips]}}
        trips = tripsResponse.data.data;
      } else if (tripsResponse?.data && Array.isArray(tripsResponse.data)) {
        trips = tripsResponse.data;
      } else if (tripsResponse?.trips && Array.isArray(tripsResponse.trips)) {
        trips = tripsResponse.trips;
      }

      console.log('Found active trips:', trips);

      // Any trip that exists is considered "active" for navigation purposes
      if (trips.length > 0) {
        const trip = trips[0]; // Take the first active trip
        console.log('Active trip found:', trip);

        setHasActiveTrip(true);
        setActiveTrip({
          id: trip.id || trip._id,
          name: trip.name || trip.trip_name || `Trip ${trip.id}`,
          status: trip.status,
          origin: trip.origin,
          destination: trip.destination,
          scheduled_start_time: trip.scheduled_start_time,
          actual_start_time: trip.actual_start_time,
          vehicle_id: trip.vehicle_id || trip.vehicleId,
          ...trip, // Include all other trip data
        });

        // Always auto-navigate to active trip screen if there's an active trip and not already there
        const currentRoute = navigation
          .getState()
          ?.routes?.find(route => route.state?.index !== undefined)?.state?.routes[
          navigation.getState()?.routes?.find(route => route.state?.index !== undefined)?.state
            ?.index || 0
        ]?.name;

        if (currentRoute !== 'ActiveTrip') {
          console.log('Navigating to active trip screen from:', currentRoute);
          // Use a timeout to ensure navigation state is stable
          setTimeout(() => {
            try {
              (navigation as any).navigate('Dashboard', {
                screen: 'ActiveTrip',
              });
            } catch (navError) {
              console.error('Navigation error:', navError);
            }
          }, 100);
        }
      } else {
        console.log('No active trips found');
        setHasActiveTrip(false);
        setActiveTrip(null);
      }
    } catch (checkError) {
      console.error('Error checking for active trips:', checkError);
      setError(
        checkError instanceof Error ? checkError.message : 'Failed to check for active trips'
      );
      // Don't clear active trip state on error to avoid disrupting ongoing trips
    } finally {
      setIsCheckingActiveTrip(false);
    }
  }, [navigation, getEmployeeID, lastCheckTime]);

  // Clear active trip (called when trip is completed)
  const clearActiveTrip = useCallback(() => {
    console.log('Clearing active trip');
    setHasActiveTrip(false);
    setActiveTrip(null);
    setError(null);
  }, []);

  // Check for active trips when app becomes active
  useEffect(() => {
    const handleAppStateChange = (nextAppState: string) => {
      if (nextAppState === 'active') {
        console.log('App became active, checking for active trips');
        checkForActiveTrip();
      }
    };

    const subscription = AppState.addEventListener('change', handleAppStateChange);
    return () => subscription?.remove();
  }, [checkForActiveTrip]);

  // Initial check when context is created
  useEffect(() => {
    checkForActiveTrip();
  }, [checkForActiveTrip]);

  // Periodic check every 5 minutes when app is active (reduced from 2 minutes)
  useEffect(() => {
    const interval = setInterval(() => {
      if (AppState.currentState === 'active') {
        checkForActiveTrip();
      }
    }, 300000); // 5 minutes

    return () => clearInterval(interval);
  }, [checkForActiveTrip]);

  const contextValue: ActiveTripContextType = {
    hasActiveTrip,
    activeTrip,
    isCheckingActiveTrip,
    checkForActiveTrip,
    clearActiveTrip,
    error,
  };

  return <ActiveTripContext.Provider value={contextValue}>{children}</ActiveTripContext.Provider>;
};
