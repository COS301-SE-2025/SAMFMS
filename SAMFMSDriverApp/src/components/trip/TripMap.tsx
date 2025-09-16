import React, { useRef, useCallback } from 'react';
import { View, StyleSheet } from 'react-native';
import { WebView } from 'react-native-webview';
import { useTheme } from '../../contexts/ThemeContext';

interface TripMapProps {
  activeTrip: any;
  isWebViewLoaded: boolean;
  onWebViewLoad: () => void;
  onWebViewLoadEnd: () => void;
  onWebViewError: (error: any) => void;
  onWebViewMessage: (event: any) => void;
  webViewRef?: React.RefObject<WebView | null>;
}

const TripMap: React.FC<TripMapProps> = ({
  activeTrip,
  isWebViewLoaded,
  onWebViewLoad,
  onWebViewLoadEnd,
  onWebViewError,
  onWebViewMessage,
  webViewRef,
}) => {
  const { theme } = useTheme();
  const localWebViewRef = useRef<WebView>(null);

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
        body { margin: 0; padding: 0; overflow: hidden; font-family: system-ui, -apple-system, sans-serif; }
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
            iconUrl: 'data:image/svg+xml;base64,' + btoa('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#4285F4"><path d="M12 2 L18 12 L12 22 L6 12 Z" stroke="white" stroke-width="2" stroke-linejoin="round"/></svg>'),
            iconSize: [24, 40],
            iconAnchor: [12, 20],
            popupAnchor: [0, -20]
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

        // Add initial vehicle marker with rotation capability
        vehicleMarker = L.marker(vehiclePosition, { 
            icon: vehicleIcon,
            rotationAngle: 0,
            rotationOrigin: 'center'
        }).addTo(map)
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
            
            if (data.vehiclePosition && vehicleMarker) {
                // Update vehicle marker position
                vehicleMarker.setLatLng(data.vehiclePosition);
                
                // Update popup content with new speed
                const speed = data.speed ? Math.round(data.speed) : 0;
                vehicleMarker.setPopupContent('<b>Vehicle Position</b><br>Speed: ' + speed + ' km/h');
            }
            
            if (data.polyline && routePolyline) {
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
            try {
                const data = JSON.parse(event.data);
                if (data.type === 'UPDATE_MAP') {
                    updateMapElements(data);
                }
            } catch (error) {
                // Silently handle message parsing errors
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
        
        // Send initialization status to React Native
        setTimeout(() => {
            if (typeof window.ReactNativeWebView !== 'undefined') {
                window.ReactNativeWebView.postMessage(JSON.stringify({
                    type: 'debug',
                    message: 'Map initialization complete. Variables available: map=' + (typeof map !== 'undefined' ? 'defined' : 'undefined') + 
                             ', vehicleMarker=' + (typeof vehicleMarker !== 'undefined' ? 'defined' : 'undefined') + 
                             ', routePolyline=' + (typeof routePolyline !== 'undefined' ? 'defined' : 'undefined') +
                             ', Leaflet=' + (typeof L !== 'undefined' ? 'defined' : 'undefined')
                }));
            }
        }, 1000);
        
    </script>
</body>
</html>
    `;
  }, [activeTrip, theme]);

  const mapHTML = getMapHTML();

  return (
    <View style={styles.mapContainer}>
      <WebView
        key={`webview-${activeTrip?.id || 'default'}`}
        ref={webViewRef || localWebViewRef}
        style={styles.map}
        source={{
          html: mapHTML,
        }}
        onLoad={onWebViewLoad}
        onLoadEnd={() => {
          if (!isWebViewLoaded) {
            onWebViewLoadEnd();
          }
        }}
        onError={onWebViewError}
        onMessage={onWebViewMessage}
        javaScriptEnabled={true}
        domStorageEnabled={true}
        startInLoadingState={true}
        scalesPageToFit={true}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  mapContainer: {
    flex: 1,
  },
  map: {
    flex: 1,
  },
});

export default TripMap;
