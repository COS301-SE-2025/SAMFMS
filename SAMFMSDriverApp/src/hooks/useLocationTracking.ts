import { useState, useCallback, useEffect } from 'react';
import Geolocation from '@react-native-community/geolocation';
import { pingDriverLocation } from '../utils/api';

interface LocationState {
  latitude: number;
  longitude: number;
}

interface LocationHookReturn {
  currentLocation: LocationState | null;
  currentSpeed: number;
  getCurrentLocation: () => Promise<LocationState | null>;
  startLocationPing: (tripId: string, isPaused: boolean) => void;
  stopLocationPing: () => void;
}

export const useLocationTracking = (): LocationHookReturn => {
  const [currentLocation, setCurrentLocation] = useState<LocationState | null>(null);
  const [previousLocation, setPreviousLocation] = useState<{
    latitude: number;
    longitude: number;
    timestamp: number;
  } | null>(null);
  const [currentSpeed, setCurrentSpeed] = useState<number>(0);
  const [pingInterval, setPingInterval] = useState<ReturnType<typeof setInterval> | null>(null);

  // Calculate distance between two coordinates in meters using Haversine formula
  const calculateDistance = useCallback(
    (lat1: number, lon1: number, lat2: number, lon2: number): number => {
      const R = 6371e3; // Earth's radius in meters
      const φ1 = (lat1 * Math.PI) / 180; // φ, λ in radians
      const φ2 = (lat2 * Math.PI) / 180;
      const Δφ = ((lat2 - lat1) * Math.PI) / 180;
      const Δλ = ((lon2 - lon1) * Math.PI) / 180;

      const a =
        Math.sin(Δφ / 2) * Math.sin(Δφ / 2) +
        Math.cos(φ1) * Math.cos(φ2) * Math.sin(Δλ / 2) * Math.sin(Δλ / 2);
      const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

      return R * c; // Distance in meters
    },
    []
  );

  // Get current location for pinging with retry mechanism
  const getCurrentLocation = useCallback((): Promise<LocationState | null> => {
    return new Promise(resolve => {
      // First try with high accuracy but short timeout
      Geolocation.getCurrentPosition(
        position => {
          const location = {
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
          };
          setCurrentLocation(location);
          resolve(location);
        },
        _highAccuracyError => {
          // Fallback to low accuracy with longer timeout
          Geolocation.getCurrentPosition(
            position => {
              const location = {
                latitude: position.coords.latitude,
                longitude: position.coords.longitude,
              };
              setCurrentLocation(location);
              resolve(location);
            },
            _lowAccuracyError => {
              // Final fallback - use last known location if available
              if (currentLocation) {
                resolve(currentLocation);
              } else {
                // Use a default/mock location as last resort
                const mockLocation = {
                  latitude: -25.7479, // Pretoria coordinates as fallback
                  longitude: 28.2293,
                };
                setCurrentLocation(mockLocation); // Set mock location to state
                resolve(mockLocation);
              }
            },
            {
              enableHighAccuracy: false,
              timeout: 10000,
              maximumAge: 30000,
            }
          );
        },
        {
          enableHighAccuracy: true,
          timeout: 5000,
          maximumAge: 5000,
        }
      );
    });
  }, [currentLocation]);

  // Start location pinging for active trip
  const startLocationPing = useCallback(
    (tripId: string, isPaused: boolean) => {
      if (!tripId || isPaused || pingInterval) return;

      const interval = setInterval(async () => {
        try {
          const location = await getCurrentLocation();
          if (location && tripId) {
            const currentTime = Date.now();

            // Check if this is the first location (no previous location)
            if (!previousLocation) {
              // Set initial location without calculating speed
              setPreviousLocation({
                latitude: location.latitude,
                longitude: location.longitude,
                timestamp: currentTime,
              });
            } else {
              // Calculate speed using previous location
              const distance = calculateDistance(
                previousLocation.latitude,
                previousLocation.longitude,
                location.latitude,
                location.longitude
              );

              // Calculate time difference in seconds
              const timeDiff = (currentTime - previousLocation.timestamp) / 1000;

              if (timeDiff > 0) {
                // Speed in m/s
                const speedMS = distance / timeDiff;
                // Convert to km/h
                const speedKMH = speedMS * 3.6;
                // Update speed state
                setCurrentSpeed(speedKMH);
              }

              // Update previous location for next calculation
              setPreviousLocation({
                latitude: location.latitude,
                longitude: location.longitude,
                timestamp: currentTime,
              });
            }

            // Use the calculated speed
            await pingDriverLocation(tripId, location.longitude, location.latitude, currentSpeed);
          }
        } catch (pingError) {
          // Silently handle ping errors
        }
      }, 5000); // Ping every 5 seconds

      setPingInterval(interval);
    },
    [pingInterval, getCurrentLocation, previousLocation, currentSpeed, calculateDistance]
  );

  // Stop location pinging
  const stopLocationPing = useCallback(() => {
    if (pingInterval) {
      clearInterval(pingInterval);
      setPingInterval(null);
    }
  }, [pingInterval]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopLocationPing();
    };
  }, [stopLocationPing]);

  return {
    currentLocation,
    currentSpeed,
    getCurrentLocation,
    startLocationPing,
    stopLocationPing,
  };
};
