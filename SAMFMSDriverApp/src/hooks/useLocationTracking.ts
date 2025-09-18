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
  startLocationPing: (tripId: string, isPaused: boolean) => void;
  stopLocationPing: () => void;
}

export const useLocationTracking = (): LocationTrackingHookReturn => {
  const [currentLocation, setCurrentLocation] = useState<LocationData | null>(null);
  const [currentSpeed, setCurrentSpeed] = useState<number>(0);

  const locationInterval = useRef<ReturnType<typeof setInterval> | null>(null);
  const watchId = useRef<number | null>(null);
  const isTracking = useRef<boolean>(false);
  const currentTripId = useRef<string | null>(null);
  const isPausedRef = useRef<boolean>(false);

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

        console.log('📍 Location updated:', {
          lat: locationData.latitude.toFixed(6),
          lng: locationData.longitude.toFixed(6),
          speed: speedKmh.toFixed(1) + ' km/h',
          accuracy: locationData.accuracy.toFixed(1) + 'm',
        });
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
    if (!currentTripId.current || isPausedRef.current || !currentLocation) {
      return;
    }

    try {
      await pingDriverLocation(
        currentTripId.current,
        currentLocation.longitude,
        currentLocation.latitude,
        currentSpeed
      );

      console.log('📡 Location ping sent successfully:', {
        tripId: currentTripId.current,
        lat: currentLocation.latitude.toFixed(6),
        lng: currentLocation.longitude.toFixed(6),
        speed: currentSpeed.toFixed(1) + ' km/h',
      });
    } catch (error) {
      console.error('Failed to send location ping:', error);
      // Don't stop pinging on API errors, the API has fallback handling
    }
  }, [currentLocation, currentSpeed]);

  // Start location pinging for a trip
  const startLocationPing = useCallback(
    (tripId: string, isPaused: boolean) => {
      console.log('🚀 Starting location ping for trip:', tripId, 'Paused:', isPaused);

      currentTripId.current = tripId;
      isPausedRef.current = isPaused;
      isTracking.current = true;

      // Start location tracking
      startLocationWatch();

      // Start periodic pinging (every 10 seconds)
      if (locationInterval.current) {
        clearInterval(locationInterval.current);
      }

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
    },
    [startLocationWatch, sendLocationPing]
  );

  // Stop location pinging
  const stopLocationPing = useCallback(() => {
    console.log('🛑 Stopping location ping');

    isTracking.current = false;
    currentTripId.current = null;
    isPausedRef.current = false;

    // Stop location tracking
    stopLocationWatch();

    // Clear ping interval
    if (locationInterval.current) {
      clearInterval(locationInterval.current);
      locationInterval.current = null;
    }
  }, [stopLocationWatch]);

  // Update pause state when needed
  useEffect(() => {
    // This effect can be used to handle pause state updates if needed
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
  };
};
