import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Alert,
  TouchableOpacity,
  PermissionsAndroid,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { ArrowLeft, Navigation, Square, Pause, Play, X, CheckCircle } from 'lucide-react-native';
import { WebView } from 'react-native-webview';
import Geolocation from '@react-native-community/geolocation';
import {
  finishTrip,
  getLocation,
  getVehiclePolyline,
  pauseTrip,
  resumeTrip,
  cancelTrip,
  completeTrip,
  pingDriverLocation,
} from '../utils/api';
import { useActiveTripContext } from '../contexts/ActiveTripContext';
import { useTheme } from '../contexts/ThemeContext';

interface VehicleLocation {
  id: string;
  position: [number, number];
  speed: number | null;
  heading: number | null;
  lastUpdated: Date;
}

interface ActiveTripScreenProps {
  navigation: {
    goBack: () => void;
    navigate: (screen: string, params?: any) => void;
  };
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  // Enhanced Header Styles
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 6,
    elevation: 4,
  },
  backButton: {
    padding: 4,
  },
  backButtonCircle: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerTitleContainer: {
    alignItems: 'center',
    flex: 1,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  headerDistance: {
    fontSize: 18,
    fontWeight: '700',
    marginTop: 2,
  },
  headerPriority: {
    fontSize: 14,
    fontWeight: '600',
    marginTop: 4,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
    textAlign: 'center',
    minWidth: 60,
  },
  headerRight: {
    width: 40,
  },
  speedContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 8,
  },
  speedValue: {
    fontSize: 16,
    fontWeight: '700',
  },
  speedLabel: {
    fontSize: 10,
    fontWeight: '500',
    marginTop: 2,
  },
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  loadingText: {
    fontSize: 16,
    marginTop: 16,
  },
  errorContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 32,
  },
  errorText: {
    fontSize: 16,
    textAlign: 'center',
    marginTop: 16,
    marginBottom: 24,
  },
  retryButton: {
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  retryButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  // Enhanced Map Styles
  mapContainer: {
    flex: 1,
    minHeight: 400,
    marginTop: 0,
    marginBottom: 0,
    overflow: 'hidden',
    backgroundColor: '#f1f5f9',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.15,
    shadowRadius: 12,
    elevation: 8,
    position: 'relative',
  },
  map: {
    flex: 1,
  },
  endTripContainer: {
    position: 'absolute',
    bottom: 20,
    left: 20,
    right: 20,
    zIndex: 1000,
  },
  endTripButton: {
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  endTripButtonContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  endTripButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  tripControlContainer: {
    position: 'absolute',
    bottom: 20,
    left: 20,
    right: 20,
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 10,
    zIndex: 1000,
  },
  controlButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 4,
  },
  controlButtonContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  controlButtonText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '600',
    marginLeft: 6,
  },
  loadingSpinner: {
    width: 20,
    height: 20,
    borderWidth: 2,
    borderTopColor: 'transparent',
    borderRadius: 10,
  },
  loadingSpinnerWhite: {
    borderColor: 'white',
  },
});

const ActiveTripScreen: React.FC<ActiveTripScreenProps> = ({ navigation }) => {
  // Use the ActiveTripContext instead of local state
  const { activeTrip, isCheckingActiveTrip, error, checkForActiveTrip, clearActiveTrip } =
    useActiveTripContext();

  // WebView ref for sending messages
  const webViewRef = useRef<WebView>(null);

  // Keep local state for screen-specific functionality
  const [endingTrip, setEndingTrip] = useState(false);
  const [canEndTrip, _setCanEndTrip] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [pausingTrip, setPausingTrip] = useState(false);
  const [cancelingTrip, setCancelingTrip] = useState(false);
  const [statusCheckInterval, setStatusCheckInterval] = useState<ReturnType<
    typeof setInterval
  > | null>(null);

  // Determine if back button should be visible (when trip is paused or cancelled)
  const shouldShowBackButton = isPaused || activeTrip?.status === 'cancelled';

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

  const [vehicleLocation, setVehicleLocation] = useState<VehicleLocation | null>(null);
  const [_mapCenter, setMapCenter] = useState<[number, number]>([37.7749, -122.4194]);
  const [isWebViewLoaded, setIsWebViewLoaded] = useState(false);
  const webViewLoadAttempts = useRef(0);

  // Location ping state
  const [pingInterval, setPingInterval] = useState<ReturnType<typeof setInterval> | null>(null);
  const [speedLimitInterval, setSpeedLimitInterval] = useState<ReturnType<
    typeof setInterval
  > | null>(null);
  const [currentLocation, setCurrentLocation] = useState<{
    latitude: number;
    longitude: number;
  } | null>(null);
  const [previousLocation, setPreviousLocation] = useState<{
    latitude: number;
    longitude: number;
    timestamp: number;
  } | null>(null);
  const [_previousVehicleLocation, setPreviousVehicleLocation] = useState<{
    latitude: number;
    longitude: number;
    timestamp: number;
  } | null>(null);
  const [currentSpeed, setCurrentSpeed] = useState<number>(0);
  const [speedLimit, setSpeedLimit] = useState<number | null>(null);

  // Check if driver is within 250m of destination
  const isNearDestination = useMemo(() => {
    if (!currentLocation || !activeTrip?.destination?.location?.coordinates) {
      return false;
    }

    const destCoords = activeTrip.destination.location.coordinates;

    const distance = calculateDistance(
      currentLocation.latitude,
      currentLocation.longitude,
      destCoords[1], // destination latitude (GeoJSON: [lng, lat])
      destCoords[0] // destination longitude (GeoJSON: [lng, lat])
    );

    const isNear = distance <= 10000; // Temporarily 10km for testing

    return isNear;
  }, [currentLocation, activeTrip?.destination?.location?.coordinates, calculateDistance]);

  const { theme } = useTheme();

  // Get current location for pinging with retry mechanism
  const getCurrentLocation = useCallback((): Promise<{
    latitude: number;
    longitude: number;
  } | null> => {
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
  const startLocationPing = useCallback(() => {
    if (!activeTrip?.id || isPaused || pingInterval) return;

    const interval = setInterval(async () => {
      try {
        const location = await getCurrentLocation();
        if (location && activeTrip?.id) {
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
            // Update previous location for next calculation
            setPreviousLocation({
              latitude: location.latitude,
              longitude: location.longitude,
              timestamp: currentTime,
            });
          }

          // Use the same speed that's displayed in the UI (currentSpeed)
          const speedToSend = currentSpeed;

          console.log('Ping request:', {
            tripId: activeTrip.id,
            longitude: location.longitude,
            latitude: location.latitude,
            speed: speedToSend,
          });

          const pingResponse = await pingDriverLocation(
            activeTrip.id,
            location.longitude,
            location.latitude,
            speedToSend
          );

          console.log('Ping response:', pingResponse);
        }
      } catch (pingError) {
        console.error('Failed to ping location:', pingError);
      }
    }, 5000); // Ping every 5 seconds

    setPingInterval(interval);
  }, [
    activeTrip?.id,
    isPaused,
    pingInterval,
    getCurrentLocation,
    setPreviousLocation,
    previousLocation,
    currentSpeed,
  ]);

  // Stop location pinging
  const stopLocationPing = useCallback(() => {
    if (pingInterval) {
      clearInterval(pingInterval);
      setPingInterval(null);
    }
  }, [pingInterval]);

  // Get speed limit using Geoapify Map Matching API
  const getSpeedLimit = useCallback(async () => {
    try {
      const location = await getCurrentLocation();
      if (!location) return;

      // Create two waypoints - current location and a small offset
      // This provides the minimum "shape" required by the API
      const offsetDistance = 0.001; // Small offset in degrees (~100m)
      const waypoints = [
        {
          timestamp: new Date().toISOString(),
          location: [location.longitude, location.latitude],
        },
        {
          timestamp: new Date(Date.now() + 10000).toISOString(), // 10 seconds later
          location: [location.longitude + offsetDistance, location.latitude + offsetDistance],
        },
      ];

      // Make API call to Geoapify
      const response = await fetch(
        'https://api.geoapify.com/v1/mapmatching?apiKey=8c5cae4820744254b3cb03ebd9b9ce13',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            mode: 'drive',
            waypoints: waypoints,
          }),
        }
      );

      if (response.ok) {
        const data = await response.json();

        // Extract speed limit from the first step
        const firstFeature = data.features?.[0];
        const firstLeg = firstFeature?.properties?.legs?.[0];
        const firstStep = firstLeg?.steps?.[0];
        const speedLimitValue = firstStep?.speed_limit;

        if (speedLimitValue && typeof speedLimitValue === 'number') {
          setSpeedLimit(speedLimitValue);
          console.log('Speed limit updated:', speedLimitValue);
        } else {
          console.log('No speed limit data available');
        }
      } else {
        console.error('Speed limit API call failed:', response);
      }
    } catch (speedLimitError) {
      console.error('Error fetching speed limit:', speedLimitError);
    }
  }, [getCurrentLocation]);

  // Start speed limit checking every 90 seconds
  const startSpeedLimitChecking = useCallback(() => {
    if (!activeTrip?.id || isPaused || speedLimitInterval) return;

    // Get initial speed limit
    getSpeedLimit();

    // Set up interval for every 90 seconds
    const interval = setInterval(() => {
      getSpeedLimit();
    }, 90000); // 90 seconds

    setSpeedLimitInterval(interval);
  }, [activeTrip?.id, isPaused, speedLimitInterval, getSpeedLimit]);

  // Stop speed limit checking
  const stopSpeedLimitChecking = useCallback(() => {
    if (speedLimitInterval) {
      clearInterval(speedLimitInterval);
      setSpeedLimitInterval(null);
    }
  }, [speedLimitInterval]);

  const fetchVehicleData = useCallback(async () => {
    if (!activeTrip?.vehicle_id && !activeTrip?.vehicleId) return;

    const vehicleId = activeTrip.vehicle_id || activeTrip.vehicleId;
    if (!vehicleId) return;

    try {
      // Inline vehicle location fetching to avoid dependency issues
      const locationResponse = await getLocation(vehicleId);
      let location = null;
      if (locationResponse && locationResponse.data.data) {
        const locationData = locationResponse.data.data;
        location = {
          id: vehicleId,
          position: [
            locationData.latitude || locationData.lat,
            locationData.longitude || locationData.lng,
          ] as [number, number],
          speed: locationData.speed || null,
          heading: locationData.heading || locationData.direction || null,
          lastUpdated: new Date(locationData.timestamp || Date.now()),
        };
      }

      // Inline polyline fetching
      const polylineResponse = await getVehiclePolyline(vehicleId);
      let polyline = null;
      let polylineStatus = 'live'; // 'live', 'fallback', or 'mock'

      if (polylineResponse && polylineResponse.data) {
        const polylineData = polylineResponse.data.data || polylineResponse.data;
        if (Array.isArray(polylineData)) {
          polyline = polylineData.map((point: any) => [
            point.latitude || point.lat || point[0],
            point.longitude || point.lng || point[1],
          ]);

          // Check if this is fallback data
          if (polylineResponse.fallback) {
            polylineStatus =
              polylineResponse.fallback_reason === 'no_previous_polyline' ? 'mock' : 'fallback';
            console.log(
              `Using ${polylineStatus} polyline for vehicle ${vehicleId}`,
              polylineResponse.fallback_reason === 'api_error'
                ? `(${polylineResponse.fallback_age_minutes} minutes old)`
                : ''
            );
          }
        }
      }

      // Update state for UI display
      if (location) {
        setVehicleLocation(location);
        setMapCenter(location.position as [number, number]);

        // Calculate speed using vehicle timestamps
        const vehicleTimestamp =
          location.lastUpdated instanceof Date
            ? location.lastUpdated.getTime()
            : new Date(location.lastUpdated).getTime();

        // Get current previous location state
        setPreviousVehicleLocation(prev => {
          if (!prev) {
            // Set initial vehicle location without calculating speed
            return {
              latitude: location.position[0], // latitude
              longitude: location.position[1], // longitude
              timestamp: vehicleTimestamp,
            };
          } else {
            // Calculate speed using previous vehicle location
            const currentTime = new Date(
              location.lastUpdated instanceof Date
                ? location.lastUpdated.toISOString()
                : location.lastUpdated
            ).getTime();

            // Calculate distance using Haversine formula
            const distance = calculateDistance(
              prev.latitude,
              prev.longitude,
              location.position[0], // latitude
              location.position[1] // longitude
            );

            // Calculate time difference in seconds
            const timeDiff = (currentTime - prev.timestamp) / 1000;

            if (timeDiff > 0) {
              // Speed in m/s
              const speedMS = distance / timeDiff;
              // Convert to km/h
              const speedKMH = speedMS * 3.6;
              // Update speed state for UI display
              setCurrentSpeed(speedKMH);
            }

            // Return new previous location for next calculation
            return {
              latitude: location.position[0], // latitude
              longitude: location.position[1], // longitude
              timestamp: vehicleTimestamp,
            };
          }
        });
      }

      // Send update to WebView using injectJavaScript for more reliable delivery
      if (webViewRef.current && isWebViewLoaded && (location || polyline)) {
        let script = '';

        if (location) {
          // Calculate rotation for both marker and map
          const vehicleHeading = location.heading || 0;
          const mapRotation = -vehicleHeading; // Negative to rotate map opposite to vehicle heading

          script += `
            if (typeof vehicleMarker !== 'undefined' && vehicleMarker && typeof map !== 'undefined') {
              vehicleMarker.setLatLng([${location.position[0]}, ${location.position[1]}]);
              vehicleMarker.setPopupContent('<b>Vehicle Position</b><br>Speed: ${Math.round(
                currentSpeed
              )} km/h<br>Heading: ${location.heading || 0}°');
              
              // Rotate the vehicle marker to show direction of travel
              if (typeof vehicleMarker.setRotationAngle === 'function') {
                vehicleMarker.setRotationAngle(${vehicleHeading});
              } else if (vehicleMarker._icon) {
                // Fallback: rotate the marker icon using CSS
                vehicleMarker._icon.style.transform = 'rotate(${vehicleHeading}deg)';
                vehicleMarker._icon.style.transformOrigin = 'center';
              }
              
              // Center map on vehicle location
              map.setView([${location.position[0]}, ${location.position[1]}], 16, {
                animate: true,
                duration: 1.0
              });
              
              // Rotate the entire map so vehicle's direction of travel points up
              const mapElement = document.getElementById('map');
              if (mapElement) {
                mapElement.style.transform = 'rotate(${mapRotation}deg)';
                mapElement.style.transformOrigin = 'center';
              }
              
              console.log('Updated vehicle position, rotated marker to ${vehicleHeading}°, and rotated map to ${mapRotation}°:', [${
            location.position[0]
          }, ${location.position[1]}]);
            }
          `;
        }
        if (polyline) {
          const polylineString = JSON.stringify(polyline);
          script += `
            if (typeof routePolyline !== 'undefined' && routePolyline) {
              routePolyline.setLatLngs(${polylineString});
              console.log('Updated polyline with', ${polyline.length}, 'points');
            }
          `;
        }

        // Update polyline status indicator
        script += `
          if (typeof updatePolylineStatusIndicator === 'function') {
            updatePolylineStatusIndicator('${polylineStatus}', ${
          polylineStatus === 'fallback' ? polylineResponse.fallback_age_minutes || 0 : 0
        });
          }
        `;

        if (script) {
          webViewRef.current.injectJavaScript(script);
        }
      } else {
        webViewLoadAttempts.current += 1;
        const currentAttempts = webViewLoadAttempts.current;

        // If we've tried 3 times and WebView still not loaded, force it
        if (currentAttempts >= 3 && !isWebViewLoaded) {
          setIsWebViewLoaded(true);
          // Retry sending the update
          if (webViewRef.current && (location || polyline)) {
            let script = '';

            if (location) {
              // Calculate rotation for both marker and map
              const vehicleHeading = location.heading || 0;
              const mapRotation = -vehicleHeading; // Negative to rotate map opposite to vehicle heading

              script += `
                if (typeof vehicleMarker !== 'undefined' && vehicleMarker && typeof map !== 'undefined') {
                  vehicleMarker.setLatLng([${location.position[0]}, ${location.position[1]}]);
                  vehicleMarker.setPopupContent('<b>Vehicle Position</b><br>Speed: ${Math.round(
                    currentSpeed
                  )} km/h<br>Heading: ${location.heading || 0}°');
                  
                  // Rotate the vehicle marker to show direction of travel
                  if (typeof vehicleMarker.setRotationAngle === 'function') {
                    vehicleMarker.setRotationAngle(${vehicleHeading});
                  } else if (vehicleMarker._icon) {
                    // Fallback: rotate the marker icon using CSS
                    vehicleMarker._icon.style.transform = 'rotate(${vehicleHeading}deg)';
                    vehicleMarker._icon.style.transformOrigin = 'center';
                  }
                  
                  // Center map on vehicle location
                  map.setView([${location.position[0]}, ${location.position[1]}], 16, {
                    animate: true,
                    duration: 1.0
                  });
                  
                  // Rotate the entire map so vehicle's direction of travel points up
                  const mapElement = document.getElementById('map');
                  if (mapElement) {
                    mapElement.style.transform = 'rotate(${mapRotation}deg)';
                    mapElement.style.transformOrigin = 'center';
                  }
                  
                  console.log('Updated vehicle position, rotated marker to ${vehicleHeading}°, and rotated map to ${mapRotation}°:', [${
                location.position[0]
              }, ${location.position[1]}]);
                }
              `;
            }
            if (polyline) {
              const polylineString = JSON.stringify(polyline);
              script += `
                if (typeof routePolyline !== 'undefined' && routePolyline) {
                  routePolyline.setLatLngs(${polylineString});
                  console.log('Updated polyline with', ${polyline.length}, 'points');
                }
              `;
            }

            // Update polyline status indicator in retry logic too
            script += `
              if (typeof updatePolylineStatusIndicator === 'function') {
                updatePolylineStatusIndicator('${polylineStatus}', ${
              polylineStatus === 'fallback' ? polylineResponse.fallback_age_minutes || 0 : 0
            });
              }
            `;

            if (script) {
              webViewRef.current.injectJavaScript(script);
            }
          }
        }
      }
    } catch (err) {
      console.error('Error fetching vehicle data:', err);
    }
  }, [
    activeTrip?.vehicle_id,
    activeTrip?.vehicleId,
    calculateDistance,
    isWebViewLoaded,
    currentSpeed,
  ]);

  const stopStatusMonitoring = useCallback(() => {
    if (statusCheckInterval) {
      clearInterval(statusCheckInterval);
      setStatusCheckInterval(null);
    }
  }, [statusCheckInterval]);

  // Use context's active trip checking instead of local fetch
  const fetchActiveTrip = useCallback(async () => {
    await checkForActiveTrip();
  }, [checkForActiveTrip]);

  // Function to generate stable map HTML
  // Handle WebView load - fetch initial vehicle data
  const handleWebViewLoad = useCallback(() => {
    setIsWebViewLoaded(true);
    // Fetch initial vehicle data when WebView is ready
    setTimeout(() => {
      fetchVehicleData();
    }, 500); // Small delay to ensure WebView is fully initialized
  }, [fetchVehicleData]);

  // Backup mechanism - if WebView doesn't load within 10 seconds, force it to be ready
  useEffect(() => {
    const backupTimer = setTimeout(() => {
      if (!isWebViewLoaded) {
        setIsWebViewLoaded(true);
        // Try to fetch vehicle data anyway
        fetchVehicleData();
      }
    }, 10000); // 10 seconds timeout

    return () => clearTimeout(backupTimer);
  }, [isWebViewLoaded, fetchVehicleData]);

  const getMapHTML = useCallback(() => {
    const pickup = activeTrip?.origin?.location?.coordinates
      ? [activeTrip.origin.location.coordinates[1], activeTrip.origin.location.coordinates[0]]
      : [37.7749, -122.4194];

    const destination = activeTrip?.destination?.location?.coordinates
      ? [
          activeTrip.destination.location.coordinates[1],
          activeTrip.destination.location.coordinates[0],
        ]
      : [37.6197, -122.3875];

    // Get waypoints data if available
    const waypoints =
      activeTrip?.waypoints?.map((waypoint: any) => ({
        id: waypoint.id,
        coordinates: waypoint.location?.coordinates
          ? [waypoint.location.coordinates[1], waypoint.location.coordinates[0]]
          : null,
        name: waypoint.name || `Waypoint ${waypoint.order || ''}`,
        order: waypoint.order || 0,
      })) || [];

    const initialVehiclePos = pickup; // Start at pickup, will be updated via postMessage
    const initialPolylineCoords = [pickup, destination]; // Basic route, will be updated via postMessage

    return `
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Active Trip Map</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <!-- Add Leaflet rotation plugin for proper map orientation -->
    <script src="https://cdn.jsdelivr.net/npm/leaflet-rotatedmarker@0.2.0/leaflet.rotatedMarker.min.js"></script>
    <style>
        body { margin: 0; padding: 0; overflow: hidden; }
        #mapContainer { 
            position: relative;
            width: 100vw; 
            height: 100vh; 
            overflow: hidden;
        }
        #map { 
            width: 300vw; 
            height: 300vh; 
            position: absolute;
            left: -100vw;
            top: -100vh;
            transition: transform 0.5s ease-out;
        }
    </style>
</head>
<body>
    <div id="mapContainer">
        <div id="map"></div>
    </div>
    <script>
        // Global variables for map elements that need updates
        let map;
        let vehicleMarker;
        let routePolyline;
        
        // Initialize the map with better zoom constraints and rotation
        map = L.map('map', {
            center: [${pickup[0]}, ${pickup[1]}],
            zoom: 10,     // Lower initial zoom (will be adjusted by fitBounds)
            minZoom: 3,   // Allow zooming out very far for context
            maxZoom: 18,  // Allow detailed zoom
            zoomControl: true,
            dragging: false,        // Disable panning/dragging
            touchZoom: true,        // Allow zoom via touch gestures
            doubleClickZoom: true,  // Allow double-click zoom
            scrollWheelZoom: true,  // Allow scroll wheel zoom
            boxZoom: false,         // Disable box zoom
            keyboard: false,        // Disable keyboard controls
            rotate: false,          // Disable map rotation
            bearing: 0,             // Initial rotation angle
            touchRotate: false,     // Disable rotation via touch gestures
            rotateControl: false    // Hide rotation control
        });
        
        // Add OpenStreetMap tile layer
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 18
        }).addTo(map);
        
        // Function to truncate location text at first comma
        const truncateAtComma = (text) => {
            if (!text) return '';
            const commaIndex = text.indexOf(',');
            return commaIndex !== -1 ? text.substring(0, commaIndex) : text;
        };
        
        // Define initial coordinates
        const pickup = [${pickup[0]}, ${pickup[1]}];
        const destination = [${destination[0]}, ${destination[1]}];
        let vehiclePosition = [${initialVehiclePos[0]}, ${initialVehiclePos[1]}];
        let routeCoordinates = ${JSON.stringify(initialPolylineCoords)};
        
        // Get waypoints data if available
        const waypoints = ${JSON.stringify(waypoints)};
        
        // Get location names and truncate at first comma
        const pickupFullName = "${
          activeTrip?.origin?.name || activeTrip?.origin?.address || 'Pickup Location'
        }";
        const pickupName = truncateAtComma(pickupFullName);
        
        const destinationFullName = "${
          activeTrip?.destination?.name || activeTrip?.destination?.address || 'Destination'
        }";
        const destinationName = truncateAtComma(destinationFullName);
        
        // Custom icons for better visibility
        const blueIcon = L.icon({
            iconUrl: 'data:image/svg+xml;base64,' + btoa('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#007AFF"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg>'),
            iconSize: [30, 30],
            iconAnchor: [15, 30],
            popupAnchor: [0, -30]
        });
        
        const greenIcon = L.icon({
            iconUrl: 'data:image/svg+xml;base64,' + btoa('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="green"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg>'),
            iconSize: [30, 30],
            iconAnchor: [15, 30],
            popupAnchor: [0, -30]
        });

        const vehicleIcon = L.icon({
            iconUrl: 'data:image/svg+xml;base64,' + btoa('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#4285F4"><path d="M12 2 L18 12 L12 10 L6 12 Z" stroke="white" stroke-width="1.5" stroke-linejoin="round"/></svg>'),
            iconSize: [96, 96],
            iconAnchor: [48, 48],
            popupAnchor: [0, -48]
        });
        
        const waypointIcon = L.icon({
            iconUrl: 'data:image/svg+xml;base64,' + btoa('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#f59e0b"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg>'),
            iconSize: [25, 25],
            iconAnchor: [12, 25],
            popupAnchor: [0, -25]
        });
        
        // Add static markers (these don't change)
        const startMarker = L.marker(pickup, { icon: blueIcon }).addTo(map)
            .bindPopup('<b>From:</b><br>' + pickupName);
        
        const endMarker = L.marker(destination, { icon: greenIcon }).addTo(map)
            .bindPopup('<b>To:</b><br>' + destinationName);

        // Add initial vehicle marker (this will be updated)
        vehicleMarker = L.marker(vehiclePosition, { icon: vehicleIcon }).addTo(map)
            .bindPopup('<b>Vehicle Position</b><br>Speed: 0 km/h'); // Initial speed, will be updated via postMessage
        
        // Add waypoint markers
        const waypointMarkers = [];
        waypoints.forEach((waypoint, index) => {
            if (waypoint.coordinates && waypoint.coordinates.length === 2) {
                const waypointMarker = L.marker(waypoint.coordinates, { icon: waypointIcon }).addTo(map)
                    .bindPopup('<b>Waypoint:</b><br>' + waypoint.name);
                waypointMarkers.push(waypointMarker);
            }
        });
        
        // Add priority indicator in top right corner
        const priorityText = "${
          activeTrip?.priority
            ? activeTrip.priority.charAt(0).toUpperCase() + activeTrip.priority.slice(1)
            : 'Normal'
        }";
        
        // Define priority colors for low, normal, high, urgent
        let priorityColor;
        switch(priorityText.toLowerCase()) {
            case 'low':
                priorityColor = '#10b981'; // Green
                break;
            case 'normal':
                priorityColor = '#6366f1'; // Blue (accent color)
                break;
            case 'high':
                priorityColor = '#f59e0b'; // Orange
                break;
            case 'urgent':
                priorityColor = '#dc2626'; // Red
                break;
            default:
                priorityColor = '#6366f1'; // Default to blue
        }
        
        const cardBg = "${theme.cardBackground}";
        const textColor = "${theme.text}";
        
        const priorityCard = L.control({position: 'topright'});
        priorityCard.onAdd = function (map) {
            const div = L.DomUtil.create('div', 'priority-indicator');
            div.innerHTML = '<div style="background: ' + cardBg + '; padding: 10px 16px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); border: 2px solid ' + priorityColor + '; min-width: 80px;"><div style="font-size: 10px; color: ' + textColor + '; font-weight: 500; margin-bottom: 2px;">Priority:</div><div style="color: ' + priorityColor + '; font-size: 14px; font-weight: bold;">' + priorityText + '</div></div>';
            return div;
        };
        priorityCard.addTo(map);

        // Add status indicator in top left corner
        const statusCard = L.control({position: 'topleft'});
        statusCard.onAdd = function (map) {
            const div = L.DomUtil.create('div', 'status-indicator');
            div.innerHTML = '<div style="background: ' + cardBg + '; padding: 10px 16px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); border: 2px solid #10b981; min-width: 80px;"><div style="font-size: 10px; color: ' + textColor + '; font-weight: 500; margin-bottom: 2px;">Status:</div><div style="color: #10b981; font-size: 14px; font-weight: bold;">In Progress</div></div>';
            return div;
        };
        statusCard.addTo(map);

        // Add polyline status indicator in bottom left corner (initially hidden)
        const polylineStatusCard = L.control({position: 'bottomleft'});
        polylineStatusCard.onAdd = function (map) {
            const div = L.DomUtil.create('div', 'polyline-status-indicator');
            div.style.display = 'none'; // Initially hidden
            div.innerHTML = '<div style="background: ' + cardBg + '; padding: 8px 12px; border-radius: 6px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border: 2px solid #f59e0b; opacity: 0.9;"><div style="color: #f59e0b; font-size: 12px; font-weight: bold;">Route Status</div><div style="font-size: 10px; color: ' + textColor + '; margin-top: 2px;">Fallback Data</div></div>';
            return div;
        };
        polylineStatusCard.addTo(map);

        // Add initial route polyline (this will be updated)
        if (routeCoordinates.length > 0) {
            routePolyline = L.polyline(routeCoordinates, {
                color: '#007AFF',
                weight: 6,
                opacity: 0.8
            }).addTo(map);
            
            // Fit map to show entire route with tighter bounds including waypoints
            const allMarkers = [startMarker, endMarker, vehicleMarker, ...waypointMarkers];
            const group = new L.featureGroup([...allMarkers, routePolyline]);
            const bounds = group.getBounds();
            
            // Use adequate padding to ensure all markers are clearly visible
            map.fitBounds(bounds, {
                padding: [80, 80] // Generous padding to ensure all locations are visible
            });
        } else {
            // If no route, fit to markers with appropriate zoom including waypoints
            const allMarkers = [startMarker, endMarker, vehicleMarker, ...waypointMarkers];
            const group = new L.featureGroup(allMarkers);
            const bounds = group.getBounds();
            
            // Always use generous padding to ensure all markers are visible
            map.fitBounds(bounds, {
                padding: [100, 100] // Large padding to guarantee all locations are visible
            });
        }
        
        // Function to update vehicle position and polyline without re-rendering the map
        function updateMapElements(data) {
            console.log('Received map update:', data);
            
            if (data.vehiclePosition && vehicleMarker) {
                console.log('Updating vehicle position to:', data.vehiclePosition);
                // Update vehicle marker position
                vehicleMarker.setLatLng(data.vehiclePosition);
                
                // Update popup content with new speed
                const speed = data.speed ? Math.round(data.speed) : 0;
                vehicleMarker.setPopupContent('<b>Vehicle Position</b><br>Speed: ' + speed + ' km/h');
            }
            
            if (data.polyline && routePolyline) {
                console.log('Updating polyline with', data.polyline.length, 'points');
                // Update route polyline
                routePolyline.setLatLngs(data.polyline);
            }
            
            // Update polyline status indicator
            if (data.polylineStatus) {
                updatePolylineStatusIndicator(data.polylineStatus, data.polylineAge);
            }
        }
        
        // Function to update polyline status indicator
        function updatePolylineStatusIndicator(status, age) {
            const statusElement = document.querySelector('.polyline-status-indicator');
            if (!statusElement) return;
            
            if (status === 'live') {
                // Hide indicator for live data
                statusElement.style.display = 'none';
            } else {
                // Show indicator for fallback/mock data
                statusElement.style.display = 'block';
                const statusDiv = statusElement.querySelector('div');
                
                if (status === 'fallback') {
                    const ageText = age ? \` (\${age}m old)\` : '';
                    statusDiv.innerHTML = '<div style="background: ' + cardBg + '; padding: 8px 12px; border-radius: 6px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border: 2px solid #f59e0b; opacity: 0.9;"><div style="color: #f59e0b; font-size: 12px; font-weight: bold;">Route Status</div><div style="font-size: 10px; color: ' + textColor + '; margin-top: 2px;">Fallback Data' + ageText + '</div></div>';
                } else if (status === 'mock') {
                    statusDiv.innerHTML = '<div style="background: ' + cardBg + '; padding: 8px 12px; border-radius: 6px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border: 2px solid #ef4444; opacity: 0.9;"><div style="color: #ef4444; font-size: 12px; font-weight: bold;">Route Status</div><div style="font-size: 10px; color: ' + textColor + '; margin-top: 2px;">Mock Data</div></div>';
                }
            }
        }
        
        // Listen for messages from React Native
        window.addEventListener('message', function(event) {
            console.log('WebView received message:', event.data);
            try {
                const data = JSON.parse(event.data);
                if (data.type === 'UPDATE_MAP') {
                    updateMapElements(data);
                } else {
                    console.log('Unknown message type:', data.type);
                }
            } catch (error) {
                console.error('Error parsing message:', error);
            }
        });
        
        // Add a short delay to ensure all elements are rendered before final zoom adjustment
        setTimeout(() => {
            // Force refresh of map size and re-fit bounds for better display
            map.invalidateSize();
            
            // Re-fit to ensure optimal zoom after map is fully loaded including waypoints
            if (routeCoordinates.length > 0) {
                const allElements = [startMarker, endMarker, vehicleMarker, ...waypointMarkers];
                const group = new L.featureGroup(allElements);
                map.fitBounds(group.getBounds(), {
                    padding: [80, 80] // Good padding in delayed fit
                });
            }
        }, 500);
        
        console.log('Active trip Leaflet map initialized successfully');
        console.log('Pickup:', pickup);
        console.log('Destination:', destination);
        console.log('Vehicle Position:', vehiclePosition);
        console.log('Route points:', routeCoordinates.length);
        console.log('Map bounds fitted with automatic zoom');
        console.log('Map is ready to receive updates via postMessage');
    </script>
</body>
</html>
    `;
  }, [activeTrip, theme]);

  // Memoize the HTML so it only generates once and doesn't cause re-renders
  const mapHTML = useMemo(() => getMapHTML(), [getMapHTML]);

  const handleEndTrip = useCallback(async () => {
    if (!activeTrip) return;

    Alert.alert('End Trip', 'Are you sure you want to end this trip?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'End Trip',
        style: 'destructive',
        onPress: async () => {
          setEndingTrip(true);

          try {
            const now = new Date().toISOString();
            const data = {
              actual_end_time: now,
              status: 'completed',
            };

            const tripId = activeTrip.id || activeTrip._id;
            if (!tripId) {
              throw new Error('Trip ID not found');
            }

            console.log('Ending trip ID:', tripId);

            const response = await finishTrip(tripId, data);
            console.log('Response for ending trip:', response);

            stopStatusMonitoring();
            stopLocationPing(); // Stop location pinging when trip is finished
            stopSpeedLimitChecking(); // Stop speed limit checking when trip is finished
            clearActiveTrip();
            setVehicleLocation(null);

            console.log(`Trip ${tripId} ended successfully`);

            // Navigate back to dashboard
            navigation.navigate('Dashboard');
          } catch (err) {
            console.error('Error ending trip:', err);
            Alert.alert('Error', 'Failed to end trip. Please try again.');
          } finally {
            setEndingTrip(false);
          }
        },
      },
    ]);
  }, [
    activeTrip,
    navigation,
    stopStatusMonitoring,
    clearActiveTrip,
    stopLocationPing,
    stopSpeedLimitChecking,
  ]);

  const handlePauseResumeTrip = useCallback(async () => {
    if (!activeTrip) return;

    const action = isPaused ? 'resume' : 'pause';
    const actionText = isPaused ? 'Resume Trip' : 'Pause Trip';
    const confirmText = isPaused
      ? 'Are you sure you want to resume this trip?'
      : 'Are you sure you want to pause this trip?';

    Alert.alert(actionText, confirmText, [
      { text: 'Cancel', style: 'cancel' },
      {
        text: actionText,
        onPress: async () => {
          setPausingTrip(true);

          try {
            const tripId = activeTrip.id || activeTrip._id;
            if (!tripId) {
              throw new Error('Trip ID not found');
            }

            console.log(`${action}ing trip ID:`, tripId);

            const response = isPaused ? await resumeTrip(tripId) : await pauseTrip(tripId);
            console.log(`Response for ${action}ing trip:`, response);

            setIsPaused(!isPaused);

            console.log(`Trip ${tripId} ${action}d successfully`);
          } catch (err) {
            console.error(`Error ${action}ing trip:`, err);
            Alert.alert('Error', `Failed to ${action} trip. Please try again.`);
          } finally {
            setPausingTrip(false);
          }
        },
      },
    ]);
  }, [activeTrip, isPaused]);

  const handleCancelTrip = useCallback(async () => {
    if (!activeTrip) return;

    Alert.alert(
      'Cancel Trip',
      'Are you sure you want to cancel this trip? This action cannot be undone.',
      [
        { text: 'No', style: 'cancel' },
        {
          text: 'Yes, Cancel Trip',
          style: 'destructive',
          onPress: async () => {
            setCancelingTrip(true);

            try {
              const tripId = activeTrip.id || activeTrip._id;
              if (!tripId) {
                throw new Error('Trip ID not found');
              }

              console.log('Canceling trip ID:', tripId);

              const response = await cancelTrip(tripId);
              console.log('Response for canceling trip:', response);

              stopStatusMonitoring();
              stopLocationPing(); // Stop location pinging when trip is cancelled
              stopSpeedLimitChecking(); // Stop speed limit checking when trip is cancelled
              clearActiveTrip();
              setVehicleLocation(null);

              console.log(`Trip ${tripId} cancelled successfully`);

              // Navigate back to dashboard
              navigation.navigate('Dashboard');
            } catch (err) {
              console.error('Error canceling trip:', err);
              Alert.alert('Error', 'Failed to cancel trip. Please try again.');
            } finally {
              setCancelingTrip(false);
            }
          },
        },
      ]
    );
  }, [
    activeTrip,
    navigation,
    stopStatusMonitoring,
    clearActiveTrip,
    stopLocationPing,
    stopSpeedLimitChecking,
  ]);

  // Handle trip completion when near destination
  const handleCompleteTrip = useCallback(async () => {
    if (!activeTrip) return;

    Alert.alert(
      'Complete Trip',
      'You are near the destination. Would you like to complete this trip?',
      [
        { text: 'Not Yet', style: 'cancel' },
        {
          text: 'Complete Trip',
          style: 'default',
          onPress: async () => {
            setEndingTrip(true);

            try {
              const tripId = activeTrip.id || activeTrip._id;
              if (!tripId) {
                throw new Error('Trip ID not found');
              }

              console.log('Completing trip ID:', tripId);

              const response = await completeTrip(tripId);
              console.log('Response for completing trip:', response);

              stopStatusMonitoring();
              stopLocationPing(); // Stop location pinging when trip is completed
              stopSpeedLimitChecking(); // Stop speed limit checking when trip is completed
              clearActiveTrip();
              setVehicleLocation(null);

              console.log(`Trip ${tripId} completed successfully`);

              // Navigate back to dashboard
              navigation.navigate('Dashboard');
            } catch (err) {
              console.error('Error completing trip:', err);
              Alert.alert('Error', 'Failed to complete trip. Please try again.');
            } finally {
              setEndingTrip(false);
            }
          },
        },
      ]
    );
  }, [
    activeTrip,
    navigation,
    stopStatusMonitoring,
    clearActiveTrip,
    stopLocationPing,
    stopSpeedLimitChecking,
    setEndingTrip,
  ]);

  // Fetch active trip on component mount
  useEffect(() => {
    fetchActiveTrip();

    return () => {
      stopStatusMonitoring();
    };
  }, [fetchActiveTrip, stopStatusMonitoring]);

  // Get initial location when component mounts
  useEffect(() => {
    const getInitialLocation = async () => {
      const location = await getCurrentLocation();
      if (location) {
        // Set initial previous location for speed calculations
        if (!previousLocation) {
          const initialTime = Date.now();
          setPreviousLocation({
            latitude: location.latitude,
            longitude: location.longitude,
            timestamp: initialTime,
          });
        }
      }
    };

    getInitialLocation();
  }, [getCurrentLocation, previousLocation]);

  // Fetch vehicle data when active trip changes and poll for updates
  useEffect(() => {
    if (!activeTrip) {
      setVehicleLocation(null);
      return;
    }

    // Initial fetch
    fetchVehicleData();

    // Set up polling every 3 seconds for live updates
    const dataInterval = setInterval(() => {
      fetchVehicleData();
    }, 3000);

    return () => clearInterval(dataInterval);
  }, [activeTrip, fetchVehicleData]);

  // Reset WebView loaded state when component mounts or activeTrip changes
  useEffect(() => {
    setIsWebViewLoaded(false);
    webViewLoadAttempts.current = 0;
  }, [activeTrip?.id]);

  // Reset WebView loaded state when component unmounts
  useEffect(() => {
    return () => {
      setIsWebViewLoaded(false);
      webViewLoadAttempts.current = 0;
    };
  }, []);

  // Manage location pinging based on trip state
  useEffect(() => {
    if (activeTrip && !isPaused) {
      // Start pinging when trip is active and not paused
      startLocationPing();
    } else {
      // Stop pinging when trip is paused or ended
      stopLocationPing();
    }

    // Cleanup when component unmounts or dependencies change
    return () => {
      stopLocationPing();
    };
  }, [activeTrip, isPaused, startLocationPing, stopLocationPing]);

  // Manage speed limit checking based on trip state
  useEffect(() => {
    if (activeTrip && !isPaused) {
      // Start speed limit checking when trip is active and not paused
      startSpeedLimitChecking();
    } else {
      // Stop speed limit checking when trip is paused or ended
      stopSpeedLimitChecking();
    }

    // Cleanup when component unmounts or dependencies change
    return () => {
      stopSpeedLimitChecking();
    };
  }, [activeTrip, isPaused, startSpeedLimitChecking, stopSpeedLimitChecking]);

  if (isCheckingActiveTrip) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
        <View
          style={[
            styles.header,
            { backgroundColor: theme.cardBackground, borderBottomColor: theme.border },
          ]}
        >
          {shouldShowBackButton && (
            <TouchableOpacity
              onPress={navigation.goBack}
              style={[styles.backButton, { backgroundColor: theme.accent + '20' }]}
            >
              <ArrowLeft size={24} color={theme.accent} />
            </TouchableOpacity>
          )}
          {!shouldShowBackButton && <View style={styles.headerRight} />}
          <Text style={[styles.headerTitle, { color: theme.text }]}>Active Trip</Text>
        </View>
        <View style={styles.loadingContainer}>
          <Navigation size={48} color={theme.accent} />
          <Text style={[styles.loadingText, { color: theme.textSecondary }]}>
            Loading active trip...
          </Text>
        </View>
      </SafeAreaView>
    );
  }

  if (error || !activeTrip) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
        <View
          style={[
            styles.header,
            { backgroundColor: theme.cardBackground, borderBottomColor: theme.border },
          ]}
        >
          {shouldShowBackButton && (
            <TouchableOpacity
              onPress={navigation.goBack}
              style={[styles.backButton, { backgroundColor: theme.accent + '20' }]}
            >
              <ArrowLeft size={24} color={theme.accent} />
            </TouchableOpacity>
          )}
          {!shouldShowBackButton && <View style={styles.headerRight} />}
          <Text style={[styles.headerTitle, { color: theme.text }]}>Active Trip</Text>
        </View>
        <View style={styles.errorContainer}>
          <Navigation size={48} color={theme.textSecondary} />
          <Text style={[styles.errorText, { color: theme.textSecondary }]}>
            {error || 'No active trip found'}
          </Text>
          <TouchableOpacity
            onPress={checkForActiveTrip}
            style={[styles.retryButton, { backgroundColor: theme.accent }]}
          >
            <Text style={styles.retryButtonText}>Retry</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
      {/* Enhanced Header */}
      <View
        style={[
          styles.header,
          {
            backgroundColor: theme.cardBackground,
            borderBottomColor: theme.border,
            shadowColor: theme.shadow,
          },
        ]}
      >
        {shouldShowBackButton && (
          <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
            <View style={[styles.backButtonCircle, { backgroundColor: theme.accent + '20' }]}>
              <ArrowLeft size={20} color={theme.accent} />
            </View>
          </TouchableOpacity>
        )}
        {!shouldShowBackButton && <View style={styles.headerRight} />}
        <View style={styles.headerTitleContainer}>
          <Text style={[styles.headerTitle, { color: theme.text }]}>
            {activeTrip.name || 'Active Trip'}
          </Text>
          {activeTrip.priority && (
            <Text
              style={[
                styles.headerPriority,
                {
                  color: theme.background,
                  backgroundColor:
                    activeTrip.priority.toLowerCase() === 'low'
                      ? theme.success
                      : activeTrip.priority.toLowerCase() === 'normal'
                      ? theme.info
                      : activeTrip.priority.toLowerCase() === 'high'
                      ? theme.warning
                      : activeTrip.priority.toLowerCase() === 'urgent'
                      ? theme.danger
                      : theme.info,
                },
              ]}
            >
              {activeTrip.priority.charAt(0).toUpperCase() + activeTrip.priority.slice(1)}
            </Text>
          )}
          <Text style={[styles.headerDistance, { color: theme.success }]}>
            {activeTrip.estimated_distance
              ? (activeTrip.estimated_distance / 1000).toFixed(1) + ' km'
              : 'Distance N/A'}
          </Text>
        </View>
        <View style={styles.speedContainer}>
          <Text style={[styles.speedValue, { color: theme.accent }]}>
            {currentSpeed.toFixed(0)}
          </Text>
          <Text style={[styles.speedLabel, { color: theme.textSecondary }]}>km/h</Text>
          {speedLimit && <Text style={[{ color: theme.textSecondary }]}>Limit: {speedLimit}</Text>}
        </View>
      </View>

      {/* Leaflet Map Container */}
      <View style={styles.mapContainer}>
        <WebView
          key={`webview-${activeTrip?.id || 'default'}`}
          ref={webViewRef}
          style={styles.map}
          source={{
            html: mapHTML,
          }}
          onLoad={() => {
            handleWebViewLoad();
          }}
          onLoadEnd={() => {
            if (!isWebViewLoaded) {
              handleWebViewLoad();
            }
          }}
          onError={webViewError => {
            console.error('WebView error:', webViewError);
          }}
          onMessage={_event => {
            // Handle WebView messages if needed
          }}
          javaScriptEnabled={true}
          domStorageEnabled={true}
          startInLoadingState={true}
          scalesPageToFit={true}
        />

        {/* Trip Control Buttons */}
        <View style={styles.tripControlContainer}>
          {/* Pause/Resume Button - Only show if NOT near destination */}
          {!isNearDestination && (
            <TouchableOpacity
              onPress={handlePauseResumeTrip}
              disabled={pausingTrip}
              style={[
                styles.controlButton,
                {
                  backgroundColor: pausingTrip
                    ? isPaused
                      ? theme.success + '60'
                      : theme.accent + '60'
                    : isPaused
                    ? theme.success
                    : theme.accent,
                },
              ]}
            >
              {pausingTrip ? (
                <View style={styles.controlButtonContent}>
                  <View style={[styles.loadingSpinner, styles.loadingSpinnerWhite]} />
                  <Text style={styles.controlButtonText}>
                    {isPaused ? 'Resuming...' : 'Pausing...'}
                  </Text>
                </View>
              ) : (
                <View style={styles.controlButtonContent}>
                  {isPaused ? <Play size={18} color="white" /> : <Pause size={18} color="white" />}
                  <Text style={styles.controlButtonText}>{isPaused ? 'Resume' : 'Pause'}</Text>
                </View>
              )}
            </TouchableOpacity>
          )}

          {/* Cancel/Complete Trip Button */}
          <TouchableOpacity
            onPress={isNearDestination ? handleCompleteTrip : handleCancelTrip}
            disabled={cancelingTrip || endingTrip}
            style={[
              styles.controlButton,
              {
                backgroundColor: isNearDestination
                  ? endingTrip
                    ? theme.success + '60'
                    : theme.success
                  : cancelingTrip
                  ? theme.textSecondary + '60'
                  : theme.textSecondary,
              },
            ]}
          >
            {cancelingTrip || endingTrip ? (
              <View style={styles.controlButtonContent}>
                <View style={[styles.loadingSpinner, styles.loadingSpinnerWhite]} />
                <Text style={styles.controlButtonText}>
                  {isNearDestination ? 'Completing...' : 'Canceling...'}
                </Text>
              </View>
            ) : (
              <View style={styles.controlButtonContent}>
                {isNearDestination ? (
                  <CheckCircle size={18} color="white" />
                ) : (
                  <X size={18} color="white" />
                )}
                <Text style={styles.controlButtonText}>
                  {isNearDestination ? 'Complete Trip' : 'Cancel'}
                </Text>
              </View>
            )}
          </TouchableOpacity>

          {/* End Trip Button */}
          {canEndTrip && (
            <TouchableOpacity
              onPress={handleEndTrip}
              disabled={endingTrip}
              style={[
                styles.controlButton,
                { backgroundColor: endingTrip ? theme.danger + '60' : theme.danger },
              ]}
            >
              {endingTrip ? (
                <View style={styles.controlButtonContent}>
                  <View style={[styles.loadingSpinner, styles.loadingSpinnerWhite]} />
                  <Text style={styles.controlButtonText}>Ending...</Text>
                </View>
              ) : (
                <View style={styles.controlButtonContent}>
                  <Square size={18} color="white" />
                  <Text style={styles.controlButtonText}>End Trip</Text>
                </View>
              )}
            </TouchableOpacity>
          )}
        </View>
      </View>
    </SafeAreaView>
  );
};

export default ActiveTripScreen;
