import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, useColorScheme } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { ArrowLeft } from 'lucide-react-native';
import { WebView } from 'react-native-webview';

interface Location {
  coordinates: [number, number];
  type: string;
}

interface TripStop {
  id: string | null;
  location: Location;
  address: string | null;
  name: string;
  arrival_time: string | null;
  departure_time: string | null;
  stop_duration: number | null;
  order: number;
}

interface RouteInfo {
  bounds: {
    southWest: { lat: number; lng: number };
    northEast: { lat: number; lng: number };
  };
  coordinates: Array<[number, number]>;
}

interface ApiTrip {
  id?: string;
  name?: string;
  description?: string;
  origin?: TripStop;
  destination?: TripStop;
  driver_assignment?: string;
  estimated_distance?: number;
  estimated_duration?: number;
  estimated_end_time?: string | null;
  actual_start_time?: string | null;
  actual_end_time?: string | null;
  priority?: string;
  route_info?: RouteInfo;
  created_at?: string;
  created_by?: string;
  constraints?: any[];
  custom_fields?: any;
  // Fallback properties for backward compatibility
  pickup?: string;
  pickupShort?: string;
  destinationShort?: string;
  startTime?: string;
  endTime?: string;
  startDate?: string;
  endDate?: string;
  distance?: string;
  status?: string;
  canStart?: boolean;
  rawStartTime?: Date | null;
}

interface TripDetailsScreenProps {
  route: {
    params: {
      trip: ApiTrip;
    };
  };
  navigation: {
    goBack: () => void;
  };
}

const TripDetailsScreen: React.FC<TripDetailsScreenProps> = ({ route, navigation }) => {
  const { trip: rawTrip } = route.params;

  // Handle serialized dates by converting them back to Date objects if needed
  const trip = React.useMemo(
    () => ({
      ...rawTrip,
      rawStartTime:
        rawTrip.rawStartTime && typeof rawTrip.rawStartTime === 'string'
          ? new Date(rawTrip.rawStartTime)
          : rawTrip.rawStartTime,
      rawEndTime:
        (rawTrip as any).rawEndTime && typeof (rawTrip as any).rawEndTime === 'string'
          ? new Date((rawTrip as any).rawEndTime)
          : (rawTrip as any).rawEndTime,
    }),
    [rawTrip]
  );

  // Debug trip data to understand what distance fields are available
  console.log('DEBUG - Full trip object:', JSON.stringify(trip, null, 2));
  console.log('DEBUG - trip.estimated_distance:', trip.estimated_distance);
  console.log('DEBUG - trip.distance:', (trip as any).distance);

  const isDarkMode = useColorScheme() === 'dark';

  const theme = {
    background: isDarkMode ? '#0f0f23' : '#f8fafc',
    cardBackground: isDarkMode ? '#1a1a2e' : '#ffffff',
    headerGradient: isDarkMode ? ['#1a1a2e', '#16213e'] : ['#ffffff', '#f1f5f9'],
    text: isDarkMode ? '#f1f5f9' : '#1e293b',
    textSecondary: isDarkMode ? '#94a3b8' : '#64748b',
    border: isDarkMode ? '#334155' : '#e2e8f0',
    accent: '#6366f1',
    accentLight: '#818cf8',
    success: '#10b981',
    warning: '#f59e0b',
    shadow: isDarkMode ? '#000000' : '#64748b',
  };

  // Extract coordinates from API data with fallbacks
  const pickup = React.useMemo(() => {
    console.log('DEBUG - Full trip.origin:', JSON.stringify(trip.origin, null, 2));

    // Check if we have new API format with origin.location.coordinates
    if (
      trip.origin &&
      trip.origin.location &&
      trip.origin.location.coordinates &&
      Array.isArray(trip.origin.location.coordinates) &&
      trip.origin.location.coordinates.length >= 2
    ) {
      console.log('SUCCESS - Found origin coordinates:', trip.origin.location.coordinates);
      return {
        latitude: trip.origin.location.coordinates[1], // API uses [lng, lat] format
        longitude: trip.origin.location.coordinates[0],
      };
    }

    // Try alternative coordinate formats
    if (trip.origin && trip.origin.location) {
      const loc = trip.origin.location as any; // Allow dynamic property access
      // Check for direct lat/lng properties
      if (loc.lat !== undefined && loc.lng !== undefined) {
        console.log('SUCCESS - Found origin lat/lng properties:', { lat: loc.lat, lng: loc.lng });
        return {
          latitude: loc.lat,
          longitude: loc.lng,
        };
      }
      // Check for latitude/longitude properties
      if (loc.latitude !== undefined && loc.longitude !== undefined) {
        console.log('SUCCESS - Found origin latitude/longitude properties:', {
          latitude: loc.latitude,
          longitude: loc.longitude,
        });
        return {
          latitude: loc.latitude,
          longitude: loc.longitude,
        };
      }
    }

    // Fallback to default coordinates (Johannesburg area)
    console.warn('Using fallback pickup coordinates - API data structure may have changed');
    console.log('DEBUG - trip.origin exists:', !!trip.origin);
    console.log('DEBUG - trip.origin.location exists:', !!(trip.origin && trip.origin.location));
    console.log('DEBUG - trip.origin.location full object:', trip.origin?.location);
    return { latitude: -26.2041, longitude: 28.0473 };
  }, [trip]);

  const destination = React.useMemo(() => {
    console.log('DEBUG - Full trip object keys:', Object.keys(trip));
    console.log('DEBUG - Full trip.destination:', JSON.stringify(trip.destination, null, 2));
    console.log('DEBUG - trip.destination type:', typeof trip.destination);

    // Check if we have new API format with destination.location.coordinates
    if (
      trip.destination &&
      trip.destination.location &&
      trip.destination.location.coordinates &&
      Array.isArray(trip.destination.location.coordinates) &&
      trip.destination.location.coordinates.length >= 2
    ) {
      console.log(
        'SUCCESS - Found destination coordinates:',
        trip.destination.location.coordinates
      );
      return {
        latitude: trip.destination.location.coordinates[1], // API uses [lng, lat] format
        longitude: trip.destination.location.coordinates[0],
      };
    }

    // Try alternative coordinate formats
    if (trip.destination && trip.destination.location) {
      const loc = trip.destination.location as any; // Allow dynamic property access
      // Check for direct lat/lng properties
      if (loc.lat !== undefined && loc.lng !== undefined) {
        console.log('SUCCESS - Found destination lat/lng properties:', {
          lat: loc.lat,
          lng: loc.lng,
        });
        return {
          latitude: loc.lat,
          longitude: loc.lng,
        };
      }
      // Check for latitude/longitude properties
      if (loc.latitude !== undefined && loc.longitude !== undefined) {
        console.log('SUCCESS - Found destination latitude/longitude properties:', {
          latitude: loc.latitude,
          longitude: loc.longitude,
        });
        return {
          latitude: loc.latitude,
          longitude: loc.longitude,
        };
      }
    }

    // Fallback to default coordinates (Pretoria area)
    console.warn('Using fallback destination coordinates - API data structure may have changed');
    console.log('DEBUG - trip.destination exists:', !!trip.destination);
    console.log(
      'DEBUG - trip.destination.location exists:',
      !!(trip.destination && trip.destination.location)
    );
    console.log('DEBUG - trip.destination.location full object:', trip.destination?.location);
    return { latitude: -25.7461, longitude: 28.1881 };
  }, [trip]);

  // Convert API route coordinates to our format with error handling
  const routeLine = React.useMemo(() => {
    try {
      if (
        trip.route_info &&
        trip.route_info.coordinates &&
        Array.isArray(trip.route_info.coordinates) &&
        trip.route_info.coordinates.length > 0
      ) {
        console.log('Processing route coordinates:', trip.route_info.coordinates.length, 'points');
        // Sample the first few coordinates to see the format
        const sampleCoords = trip.route_info.coordinates.slice(0, 3);
        console.log('Sample route coordinates:', sampleCoords);

        return trip.route_info.coordinates
          .map((coord, index) => {
            if (!Array.isArray(coord) || coord.length < 2) {
              console.warn(`Invalid coordinate at index ${index}:`, coord);
              return null;
            }
            // Check if coordinates are in valid latitude range (-90 to 90)
            // If first coordinate is in longitude range (-180 to 180) and second is in latitude range, swap them
            const firstIsLat = coord[0] >= -90 && coord[0] <= 90;
            const secondIsLat = coord[1] >= -90 && coord[1] <= 90;
            const firstIsLng = coord[0] >= -180 && coord[0] <= 180;

            if (!firstIsLat && secondIsLat && firstIsLng) {
              // Format is [lng, lat] - need to swap
              return {
                latitude: coord[1],
                longitude: coord[0],
              };
            } else {
              // Format is [lat, lng] or default assumption
              return {
                latitude: coord[0],
                longitude: coord[1],
              };
            }
          })
          .filter(coord => coord !== null); // Remove invalid coordinates
      }
    } catch (error) {
      console.warn('Error processing route coordinates:', error);
    }
    // Fallback to simple line between start and end
    console.log('Using fallback route: direct line between pickup and destination');
    return [pickup, destination];
  }, [trip.route_info, pickup, destination]);

  // Calculate map region based on route bounds or coordinates with error handling
  const mapRegion = React.useMemo(() => {
    try {
      if (
        trip.route_info &&
        trip.route_info.bounds &&
        trip.route_info.bounds.southWest &&
        trip.route_info.bounds.northEast
      ) {
        const bounds = trip.route_info.bounds;
        const centerLat = (bounds.southWest.lat + bounds.northEast.lat) / 2;
        const centerLng = (bounds.southWest.lng + bounds.northEast.lng) / 2;
        // Use smaller padding for tighter zoom
        const deltaLat = Math.abs(bounds.northEast.lat - bounds.southWest.lat) * 1.1;
        const deltaLng = Math.abs(bounds.northEast.lng - bounds.southWest.lng) * 1.1;

        console.log('Using API bounds for map region:', {
          centerLat,
          centerLng,
          deltaLat,
          deltaLng,
        });

        return {
          latitude: centerLat,
          longitude: centerLng,
          latitudeDelta: Math.max(deltaLat, 0.01), // Less aggressive minimum zoom
          longitudeDelta: Math.max(deltaLng, 0.01),
        };
      }
    } catch (error) {
      console.warn('Error calculating map region from bounds:', error);
    }

    // Fallback: calculate bounds from route coordinates if available
    if (routeLine.length > 2) {
      const lats = routeLine.map(coord => coord.latitude);
      const lngs = routeLine.map(coord => coord.longitude);
      const minLat = Math.min(...lats);
      const maxLat = Math.max(...lats);
      const minLng = Math.min(...lngs);
      const maxLng = Math.max(...lngs);

      const centerLat = (minLat + maxLat) / 2;
      const centerLng = (minLng + maxLng) / 2;
      const deltaLat = Math.abs(maxLat - minLat) * 1.2;
      const deltaLng = Math.abs(maxLng - minLng) * 1.2;

      console.log('Using route coordinates for map region:', {
        centerLat,
        centerLng,
        deltaLat,
        deltaLng,
      });

      return {
        latitude: centerLat,
        longitude: centerLng,
        latitudeDelta: Math.max(deltaLat, 0.01), // Less aggressive minimum zoom
        longitudeDelta: Math.max(deltaLng, 0.01),
      };
    }

    // Final fallback: center between pickup and destination with appropriate zoom
    const centerLat = (pickup.latitude + destination.latitude) / 2;
    const centerLng = (pickup.longitude + destination.longitude) / 2;
    const deltaLat = Math.abs(destination.latitude - pickup.latitude) * 1.3;
    const deltaLng = Math.abs(destination.longitude - pickup.longitude) * 1.3;

    // Ensure minimum zoom level for very close points
    const minDelta = 0.02; // About 2km zoom level for better visibility
    const finalDeltaLat = Math.max(deltaLat, minDelta);
    const finalDeltaLng = Math.max(deltaLng, minDelta);

    console.log('Using fallback coordinates for map region:', {
      centerLat,
      centerLng,
      deltaLat: finalDeltaLat,
      deltaLng: finalDeltaLng,
    });

    return {
      latitude: centerLat,
      longitude: centerLng,
      latitudeDelta: finalDeltaLat,
      longitudeDelta: finalDeltaLng,
    };
  }, [trip.route_info, pickup, destination, routeLine]);

  // Debug logging for coordinate setup
  React.useEffect(() => {
    console.log('COMPONENT RENDERED - COORDINATE DEBUG:');
    console.log('Using Leaflet WebView for mapping');
    console.log('Pickup coords:', pickup);
    console.log('Destination coords:', destination);
    console.log('Map region:', mapRegion);
    console.log('Route line coords:', routeLine);
    console.log('Route line length:', routeLine.length);
  }, [pickup, destination, mapRegion, routeLine]);

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
            {trip.name || 'Trip Details'}
          </Text>
          <Text style={[styles.headerDistance, { color: theme.success }]}>
            {(() => {
              // Try different distance field possibilities
              const tripAny = trip as any;

              // Check for route_info.distance first (this is in meters)
              if (trip.route_info?.distance && typeof trip.route_info.distance === 'number') {
                return Math.round(trip.route_info.distance / 1000) + ' km';
              }

              // Check for estimated_distance (this is already in km)
              if (trip.estimated_distance && typeof trip.estimated_distance === 'number') {
                return Math.round(trip.estimated_distance) + ' km';
              }

              // Check for distance field (could be string or number)
              if (tripAny.distance) {
                if (typeof tripAny.distance === 'string') {
                  // If it's already formatted (e.g., "5.2 km"), return as is
                  if (tripAny.distance.includes('km') || tripAny.distance.includes('mi')) {
                    return tripAny.distance;
                  }
                  // If it's a string number, convert it
                  const numDistance = parseFloat(tripAny.distance);
                  if (!isNaN(numDistance)) {
                    return Math.round(numDistance) + ' km';
                  }
                } else if (typeof tripAny.distance === 'number') {
                  return Math.round(tripAny.distance) + ' km';
                }
              }

              // Check for other possible distance fields
              if (tripAny.total_distance) {
                const dist =
                  typeof tripAny.total_distance === 'number'
                    ? tripAny.total_distance
                    : parseFloat(tripAny.total_distance);
                if (!isNaN(dist)) {
                  return Math.round(dist) + ' km';
                }
              }

              return 'Distance N/A';
            })()}
          </Text>
        </View>
        <View style={styles.headerRight} />
      </View>

      {/* Leaflet Map Container */}
      <View style={styles.mapContainer}>
        <WebView
          style={styles.map}
          source={{
            html: `
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trip Route Map</title>
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
        // Initialize the map with better zoom constraints and rotation
        const map = L.map('map', {
            center: [${mapRegion.latitude}, ${mapRegion.longitude}],
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
        
        // Define coordinates
        const pickup = [${pickup.latitude}, ${pickup.longitude}];
        const destination = [${destination.latitude}, ${destination.longitude}];
        const routeCoordinates = [
          ${routeLine.map(coord => `[${coord.latitude}, ${coord.longitude}]`).join(',\n          ')}
        ];
        
        // Get waypoints data if available
        const waypoints = ${JSON.stringify(
          trip.waypoints?.map((waypoint: any) => ({
            id: waypoint.id,
            coordinates: waypoint.location?.coordinates
              ? [waypoint.location.coordinates[1], waypoint.location.coordinates[0]]
              : null,
            name: waypoint.name || `Waypoint ${waypoint.order || ''}`,
            order: waypoint.order || 0,
          })) || []
        )};
        
        // Get location names and truncate at first comma
        const pickupFullName = "${
          trip.origin && trip.origin.name
            ? trip.origin.name.replace(/"/g, '\\"')
            : (
                (trip as any).pickupDisplay ||
                (trip as any).pickupShort ||
                'Pickup Location'
              ).replace(/"/g, '\\"')
        }";
        const pickupName = truncateAtComma(pickupFullName);
        
        const destinationFullName = "${
          trip.destination && typeof trip.destination === 'object' && trip.destination.name
            ? trip.destination.name.replace(/"/g, '\\"')
            : (
                (trip as any).destinationDisplay ||
                (trip as any).destinationShort ||
                'Destination'
              ).replace(/"/g, '\\"')
        }";
        const destinationName = truncateAtComma(destinationFullName);
        
        // Add markers
        const startMarker = L.marker(pickup).addTo(map)
            .bindPopup('<b>From:</b><br>' + pickupName);
        
        const endMarker = L.marker(destination).addTo(map)
            .bindPopup('<b>To:</b><br>' + destinationName);
        
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
        
        const waypointIcon = L.icon({
            iconUrl: 'data:image/svg+xml;base64,' + btoa('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#f59e0b"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg>'),
            iconSize: [25, 25],
            iconAnchor: [12, 25],
            popupAnchor: [0, -25]
        });
        
        // Update markers with custom icons
        startMarker.setIcon(blueIcon);
        endMarker.setIcon(greenIcon);
        
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
          trip.priority ? trip.priority.charAt(0).toUpperCase() + trip.priority.slice(1) : 'Normal'
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

        // Add route polyline (blue thick line)
        if (routeCoordinates.length > 0) {
            const polyline = L.polyline(routeCoordinates, {
                color: '#007AFF',
                weight: 6,
                opacity: 0.8
            }).addTo(map);
            
            // Fit map to show entire route with tighter bounds including waypoints
            const allMarkers = [startMarker, endMarker, ...waypointMarkers];
            const group = new L.featureGroup([...allMarkers, polyline]);
            const bounds = group.getBounds();
            
            // Use adequate padding to ensure both markers are clearly visible
            map.fitBounds(bounds, {
                padding: [80, 80] // Generous padding to ensure both locations are visible
                // Removed maxZoom to allow automatic zoom calculation
            });
        } else {
            // If no route, fit to markers with appropriate zoom including waypoints
            const allMarkers = [startMarker, endMarker, ...waypointMarkers];
            const group = new L.featureGroup(allMarkers);
            const bounds = group.getBounds();
            
            // Calculate distance between points to determine appropriate zoom
            const distance = pickup[0] !== undefined && destination[0] !== undefined ? 
                L.latLng(pickup).distanceTo(L.latLng(destination)) : 0;
            
            // Always use generous padding to ensure both markers are visible
            map.fitBounds(bounds, {
                padding: [100, 100] // Large padding to guarantee both locations are visible
                // Let Leaflet automatically calculate the best zoom level
            });
        }
        
        // Add a short delay to ensure all elements are rendered before final zoom adjustment
        setTimeout(() => {
            // Force refresh of map size and re-fit bounds for better display
            map.invalidateSize();
            
            // Re-fit to ensure optimal zoom after map is fully loaded including waypoints
            if (routeCoordinates.length > 0) {
                const allElements = [startMarker, endMarker, ...waypointMarkers];
                if (map.hasLayer(L.polyline(routeCoordinates))) {
                    allElements.push(L.polyline(routeCoordinates));
                }
                const group = new L.featureGroup(allElements);
                map.fitBounds(group.getBounds(), {
                    padding: [80, 80] // Good padding in delayed fit
                    // Let Leaflet determine the best zoom automatically
                });
            }
        }, 500);
        
        console.log('Leaflet map initialized successfully');
        console.log('Pickup:', pickup);
        console.log('Destination:', destination);
        console.log('Route points:', routeCoordinates.length);
        console.log('Map bounds fitted with automatic zoom');
    </script>
</body>
</html>
            `,
          }}
          onLoad={() => console.log('Leaflet map loaded successfully')}
          onError={error => console.error('WebView error:', error)}
          javaScriptEnabled={true}
          domStorageEnabled={true}
          startInLoadingState={true}
          scalesPageToFit={true}
        />
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
            <Text style={[styles.timeLabel, { color: theme.textSecondary }]}>Start:</Text>
            <Text style={[styles.timeValue, { color: theme.text }]}>
              {trip.created_at
                ? (() => {
                    const date = new Date(trip.created_at);
                    const time = date.toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    });
                    const dateStr = date.toLocaleDateString('en-GB'); // dd/mm/yyyy format
                    return `${time} ${dateStr}`;
                  })()
                : '09:00 01/01/2024'}
            </Text>
          </View>
          <View style={styles.timeRow}>
            <Text style={[styles.timeLabel, { color: theme.textSecondary }]}>End:</Text>
            <Text style={[styles.timeValue, { color: theme.text }]}>
              {trip.estimated_end_time
                ? (() => {
                    const date = new Date(trip.estimated_end_time);
                    const time = date.toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    });
                    const dateStr = date.toLocaleDateString('en-GB'); // dd/mm/yyyy format
                    return `${time} ${dateStr}`;
                  })()
                : '17:00 01/01/2024'}
            </Text>
          </View>
        </View>
        <TouchableOpacity
          style={[styles.closeButton, { borderColor: theme.border }]}
          onPress={() => navigation.goBack()}
        >
          <Text style={[styles.closeButtonText, { color: theme.text }]}>×</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
};

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
  headerSubtitle: {
    fontSize: 12,
    fontWeight: '500',
    marginTop: 2,
  },
  headerDistance: {
    fontSize: 18,
    fontWeight: '700',
    marginTop: 2,
  },
  headerRight: {
    width: 40,
  },

  // Enhanced Trip Info Card Styles
  tripInfoCard: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    padding: 20,
    borderWidth: 1,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.12,
    shadowRadius: 8,
    elevation: 6,
  },

  // Simplified Trip Schedule Card Styles
  tripScheduleCard: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderWidth: 1,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.12,
    shadowRadius: 8,
    elevation: 6,
  },
  scheduleInfo: {
    flex: 1,
    paddingRight: 16,
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
  closeButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    borderWidth: 1,
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: 16,
    backgroundColor: 'transparent',
  },
  closeButtonText: {
    fontSize: 24,
    fontWeight: 'bold',
    lineHeight: 24,
  },
  tripInfoMain: {
    flex: 1,
  },
  tripName: {
    fontSize: 20,
    fontWeight: '700',
    marginBottom: 12,
    letterSpacing: 0.3,
  },
  tripMetrics: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  metricItem: {
    alignItems: 'center',
    paddingHorizontal: 8,
  },
  metricDivider: {
    width: 1,
    height: 24,
    backgroundColor: '#e2e8f0',
    marginHorizontal: 12,
  },
  metricLabel: {
    fontSize: 11,
    fontWeight: '500',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  metricValue: {
    fontSize: 16,
    fontWeight: '700',
    marginTop: 2,
  },
  statusBadge: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1,
  },
  statusText: {
    fontSize: 13,
    fontWeight: '600',
    letterSpacing: 0.3,
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
  },
  map: {
    flex: 1,
  },

  // Enhanced Details Styles
  detailsContainer: {
    flex: 1,
    margin: 20,
    marginTop: 0,
    padding: 20,
    borderRadius: 16,
    borderWidth: 1,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.12,
    shadowRadius: 8,
    elevation: 6,
  },
  detailsHeader: {
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 6,
    letterSpacing: 0.3,
  },
  detailSubtext: {
    fontSize: 13,
    marginBottom: 20,
    lineHeight: 18,
  },
  routeInfo: {
    flex: 1,
  },
  routePoint: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderRadius: 12,
    marginVertical: 6,
  },
  routeIcon: {
    width: 32,
    height: 32,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
  },
  routeText: {
    flex: 1,
    marginLeft: 12,
  },
  routeLabel: {
    fontSize: 12,
    fontWeight: '500',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 2,
  },
  routeValue: {
    fontSize: 14,
    fontWeight: '600',
    lineHeight: 20,
  },
  routeConnector: {
    alignItems: 'center',
    paddingVertical: 4,
  },
  routeLine: {
    width: 2,
    height: 20,
    borderRadius: 1,
  },
  routeCoords: {
    fontSize: 11,
    fontWeight: '400',
    marginTop: 2,
    fontFamily: 'monospace',
  },
  routeDistance: {
    fontSize: 11,
    fontWeight: '500',
    textAlign: 'center',
    marginTop: 4,
  },

  // Trip Metadata Styles
  tripMetadata: {
    marginBottom: 20,
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#e2e8f0',
  },
  metadataRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  metadataText: {
    flex: 1,
    marginLeft: 12,
  },
  metadataLabel: {
    fontSize: 11,
    fontWeight: '500',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  metadataValue: {
    fontSize: 14,
    fontWeight: '600',
    marginTop: 2,
    lineHeight: 18,
  },
  routeSectionHeader: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 6,
    letterSpacing: 0.2,
  },

  // Legacy styles (kept for compatibility)
  detailRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 8,
  },
  detailLabel: {
    fontSize: 14,
    fontWeight: '500',
    marginBottom: 16,
    textAlign: 'center',
  },
  detailValue: {
    fontSize: 16,
    fontWeight: '600',
  },
  detailMarginLeft: {
    marginLeft: 8,
  },
});

export default TripDetailsScreen;
