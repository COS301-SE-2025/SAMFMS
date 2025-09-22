import { useState, useCallback, useRef, useEffect } from 'react';
import Geolocation from '@react-native-community/geolocation';
import { pingDriverLocation } from '../utils/api';

interface LocationData {
  latitude: number;
  longitude: number;
  accuracy: number;
  speed?: number;
  heading?: number;
  timestamp: number;
}

interface LocationTrackingHookReturn {
  currentLocation: LocationData | null;
  currentSpeed: number;
  startLocationPing: (tripId: string, isPaused: boolean, vehicleLocation?: any) => void;
  stopLocationPing: () => void;
  updateVehicleLocation: (vehicleLocation: any) => void;
}

export const useLocationTracking = (): LocationTrackingHookReturn => {
  const [currentLocation, setCurrentLocation] = useState<LocationData | null>(null);
  const [currentSpeed, setCurrentSpeed] = useState<number>(0);

  const locationInterval = useRef<ReturnType<typeof setInterval> | null>(null);
  const watchId = useRef<number | null>(null);
  const isTracking = useRef<boolean>(false);
  const currentTripId = useRef<string | null>(null);
  const isPausedRef = useRef<boolean>(false);
  const vehicleLocationRef = useRef<any>(null);

  // Start watching location changes
  const startLocationWatch = useCallback(() => {
    if (watchId.current !== null) {
      return; // Already watching
    }

    console.log('🎯 Starting location tracking');

    // Configure geolocation settings
    const locationOptions = {
      enableHighAccuracy: true,
      timeout: 10000,
      maximumAge: 5000,
      distanceFilter: 5, // Update when moved at least 5 meters
      interval: 5000, // Update every 5 seconds
      fastestInterval: 2000, // But no faster than every 2 seconds
    };

    watchId.current = Geolocation.watchPosition(
      position => {
        const locationData: LocationData = {
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          accuracy: position.coords.accuracy,
          speed: position.coords.speed || 0,
          heading: position.coords.heading || 0,
          timestamp: position.timestamp,
        };

        setCurrentLocation(locationData);

        // Convert speed from m/s to km/h
        const speedKmh = (position.coords.speed || 0) * 3.6;
        setCurrentSpeed(speedKmh);

        // Reduced frequent location update logging
        // console.log('📍 Location updated:', {
        //   lat: locationData.latitude.toFixed(6),
        //   lng: locationData.longitude.toFixed(6),
        //   speed: speedKmh.toFixed(1) + ' km/h',
        //   accuracy: locationData.accuracy.toFixed(1) + 'm',
        // });
      },
      error => {
        console.error('Location watch error:', error);
        // Don't stop tracking on single errors, just log them
      },
      locationOptions
    );
  }, []);

  // Stop watching location changes
  const stopLocationWatch = useCallback(() => {
    if (watchId.current !== null) {
      console.log('🛑 Stopping location tracking');
      Geolocation.clearWatch(watchId.current);
      watchId.current = null;
    }
  }, []);

  // Send location ping to API
  const sendLocationPing = useCallback(async () => {
    if (!currentTripId.current || isPausedRef.current) {
      console.log('🔇 Skipping ping: No trip ID or paused', {
        tripId: currentTripId.current,
        paused: isPausedRef.current,
      });
      return;
    }

    // Use priority: 1) vehicleLocation from API, 2) currentLocation from GPS
    let pingLocation = null;
    let pingSpeed = currentSpeed;

    if (vehicleLocationRef.current?.position) {
      pingLocation = {
        latitude: vehicleLocationRef.current.position[0],
        longitude: vehicleLocationRef.current.position[1],
      };
      // Use live speed from vehicle data if available
      if (vehicleLocationRef.current.speed !== undefined) {
        pingSpeed = vehicleLocationRef.current.speed;
      }
    } else if (currentLocation) {
      pingLocation = {
        latitude: currentLocation.latitude,
        longitude: currentLocation.longitude,
      };
    }

    if (!pingLocation) {
      console.log('⚠️ No location available for ping yet - will retry on next interval');
      return;
    }

    try {
      await pingDriverLocation(
        currentTripId.current,
        pingLocation.longitude,
        pingLocation.latitude,
        pingSpeed
      );

      // Reduced frequent ping success logging
      // console.log('📡 Location ping sent successfully:', {
      //   tripId: currentTripId.current,
      //   lat: pingLocation.latitude.toFixed(6),
      //   lng: pingLocation.longitude.toFixed(6),
      //   speed: pingSpeed.toFixed(1) + ' km/h',
      // });
    } catch (error) {
      console.error('Failed to send location ping:', error);
      // Continue pinging even on API errors - API has fallback handling
    }
  }, [currentLocation, currentSpeed]);

  // Start location pinging for a trip
  const startLocationPing = useCallback(
    (tripId: string, isPaused: boolean, vehicleLocation?: any) => {
      console.log('🚀 Starting location ping for trip:', tripId, 'Paused:', isPaused);

      // Always update these values
      currentTripId.current = tripId;
      isPausedRef.current = isPaused;
      vehicleLocationRef.current = vehicleLocation;

      // Only start if not already tracking this trip
      if (!isTracking.current || currentTripId.current !== tripId) {
        isTracking.current = true;

        // Start location tracking
        startLocationWatch();

        // Clear any existing interval to prevent duplicates
        if (locationInterval.current) {
          clearInterval(locationInterval.current);
        }

        // Start periodic pinging (every 10 seconds)
        locationInterval.current = setInterval(() => {
          if (isTracking.current && currentTripId.current && !isPausedRef.current) {
            sendLocationPing();
          }
        }, 10000); // Ping every 10 seconds

        // Send an initial ping after a short delay to allow location to be acquired
        setTimeout(() => {
          if (isTracking.current && currentTripId.current && !isPausedRef.current) {
            sendLocationPing();
          }
        }, 3000);
      } else {
        console.log('📍 Location ping already active for trip:', tripId);
      }
    },
    [startLocationWatch, sendLocationPing]
  );

  // Stop location pinging
  const stopLocationPing = useCallback(() => {
    console.log('🛑 Stopping location ping - Current state:', {
      isTracking: isTracking.current,
      tripId: currentTripId.current,
      paused: isPausedRef.current,
    });

    isTracking.current = false;
    currentTripId.current = null;
    isPausedRef.current = false;

    // Stop location tracking
    stopLocationWatch();

    // Clear ping interval
    if (locationInterval.current) {
      clearInterval(locationInterval.current);
      locationInterval.current = null;
      console.log('✅ Location ping interval cleared');
    }
  }, [stopLocationWatch]);

  // Update pause state when needed
  useEffect(() => {
    // This effect can be used to handle pause state updates if needed
  }, []);

  // Update vehicle location reference for pinging
  const updateVehicleLocation = useCallback((vehicleLocation: any) => {
    vehicleLocationRef.current = vehicleLocation;
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopLocationPing();
    };
  }, [stopLocationPing]);

  return {
    currentLocation,
    currentSpeed,
    startLocationPing,
    stopLocationPing,
    updateVehicleLocation,
  };
};
