import { useState, useCallback, useEffect } from 'react';

interface SpeedLimitHookReturn {
  speedLimit: number | null;
  startSpeedLimitChecking: (
    activeTrip: any,
    getCurrentLocation: () => Promise<any>,
    isPaused: boolean
  ) => void;
  stopSpeedLimitChecking: () => void;
}

export const useSpeedLimitTracking = (): SpeedLimitHookReturn => {
  const [speedLimit, setSpeedLimit] = useState<number | null>(null);
  const [speedLimitInterval, setSpeedLimitInterval] = useState<ReturnType<
    typeof setInterval
  > | null>(null);

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

  // Get speed limit from route response based on current location
  const getSpeedLimit = useCallback(
    async (activeTrip: any, getCurrentLocation: () => Promise<any>) => {
      try {
        const location = await getCurrentLocation();
        if (!location || !activeTrip?.raw_route_response) return;

        // Extract route steps from raw_route_response
        const routeData = activeTrip.raw_route_response;

        // The correct path is routeData.results[0].legs[0].steps
        const steps = routeData?.results?.[0]?.legs?.[0]?.steps;

        if (!steps || !Array.isArray(steps)) {
          return;
        }

        // Get the main geometry array for coordinate lookup
        const geometry = routeData.results[0].geometry?.[0];

        // Find the closest step to current location
        let closestStep = null;
        let minDistance = Infinity;

        for (const step of steps) {
          if (step.from_index !== undefined && step.to_index !== undefined) {
            // Debug geometry structure
            if (!geometry) {
              continue;
            }

            if (geometry.length <= step.from_index) {
              continue;
            }

            if (geometry && geometry.length > step.from_index) {
              const stepCoord = geometry[step.from_index];

              if (stepCoord) {
                // Handle both array format [lng, lat] and object format {lon, lat}
                let stepLat, stepLng;

                if (Array.isArray(stepCoord) && stepCoord.length >= 2) {
                  stepLat = stepCoord[1]; // latitude
                  stepLng = stepCoord[0]; // longitude
                } else if (
                  stepCoord &&
                  typeof stepCoord === 'object' &&
                  stepCoord.lat !== undefined &&
                  stepCoord.lon !== undefined
                ) {
                  stepLat = stepCoord.lat;
                  stepLng = stepCoord.lon;
                } else {
                  continue;
                }

                // Validate coordinates are valid numbers
                if (
                  typeof stepLat === 'number' &&
                  typeof stepLng === 'number' &&
                  !isNaN(stepLat) &&
                  !isNaN(stepLng) &&
                  typeof location.latitude === 'number' &&
                  typeof location.longitude === 'number' &&
                  !isNaN(location.latitude) &&
                  !isNaN(location.longitude)
                ) {
                  // Calculate distance to step coordinate (geometry is [lng, lat])
                  const distance = calculateDistance(
                    location.latitude,
                    location.longitude,
                    stepLat,
                    stepLng
                  );

                  if (distance < minDistance) {
                    minDistance = distance;
                    closestStep = step;
                  }
                }
              }
            }
          }
        }

        // Update speed limit from closest step
        if (closestStep?.speed_limit && typeof closestStep.speed_limit === 'number') {
          setSpeedLimit(closestStep.speed_limit);
        } else {
          // If closest step has no speed limit, look for nearby steps with speed limits
          let nearbySpeedLimit = null;
          const nearbySteps = steps.filter((step: any) => {
            if (!step.speed_limit || typeof step.speed_limit !== 'number') return false;

            // Use the main geometry variable from outer scope
            if (geometry && geometry.length > step.from_index && step.from_index !== undefined) {
              const stepCoord = geometry[step.from_index];
              if (stepCoord && stepCoord.length >= 2) {
                const stepLat = stepCoord[1];
                const stepLng = stepCoord[0];

                if (
                  typeof stepLat === 'number' &&
                  typeof stepLng === 'number' &&
                  !isNaN(stepLat) &&
                  !isNaN(stepLng)
                ) {
                  const distance = calculateDistance(
                    location.latitude,
                    location.longitude,
                    stepLat,
                    stepLng
                  );

                  // Consider steps within 1km
                  return distance <= 1000;
                }
              }
            }
            return false;
          });

          if (nearbySteps.length > 0) {
            // Sort by distance and use the closest one with speed limit
            nearbySteps.sort((a: any, b: any) => {
              const getStepDistance = (step: any) => {
                if (
                  geometry &&
                  step.from_index !== undefined &&
                  geometry.length > step.from_index
                ) {
                  const stepCoord = geometry[step.from_index];
                  if (stepCoord && stepCoord.length >= 2) {
                    return calculateDistance(
                      location.latitude,
                      location.longitude,
                      stepCoord[1],
                      stepCoord[0]
                    );
                  }
                }
                return Infinity;
              };

              return getStepDistance(a) - getStepDistance(b);
            });

            nearbySpeedLimit = nearbySteps[0].speed_limit;
            setSpeedLimit(nearbySpeedLimit);
          } else {
            // Check if any steps have speed limits (general fallback)
            const stepsWithSpeedLimit = steps.filter(
              (step: any) => step.speed_limit && typeof step.speed_limit === 'number'
            );
            if (stepsWithSpeedLimit.length > 0) {
              // Use the first available speed limit as fallback
              setSpeedLimit(stepsWithSpeedLimit[0].speed_limit);
            } else {
              // Set a default speed limit based on road type or area
              const hasHighwaySteps = steps.some(
                (step: any) =>
                  step.road_class === 'motorway' ||
                  step.road_class === 'trunk' ||
                  (step.name && step.name.toLowerCase().includes('highway'))
              );
              const defaultSpeedLimit = hasHighwaySteps ? 120 : 60; // 120 km/h for highways, 60 km/h for other roads
              setSpeedLimit(defaultSpeedLimit);
            }
          }
        }
      } catch (speedLimitError) {
        // Silently handle speed limit errors
      }
    },
    [calculateDistance]
  );

  // Start speed limit checking every 90 seconds
  const startSpeedLimitChecking = useCallback(
    (activeTrip: any, getCurrentLocation: () => Promise<any>, isPaused: boolean) => {
      if (!activeTrip?.id || isPaused || speedLimitInterval) return;

      // Get initial speed limit
      getSpeedLimit(activeTrip, getCurrentLocation);

      // Set up interval for every 90 seconds
      const interval = setInterval(() => {
        getSpeedLimit(activeTrip, getCurrentLocation);
      }, 90000); // 90 seconds

      setSpeedLimitInterval(interval);
    },
    [speedLimitInterval, getSpeedLimit]
  );

  // Stop speed limit checking
  const stopSpeedLimitChecking = useCallback(() => {
    if (speedLimitInterval) {
      clearInterval(speedLimitInterval);
      setSpeedLimitInterval(null);
    }
  }, [speedLimitInterval]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopSpeedLimitChecking();
    };
  }, [stopSpeedLimitChecking]);

  return {
    speedLimit,
    startSpeedLimitChecking,
    stopSpeedLimitChecking,
  };
};
