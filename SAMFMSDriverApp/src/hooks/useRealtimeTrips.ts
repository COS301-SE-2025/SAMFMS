import { useState, useEffect, useCallback, useRef } from 'react';
import {
  getUpcomingTrips,
  getRecentTrips,
  createRealtimeUpdater,
  API_URL,
  getToken,
} from '../utils/api';
import { AppState } from 'react-native';

interface UseRealtimeTripsProps {
  driverId: string | null;
  enabled?: boolean;
  updateInterval?: number; // in milliseconds, default 30 seconds
}

interface UseRealtimeTripsReturn {
  upcomingTrips: any[];
  recentTrips: any[];
  loading: boolean;
  error: string | null;
  lastUpdated: Date | null;
  refreshData: () => Promise<void>;
  isRealTimeActive: boolean;
}

export const useRealtimeTrips = ({
  driverId,
  enabled = true,
  updateInterval = 30000, // 30 seconds default
}: UseRealtimeTripsProps): UseRealtimeTripsReturn => {
  const [upcomingTrips, setUpcomingTrips] = useState<any[]>([]);
  const [recentTrips, setRecentTrips] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [isRealTimeActive, setIsRealTimeActive] = useState(false);

  const realtimeUpdaterRef = useRef<any>(null);
  const employeeIdRef = useRef<string | null>(null);

  // Get employee ID
  const getEmployeeID = useCallback(async (securityId: string): Promise<string | null> => {
    if (employeeIdRef.current) {
      return employeeIdRef.current;
    }

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
        console.log('Employee ID API response (hook):', data);

        // Handle nested structure: {"status":"success","data":{"data":"EMP139"}}
        let empId = null;
        if (data.status === 'success') {
          if (data.data && typeof data.data === 'object' && data.data.data) {
            empId = data.data.data;
          } else if (data.data && typeof data.data === 'string') {
            empId = data.data;
          }
        }

        if (empId) {
          employeeIdRef.current = empId;
          return empId;
        }
      }
    } catch (fetchError) {
      console.error('Error fetching employee ID:', fetchError);
    }
    return null;
  }, []);

  // Fetch both upcoming and recent trips
  const fetchTripsData = useCallback(async (): Promise<void> => {
    if (!driverId) return;

    try {
      setLoading(true);
      setError(null);

      const employeeId = await getEmployeeID(driverId);
      if (!employeeId) {
        throw new Error('Unable to get employee ID');
      }

      console.log('Fetching trips data for employee ID:', employeeId);

      // Fetch both upcoming and recent trips in parallel
      const [upcomingResponse, recentResponse] = await Promise.allSettled([
        getUpcomingTrips(employeeId),
        getRecentTrips(employeeId),
      ]);

      // Process upcoming trips
      if (upcomingResponse.status === 'fulfilled') {
        const upcomingData = upcomingResponse.value;
        let upcomingTripsData = [];

        if (Array.isArray(upcomingData?.data?.data)) {
          upcomingTripsData = upcomingData.data.data;
        } else if (Array.isArray(upcomingData?.data?.trips)) {
          upcomingTripsData = upcomingData.data.trips;
        } else if (Array.isArray(upcomingData?.data)) {
          upcomingTripsData = upcomingData.data;
        } else if (Array.isArray(upcomingData?.trips)) {
          upcomingTripsData = upcomingData.trips;
        }

        console.log('Upcoming trips data:', upcomingTripsData);
        setUpcomingTrips(upcomingTripsData);
      } else {
        console.error('Failed to fetch upcoming trips:', upcomingResponse.reason);
      }

      // Process recent trips
      if (recentResponse.status === 'fulfilled') {
        const recentData = recentResponse.value;
        let recentTripsData = [];

        if (Array.isArray(recentData?.data?.data)) {
          recentTripsData = recentData.data.data;
        } else if (Array.isArray(recentData?.data?.trips)) {
          recentTripsData = recentData.data.trips;
        } else if (Array.isArray(recentData?.data)) {
          recentTripsData = recentData.data;
        } else if (Array.isArray(recentData?.trips)) {
          recentTripsData = recentData.trips;
        }

        console.log('Recent trips data:', recentTripsData);
        setRecentTrips(recentTripsData.slice(0, 5)); // Limit to last 5 trips
      } else {
        console.error('Failed to fetch recent trips:', recentResponse.reason);
      }

      setLastUpdated(new Date());
    } catch (fetchError) {
      console.error('Error fetching trips data:', fetchError);
      setError(fetchError instanceof Error ? fetchError.message : 'Failed to fetch trips data');
    } finally {
      setLoading(false);
    }
  }, [driverId, getEmployeeID]);

  // Manual refresh function
  const refreshData = useCallback(async () => {
    await fetchTripsData();
  }, [fetchTripsData]);

  // Start real-time updates
  const startRealTimeUpdates = useCallback(() => {
    if (!enabled || !driverId || realtimeUpdaterRef.current?.isRunning()) {
      return;
    }

    console.log('Starting real-time trip updates...');
    realtimeUpdaterRef.current = createRealtimeUpdater(fetchTripsData, updateInterval);
    realtimeUpdaterRef.current.start();
    setIsRealTimeActive(true);
  }, [enabled, driverId, fetchTripsData, updateInterval]);

  // Stop real-time updates
  const stopRealTimeUpdates = useCallback(() => {
    if (realtimeUpdaterRef.current?.isRunning()) {
      console.log('Stopping real-time trip updates...');
      realtimeUpdaterRef.current.stop();
      setIsRealTimeActive(false);
    }
  }, []);

  // Handle app state changes (pause updates when app is in background)
  useEffect(() => {
    const handleAppStateChange = (nextAppState: string) => {
      if (nextAppState === 'active') {
        // App became active, start real-time updates and refresh data
        startRealTimeUpdates();
        fetchTripsData();
      } else if (nextAppState === 'background' || nextAppState === 'inactive') {
        // App went to background, stop real-time updates to save battery
        stopRealTimeUpdates();
      }
    };

    const subscription = AppState.addEventListener('change', handleAppStateChange);
    return () => subscription?.remove();
  }, [startRealTimeUpdates, stopRealTimeUpdates, fetchTripsData]);

  // Initial data fetch and real-time setup
  useEffect(() => {
    if (driverId && enabled) {
      fetchTripsData().then(() => {
        startRealTimeUpdates();
      });
    }

    return () => {
      stopRealTimeUpdates();
    };
  }, [driverId, enabled, fetchTripsData, startRealTimeUpdates, stopRealTimeUpdates]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopRealTimeUpdates();
    };
  }, [stopRealTimeUpdates]);

  return {
    upcomingTrips,
    recentTrips,
    loading,
    error,
    lastUpdated,
    refreshData,
    isRealTimeActive,
  };
};
