import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, StyleSheet, Alert, TouchableOpacity, useColorScheme } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { ArrowLeft, Navigation, Square } from 'lucide-react-native';
import { WebView } from 'react-native-webview';
import {
  getDriverActiveTrips,
  finishTrip,
  getLocation,
  getVehiclePolyline,
  TripFinishedStatus,
  getDriverEMPID,
  getCurrentUserId,
} from '../utils/api';

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

interface ActiveTrip {
  id?: string;
  _id?: string; // MongoDB-style ID
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
  status?: string;
  scheduled_start_time?: string;
  scheduled_end_time?: string;
  vehicle_id?: string;
  vehicleId?: string;
}

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

const ActiveTripScreen: React.FC<ActiveTripScreenProps> = ({ navigation }) => {
  const [activeTrip, setActiveTrip] = useState<ActiveTrip | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [endingTrip, setEndingTrip] = useState(false);
  const [canEndTrip, setCanEndTrip] = useState(false);
  const [statusCheckInterval, setStatusCheckInterval] = useState<ReturnType<
    typeof setInterval
  > | null>(null);
  const [vehicleLocation, setVehicleLocation] = useState<VehicleLocation | null>(null);
  const [vehiclePolyline, setVehiclePolyline] = useState<Array<[number, number]> | null>(null);
  const [_mapCenter, setMapCenter] = useState<[number, number]>([37.7749, -122.4194]);

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

        if (response && response.data) {
          const locationData = response.data;

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

      if (location) {
        setVehicleLocation(location);
        setMapCenter(location.position);
      }

      if (polyline) {
        setVehiclePolyline(polyline);
      }
    } catch (err) {
      console.error('Error fetching vehicle data:', err);
    }
  }, [activeTrip, fetchVehicleLocation, fetchVehiclePolyline]);

  const checkTripFinished = useCallback(async (employeeId: string): Promise<boolean> => {
    try {
      const isFinished = await TripFinishedStatus(employeeId);
      setCanEndTrip(isFinished);
      return isFinished;
    } catch (err) {
      console.error('Error checking trip status:', err);
      return false;
    }
  }, []);

  const startStatusMonitoring = useCallback(
    async (employeeId: string) => {
      if (statusCheckInterval) return;

      const interval = setInterval(async () => {
        await checkTripFinished(employeeId);
      }, 30000); // Check every 30 seconds

      setStatusCheckInterval(interval);
      await checkTripFinished(employeeId); // Check immediately
    },
    [checkTripFinished, statusCheckInterval]
  );

  const stopStatusMonitoring = useCallback(() => {
    if (statusCheckInterval) {
      clearInterval(statusCheckInterval);
      setStatusCheckInterval(null);
    }
  }, [statusCheckInterval]);

  // Real API function for fetching active trip
  const fetchActiveTrip = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const driverId = await getCurrentUserId();
      if (!driverId) {
        throw new Error('No driver ID found');
      }

      const employeeIDResponse = await getDriverEMPID(driverId);
      if (!employeeIDResponse?.data) {
        throw new Error('No employee ID found');
      }

      console.log('Fetching active trip for EMP ID:', employeeIDResponse.data);

      const response = await getDriverActiveTrips(employeeIDResponse.data);
      console.log('Active trip response:', response);

      if (response && response.length > 0) {
        const trip = response[0]; // Get the first active trip
        setActiveTrip(trip);

        // Start monitoring trip finish status
        await startStatusMonitoring(employeeIDResponse.data);
      } else {
        setActiveTrip(null);
        stopStatusMonitoring();
      }
    } catch (err) {
      console.error('Error fetching active trip:', err);
      setError(err instanceof Error ? err.message : 'Failed to load active trip');
      setActiveTrip(null);
      stopStatusMonitoring();
    } finally {
      setLoading(false);
    }
  }, [startStatusMonitoring, stopStatusMonitoring]);

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
            setActiveTrip(null);
            setVehicleLocation(null);
            setVehiclePolyline(null);

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
  }, [activeTrip, navigation, stopStatusMonitoring]);

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
      setVehiclePolyline(null);
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

    const vehiclePos = vehicleLocation ? vehicleLocation.position : pickup;
    const polylineCoords = vehiclePolyline || [pickup, destination];

    return `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <style>
          body { margin: 0; padding: 0; }
          #map { height: 100vh; width: 100%; }
        </style>
      </head>
      <body>
        <div id="map"></div>
        <script>
          // Initialize map
          const map = L.map('map', {
            zoomControl: false,
            attributionControl: false
          });

          // Add tile layer
          L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

          // Define coordinates
          const pickup = [${pickup[0]}, ${pickup[1]}];
          const destination = [${destination[0]}, ${destination[1]}];
          const vehiclePosition = [${vehiclePos[0]}, ${vehiclePos[1]}];
          const routeCoordinates = ${JSON.stringify(polylineCoords)};

          // Create custom icons
          const originIcon = L.divIcon({
            html: '<div style="background-color: #6b7280; width: 20px; height: 20px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3);"></div>',
            className: 'custom-marker',
            iconSize: [20, 20],
            iconAnchor: [10, 10]
          });

          const destinationIcon = L.divIcon({
            html: '<div style="background-color: #10b981; width: 24px; height: 24px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3);"></div>',
            className: 'custom-marker',
            iconSize: [24, 24],
            iconAnchor: [12, 12]
          });

          const vehicleIcon = L.divIcon({
            html: '<div style="background-color: #3b82f6; width: 16px; height: 16px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.5); position: relative;"><div style="position: absolute; top: -2px; left: -2px; width: 20px; height: 20px; border: 2px solid #3b82f6; border-radius: 50%; animation: pulse 2s infinite;"></div></div>',
            className: 'vehicle-marker',
            iconSize: [16, 16],
            iconAnchor: [8, 8]
          });

          // Add markers
          const originMarker = L.marker(pickup, { icon: originIcon }).addTo(map);
          const destMarker = L.marker(destination, { icon: destinationIcon }).addTo(map);
          const vehicleMarker = L.marker(vehiclePosition, { icon: vehicleIcon }).addTo(map);

          // Add route polyline
          const polyline = L.polyline(routeCoordinates, {
            color: '#007AFF',
            weight: 4,
            opacity: 0.8
          }).addTo(map);

          // Fit map to show route
          const group = L.featureGroup([originMarker, destMarker, vehicleMarker, polyline]);
          map.fitBounds(group.getBounds(), { padding: [50, 50] });

          // Add pulse animation CSS
          const style = document.createElement('style');
          style.textContent = \`
            @keyframes pulse {
              0% { opacity: 1; transform: scale(1); }
              50% { opacity: 0.5; transform: scale(1.2); }
              100% { opacity: 1; transform: scale(1); }
            }
          \`;
          document.head.appendChild(style);
        </script>
      </body>
      </html>
    `;
  };

  if (loading) {
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
            onPress={fetchActiveTrip}
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
      {/* Header */}
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
        <View style={styles.headerTitleContainer}>
          <Text style={[styles.headerTitle, { color: theme.text }]}>
            {activeTrip.name || 'Active Trip'}
          </Text>
          <View style={styles.statusContainer}>
            <View style={[styles.statusDot, { backgroundColor: theme.success }]} />
            <Text style={[styles.statusText, { color: theme.success }]}>In Progress</Text>
            {vehicleLocation && (
              <View style={[styles.liveDot, { backgroundColor: theme.danger }]} />
            )}
          </View>
        </View>
      </View>

      {/* Map */}
      <View style={styles.mapContainer}>
        <WebView
          source={{ html: getMapHTML() }}
          style={styles.map}
          javaScriptEnabled={true}
          domStorageEnabled={true}
          startInLoadingState={true}
        />

        {/* End Trip Button */}
        {canEndTrip && (
          <View style={styles.endTripContainer}>
            <TouchableOpacity
              onPress={handleEndTrip}
              disabled={endingTrip}
              style={[
                styles.endTripButton,
                { backgroundColor: endingTrip ? theme.danger + '60' : theme.danger },
              ]}
            >
              {endingTrip ? (
                <View style={styles.endTripButtonContent}>
                  <View style={[styles.loadingSpinner, styles.loadingSpinnerWhite]} />
                  <Text style={styles.endTripButtonText}>Ending Trip...</Text>
                </View>
              ) : (
                <View style={styles.endTripButtonContent}>
                  <Square size={20} color="white" />
                  <Text style={styles.endTripButtonText}>End Trip</Text>
                </View>
              )}
            </TouchableOpacity>
          </View>
        )}
      </View>

      {/* Trip Info Card */}
      <View
        style={[
          styles.tripInfoCard,
          { backgroundColor: theme.cardBackground, borderTopColor: theme.border },
        ]}
      >
        <View style={styles.tripInfoRow}>
          <Text style={[styles.tripInfoLabel, { color: theme.textSecondary }]}>From:</Text>
          <Text style={[styles.tripInfoValue, { color: theme.text }]} numberOfLines={1}>
            {activeTrip.origin?.name || activeTrip.origin?.address || 'Unknown'}
          </Text>
        </View>
        <View style={styles.tripInfoRow}>
          <Text style={[styles.tripInfoLabel, { color: theme.textSecondary }]}>To:</Text>
          <Text style={[styles.tripInfoValue, { color: theme.text }]} numberOfLines={1}>
            {activeTrip.destination?.name || activeTrip.destination?.address || 'Unknown'}
          </Text>
        </View>
        {activeTrip.estimated_distance && (
          <View style={styles.tripInfoRow}>
            <Text style={[styles.tripInfoLabel, { color: theme.textSecondary }]}>Distance:</Text>
            <Text style={[styles.tripInfoValue, { color: theme.success }]}>
              {(activeTrip.estimated_distance / 1000).toFixed(1)} km
            </Text>
          </View>
        )}
        {vehicleLocation && (
          <View style={styles.tripInfoRow}>
            <Text style={[styles.tripInfoLabel, { color: theme.textSecondary }]}>Speed:</Text>
            <Text style={[styles.tripInfoValue, { color: theme.text }]}>
              {vehicleLocation.speed ? Math.round(vehicleLocation.speed) : 0} km/h
            </Text>
          </View>
        )}
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 16,
  },
  headerTitleContainer: {
    flex: 1,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 4,
  },
  statusContainer: {
    flexDirection: 'row',
    alignItems: 'center',
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
  mapContainer: {
    flex: 1,
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
  tripInfoCard: {
    padding: 20,
    borderTopWidth: 1,
  },
  tripInfoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  tripInfoLabel: {
    fontSize: 14,
    fontWeight: '500',
    flex: 1,
  },
  tripInfoValue: {
    fontSize: 14,
    fontWeight: '600',
    flex: 2,
    textAlign: 'right',
  },
});

export default ActiveTripScreen;
