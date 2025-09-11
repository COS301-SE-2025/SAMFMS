import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { View, Text, StyleSheet, Alert, TouchableOpacity, useColorScheme } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { ArrowLeft, Navigation, Square, Pause, Play, X } from 'lucide-react-native';
import { WebView } from 'react-native-webview';
import {
  finishTrip,
  getLocation,
  getVehiclePolyline,
  pauseTrip,
  resumeTrip,
  cancelTrip,
} from '../utils/api';
import { useActiveTripContext } from '../contexts/ActiveTripContext';

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
  headerRight: {
    width: 40,
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
  // Simplified Trip Schedule Card Styles
  tripScheduleCard: {
    flexDirection: 'column',
    justifyContent: 'space-between',
    alignItems: 'stretch',
    padding: 20,
    borderWidth: 1,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.12,
    shadowRadius: 8,
    elevation: 6,
  },
  scheduleInfo: {
    flex: 1,
    paddingRight: 0,
  },
  timeRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
    paddingHorizontal: 4,
  },
  timeLabel: {
    fontSize: 14,
    fontWeight: '500',
    width: 50,
    textAlign: 'left',
  },
  timeValue: {
    fontSize: 15,
    fontWeight: '600',
    flex: 1,
    textAlign: 'right',
    letterSpacing: 0.3,
  },
  statusContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'flex-end',
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 6,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '500',
  },
  liveDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    marginLeft: 8,
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
  const [vehicleLocation, setVehicleLocation] = useState<VehicleLocation | null>(null);
  const [_mapCenter, setMapCenter] = useState<[number, number]>([37.7749, -122.4194]);
  const [isWebViewLoaded, setIsWebViewLoaded] = useState(false);
  const webViewLoadAttempts = useRef(0);

  const isDarkMode = useColorScheme() === 'dark';

  const theme = {
    background: isDarkMode ? '#0f0f23' : '#f8fafc',
    cardBackground: isDarkMode ? '#1a1a2e' : '#ffffff',
    text: isDarkMode ? '#f1f5f9' : '#1e293b',
    textSecondary: isDarkMode ? '#94a3b8' : '#64748b',
    border: isDarkMode ? '#334155' : '#e2e8f0',
    accent: '#6366f1',
    success: '#10b981',
    warning: '#f59e0b',
    danger: '#dc2626',
    shadow: isDarkMode ? '#000000' : '#64748b',
  };

  const fetchVehicleLocation = useCallback(
    async (vehicleId: string): Promise<VehicleLocation | null> => {
      try {
        const response = await getLocation(vehicleId);
        console.log('Fetching vehicle location:', response);
        if (response && response.data.data) {
          const locationData = response.data.data;

          const location: VehicleLocation = {
            id: vehicleId,
            position: [
              locationData.latitude || locationData.lat,
              locationData.longitude || locationData.lng,
            ],
            speed: locationData.speed || null,
            heading: locationData.heading || locationData.direction || null,
            lastUpdated: new Date(locationData.timestamp || Date.now()),
          };

          return location;
        }

        console.warn(`No valid location data found for vehicle ${vehicleId}`);
        return null;
      } catch (err) {
        console.error('Error fetching vehicle location:', err);
        return null;
      }
    },
    []
  );

  const fetchVehiclePolyline = useCallback(
    async (vehicleId: string): Promise<Array<[number, number]> | null> => {
      try {
        console.log(`Fetching polyline for vehicle ${vehicleId}`);
        const response = await getVehiclePolyline(vehicleId);

        // Handle the response based on the backend structure
        if (response && response.data) {
          const polylineData = response.data.data || response.data;

          // Convert polyline data to coordinates array
          if (Array.isArray(polylineData)) {
            const coordinates: Array<[number, number]> = polylineData.map((point: any) => [
              point.latitude || point.lat || point[0],
              point.longitude || point.lng || point[1],
            ]);
            return coordinates;
          }
        }

        console.warn(`No valid polyline data found for vehicle ${vehicleId}`);
        return null;
      } catch (err) {
        console.error('Error fetching vehicle polyline:', err);
        return null;
      }
    },
    []
  );

  const fetchVehicleData = useCallback(async () => {
    if (!activeTrip?.vehicle_id && !activeTrip?.vehicleId) return;

    const vehicleId = activeTrip.vehicle_id || activeTrip.vehicleId;
    if (!vehicleId) return;

    try {
      const [location, polyline] = await Promise.all([
        fetchVehicleLocation(vehicleId),
        fetchVehiclePolyline(vehicleId),
      ]);

      // Update state for UI display
      if (location) {
        setVehicleLocation(location);
        setMapCenter(location.position);
      }

      // Send update to WebView using injectJavaScript for more reliable delivery
      if (webViewRef.current && isWebViewLoaded && (location || polyline)) {
        let script = '';

        if (location) {
          script += `
            if (typeof vehicleMarker !== 'undefined' && vehicleMarker && typeof map !== 'undefined') {
              vehicleMarker.setLatLng([${location.position[0]}, ${location.position[1]}]);
              vehicleMarker.setPopupContent('<b>Vehicle Position</b><br>Speed: ${
                location.speed || 0
              } km/h');
              
              // Center and zoom map on vehicle location
              map.setView([${location.position[0]}, ${location.position[1]}], 16, {
                animate: true,
                duration: 1.0
              });
              
              console.log('Updated vehicle position and centered map at:', [${
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

        if (script) {
          console.log('Injecting JavaScript to update map');
          webViewRef.current.injectJavaScript(script);
        }
      } else {
        webViewLoadAttempts.current += 1;
        const currentAttempts = webViewLoadAttempts.current;
        console.log(
          `WebView not ready for update, isLoaded: ${isWebViewLoaded}, attempt: ${currentAttempts}`
        );

        // If we've tried 3 times and WebView still not loaded, force it
        if (currentAttempts >= 3 && !isWebViewLoaded) {
          console.log('Forcing WebView to be considered loaded after 3 attempts');
          setIsWebViewLoaded(true);
          // Retry sending the update
          if (webViewRef.current && (location || polyline)) {
            let script = '';

            if (location) {
              script += `
                if (typeof vehicleMarker !== 'undefined' && vehicleMarker && typeof map !== 'undefined') {
                  vehicleMarker.setLatLng([${location.position[0]}, ${location.position[1]}]);
                  vehicleMarker.setPopupContent('<b>Vehicle Position</b><br>Speed: ${
                    location.speed || 0
                  } km/h');
                  
                  // Center and zoom map on vehicle location
                  map.setView([${location.position[0]}, ${location.position[1]}], 16, {
                    animate: true,
                    duration: 1.0
                  });
                  
                  console.log('Updated vehicle position and centered map at:', [${
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

            if (script) {
              console.log('Force injecting JavaScript after 3 attempts');
              webViewRef.current.injectJavaScript(script);
            }
          }
        }
      }
    } catch (err) {
      console.error('Error fetching vehicle data:', err);
    }
  }, [activeTrip, fetchVehicleLocation, fetchVehiclePolyline]);

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
    console.log('Leaflet map loaded successfully, setting isWebViewLoaded to true');
    setIsWebViewLoaded(true);
    // Fetch initial vehicle data when WebView is ready
    setTimeout(() => {
      console.log('Fetching initial vehicle data after WebView load');
      fetchVehicleData();
    }, 500); // Small delay to ensure WebView is fully initialized
  }, [fetchVehicleData]);

  // Backup mechanism - if WebView doesn't load within 10 seconds, force it to be ready
  useEffect(() => {
    const backupTimer = setTimeout(() => {
      if (!isWebViewLoaded) {
        console.log('WebView loading timeout - forcing isLoaded to true');
        setIsWebViewLoaded(true);
        // Try to fetch vehicle data anyway
        fetchVehicleData();
      }
    }, 10000); // 10 seconds timeout

    return () => clearTimeout(backupTimer);
  }, [isWebViewLoaded, fetchVehicleData]);

  const getMapHTML = () => {
    const pickup = activeTrip?.origin?.location?.coordinates
      ? [activeTrip.origin.location.coordinates[1], activeTrip.origin.location.coordinates[0]]
      : [37.7749, -122.4194];

    const destination = activeTrip?.destination?.location?.coordinates
      ? [
          activeTrip.destination.location.coordinates[1],
          activeTrip.destination.location.coordinates[0],
        ]
      : [37.6197, -122.3875];

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
    <style>
        body { margin: 0; padding: 0; }
        #map { height: 100vh; width: 100vw; }
    </style>
</head>
<body>
    <div id="map"></div>
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
            rotate: true, // Enable map rotation
            bearing: 0,   // Initial rotation angle
            touchRotate: true, // Enable rotation via touch gestures
            rotateControl: true // Show rotation control
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
            iconUrl: 'data:image/svg+xml;base64,' + btoa('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#3b82f6"><circle cx="12" cy="12" r="8" stroke="white" stroke-width="3"/><circle cx="12" cy="12" r="4"/></svg>'),
            iconSize: [24, 24],
            iconAnchor: [12, 12],
            popupAnchor: [0, -12]
        });
        
        // Add static markers (these don't change)
        const startMarker = L.marker(pickup, { icon: blueIcon }).addTo(map)
            .bindPopup('<b>From:</b><br>' + pickupName);
        
        const endMarker = L.marker(destination, { icon: greenIcon }).addTo(map)
            .bindPopup('<b>To:</b><br>' + destinationName);

        // Add initial vehicle marker (this will be updated)
        vehicleMarker = L.marker(vehiclePosition, { icon: vehicleIcon }).addTo(map)
            .bindPopup('<b>Vehicle Position</b><br>Speed: 0 km/h'); // Initial speed, will be updated via postMessage
        
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

        // Add initial route polyline (this will be updated)
        if (routeCoordinates.length > 0) {
            routePolyline = L.polyline(routeCoordinates, {
                color: '#007AFF',
                weight: 6,
                opacity: 0.8
            }).addTo(map);
            
            // Fit map to show entire route with tighter bounds
            const group = new L.featureGroup([startMarker, endMarker, vehicleMarker, routePolyline]);
            const bounds = group.getBounds();
            
            // Use adequate padding to ensure all markers are clearly visible
            map.fitBounds(bounds, {
                padding: [80, 80] // Generous padding to ensure all locations are visible
            });
        } else {
            // If no route, fit to markers with appropriate zoom
            const group = new L.featureGroup([startMarker, endMarker, vehicleMarker]);
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
            
            // Re-fit to ensure optimal zoom after map is fully loaded
            if (routeCoordinates.length > 0) {
                const allElements = [startMarker, endMarker, vehicleMarker];
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
  };

  // Memoize the HTML so it only generates once and doesn't cause re-renders
  const mapHTML = useMemo(() => getMapHTML(), [activeTrip, theme]);

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
  }, [activeTrip, navigation, stopStatusMonitoring, clearActiveTrip]);

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
  }, [activeTrip, navigation, stopStatusMonitoring, clearActiveTrip]);

  // Fetch active trip on component mount
  useEffect(() => {
    fetchActiveTrip();

    return () => {
      stopStatusMonitoring();
    };
  }, [fetchActiveTrip, stopStatusMonitoring]);

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
    console.log('Resetting WebView loaded state for new trip or component mount');
    setIsWebViewLoaded(false);
    webViewLoadAttempts.current = 0;
  }, [activeTrip?.id]);

  // Reset WebView loaded state when component unmounts
  useEffect(() => {
    return () => {
      console.log('Component unmounting - resetting WebView state');
      setIsWebViewLoaded(false);
      webViewLoadAttempts.current = 0;
    };
  }, []);

  if (isCheckingActiveTrip) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
        <View
          style={[
            styles.header,
            { backgroundColor: theme.cardBackground, borderBottomColor: theme.border },
          ]}
        >
          <TouchableOpacity
            onPress={navigation.goBack}
            style={[styles.backButton, { backgroundColor: theme.accent + '20' }]}
          >
            <ArrowLeft size={24} color={theme.accent} />
          </TouchableOpacity>
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
          <TouchableOpacity
            onPress={navigation.goBack}
            style={[styles.backButton, { backgroundColor: theme.accent + '20' }]}
          >
            <ArrowLeft size={24} color={theme.accent} />
          </TouchableOpacity>
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
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
          <View style={[styles.backButtonCircle, { backgroundColor: theme.accent + '20' }]}>
            <ArrowLeft size={20} color={theme.accent} />
          </View>
        </TouchableOpacity>
        <View style={styles.headerTitleContainer}>
          <Text style={[styles.headerTitle, { color: theme.text }]}>
            {activeTrip.name || 'Active Trip'}
          </Text>
          <Text style={[styles.headerDistance, { color: theme.success }]}>
            {activeTrip.estimated_distance
              ? (activeTrip.estimated_distance / 1000).toFixed(1) + ' km'
              : 'Distance N/A'}
          </Text>
        </View>
        <View style={styles.headerRight} />
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
            console.log('WebView onLoad triggered for trip:', activeTrip?.id);
            handleWebViewLoad();
          }}
          onLoadEnd={() => {
            console.log('WebView onLoadEnd triggered for trip:', activeTrip?.id);
            if (!isWebViewLoaded) {
              handleWebViewLoad();
            }
          }}
          onError={webViewError => {
            console.error('WebView error:', webViewError);
            console.log('WebView failed to load, isLoaded will remain false');
          }}
          onMessage={event => {
            console.log('WebView message:', event.nativeEvent.data);
          }}
          javaScriptEnabled={true}
          domStorageEnabled={true}
          startInLoadingState={true}
          scalesPageToFit={true}
        />

        {/* Trip Control Buttons */}
        <View style={styles.tripControlContainer}>
          {/* Pause/Resume Button */}
          <TouchableOpacity
            onPress={handlePauseResumeTrip}
            disabled={pausingTrip}
            style={[
              styles.controlButton,
              { backgroundColor: pausingTrip ? theme.warning + '60' : theme.warning },
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

          {/* Cancel Trip Button */}
          <TouchableOpacity
            onPress={handleCancelTrip}
            disabled={cancelingTrip}
            style={[
              styles.controlButton,
              {
                backgroundColor: cancelingTrip ? theme.textSecondary + '60' : theme.textSecondary,
              },
            ]}
          >
            {cancelingTrip ? (
              <View style={styles.controlButtonContent}>
                <View style={[styles.loadingSpinner, styles.loadingSpinnerWhite]} />
                <Text style={styles.controlButtonText}>Canceling...</Text>
              </View>
            ) : (
              <View style={styles.controlButtonContent}>
                <X size={18} color="white" />
                <Text style={styles.controlButtonText}>Cancel</Text>
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

      {/* Simplified Trip Schedule Card */}
      <View
        style={[
          styles.tripScheduleCard,
          {
            backgroundColor: theme.cardBackground,
            shadowColor: theme.shadow,
            borderColor: theme.border,
          },
        ]}
      >
        <View style={styles.scheduleInfo}>
          <View style={styles.timeRow}>
            <Text style={[styles.timeLabel, { color: theme.textSecondary }]}>From:</Text>
            <Text style={[styles.timeValue, { color: theme.text }]} numberOfLines={1}>
              {activeTrip.origin?.name || activeTrip.origin?.address || 'Unknown'}
            </Text>
          </View>
          <View style={styles.timeRow}>
            <Text style={[styles.timeLabel, { color: theme.textSecondary }]}>To:</Text>
            <Text style={[styles.timeValue, { color: theme.text }]} numberOfLines={1}>
              {activeTrip.destination?.name || activeTrip.destination?.address || 'Unknown'}
            </Text>
          </View>
          <View style={styles.timeRow}>
            <Text style={[styles.timeLabel, { color: theme.textSecondary }]}>Status:</Text>
            <View style={styles.statusContainer}>
              <View style={[styles.statusDot, { backgroundColor: theme.success }]} />
              <Text style={[styles.statusText, { color: theme.success }]}>In Progress</Text>
              <View style={[styles.liveDot, { backgroundColor: theme.danger }]} />
            </View>
          </View>
        </View>
      </View>
    </SafeAreaView>
  );
};

export default ActiveTripScreen;
