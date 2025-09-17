import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Dimensions,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { MapPin, Clock, Play, CheckCircle, Eye, AlertCircle, RefreshCw } from 'lucide-react-native';
import {
  getUserData,
  setUserData as saveUserData,
  API_URL,
  getToken,
  updateTrip,
} from '../utils/api';
import { useActiveTripContext } from '../contexts/ActiveTripContext';
import { useTheme } from '../contexts/ThemeContext';
const { width } = Dimensions.get('window');

// Header refresh button component defined outside of the main component
interface HeaderRefreshButtonProps {
  onPress: () => void;
  isLoading: boolean;
  accentColor: string;
}

// Define a style object for the HeaderRefreshButton
const headerRefreshStyles = StyleSheet.create({
  button: {
    marginRight: 16,
  },
});

const HeaderRefreshButton = (props: HeaderRefreshButtonProps) => {
  const { onPress, isLoading, accentColor } = props;
  return (
    <TouchableOpacity onPress={onPress} style={headerRefreshStyles.button} disabled={isLoading}>
      <RefreshCw size={20} color={accentColor} opacity={isLoading ? 0.5 : 1} />
    </TouchableOpacity>
  );
};

// Driver Score Card Component
interface DriverScoreCardProps {
  theme: any;
  userData: any;
  performanceData: any;
  loading: boolean;
  onRefreshUserData: () => void;
}

const DriverScoreCard: React.FC<DriverScoreCardProps> = ({
  theme,
  userData,
  performanceData,
  loading,
  onRefreshUserData,
}) => {
  if (loading) {
    return (
      <View style={[styles.scoreCard, { backgroundColor: theme.cardBackground }]}>
        <ActivityIndicator size="large" color={theme.accent} />
        <Text style={[styles.loadingText, { color: theme.textSecondary }]}>
          Loading performance data...
        </Text>
      </View>
    );
  }

  const completedTrips = performanceData?.completed_trips || 0;
  const cancelledTrips = performanceData?.cancelled_trips || 0;
  const totalTrips = completedTrips + cancelledTrips;
  const completionRate = totalTrips > 0 ? Math.round((completedTrips / totalTrips) * 100) : 0;

  return (
    <View style={[styles.scoreCard, { backgroundColor: theme.cardBackground }]}>
      <View style={styles.scoreHeader}>
        <View style={styles.driverInfo}>
          <View style={[styles.avatar, { backgroundColor: theme.accent }]}>
            <Text style={styles.avatarText}>
              {userData?.full_name
                ? userData.full_name
                    .split(' ')
                    .map((n: string) => n[0])
                    .join('')
                    .toUpperCase()
                : 'DR'}
            </Text>
          </View>
          <View style={styles.driverDetails}>
            <Text style={[styles.driverName, { color: theme.text }]}>
              {userData?.full_name || 'Driver'}
            </Text>
            <Text style={[styles.driverRole, { color: theme.textSecondary }]}>
              ID: {userData?.employee_id || userData?.employeeId || 'Unknown'}
            </Text>
          </View>
          <TouchableOpacity
            onPress={onRefreshUserData}
            style={[styles.refreshButton, { backgroundColor: theme.accent + '20' }]}
          >
            <RefreshCw size={16} color={theme.accent} />
          </TouchableOpacity>
        </View>
      </View>

      <View style={styles.metricsContainer}>
        <View style={styles.metricItem}>
          <Text style={[styles.metricValue, { color: theme.accent }]}>{completedTrips}</Text>
          <Text style={[styles.metricLabel, { color: theme.textSecondary }]}>Completed Trips</Text>
        </View>
        <View style={styles.metricItem}>
          <Text style={[styles.metricValue, { color: theme.accent }]}>{completionRate}%</Text>
          <Text style={[styles.metricLabel, { color: theme.textSecondary }]}>Success Rate</Text>
        </View>
        <View style={styles.metricItem}>
          <Text style={[styles.metricValue, { color: theme.accent }]}>
            {performanceData?.avg_rating ? Number(performanceData.avg_rating).toFixed(1) : 'N/A'}
          </Text>
          <Text style={[styles.metricLabel, { color: theme.textSecondary }]}>Rating</Text>
        </View>
      </View>
    </View>
  );
};

// Upcoming Trips Component
interface UpcomingTripsProps {
  theme: any;
  onTripStarted?: (tripId: string) => void;
  userData: any;
  navigation?: any;
}

const UpcomingTrips: React.FC<UpcomingTripsProps> = ({
  theme,
  onTripStarted,
  userData,
  navigation,
}) => {
  const [trips, setTrips] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Use ActiveTripContext in the UpcomingTrips component
  const { checkForActiveTrip } = useActiveTripContext();

  useEffect(() => {
    const getEmployeeID = async (security_id: string) => {
      try {
        const token = await getToken();
        if (!token) return null;

        const response = await fetch(`${API_URL}/management/drivers/employee/${security_id}`, {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });

        if (response.ok) {
          const data = await response.json();
          console.log('Employee ID API response:', data);
          // Based on API response: {"status":"success","data":{"status":"success","data":"EMP139",...}}
          return { data: data.data?.data || data.data };
        }
      } catch (error) {
        console.error('Error fetching employee ID:', error);
      }
      return null;
    };

    const fetchUpcomingTrips = async (isInitialLoad = false) => {
      try {
        // Only show loading indicator on initial load to prevent flickering
        if (isInitialLoad) {
          setLoading(true);
        }

        const newTrips = await fetchUpcomingTripsSilent();

        // Compare and update only if data has changed
        if (newTrips && JSON.stringify(newTrips) !== JSON.stringify(trips)) {
          console.log('Upcoming trips data changed, updating UI');
          setTrips(newTrips);
        }

        if (isInitialLoad) {
          setLoading(false);
        }
      } catch (error) {
        console.error('Error fetching upcoming trips:', error);
        if (isInitialLoad) {
          setLoading(false);
        }
      }
    };

    const fetchUpcomingTripsSilent = async () => {
      try {
        const driverId = userData?.id;
        if (!driverId) {
          console.log('No driver ID found');
          return [];
        }

        const employeeID = await getEmployeeID(driverId);
        if (!employeeID) {
          console.log('No employee ID found');
          return [];
        }

        const token = await getToken();
        if (!token) {
          return [];
        }

        const response = await fetch(`${API_URL}/trips/trips/upcomming/${employeeID.data}`, {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });

        if (response.ok) {
          const data = await response.json();

          // Extract trips data from nested response structure
          let tripsData = [];
          if (Array.isArray(data?.data?.data)) {
            tripsData = data.data.data;
          } else if (Array.isArray(data?.data)) {
            tripsData = data.data;
          } else if (Array.isArray(data?.trips)) {
            tripsData = data.trips;
          }

          const formattedTrips = tripsData.map((trip: any) => {
            const startTime = trip.scheduled_start_time
              ? new Date(trip.scheduled_start_time)
              : null;
            const endTime = trip.scheduled_end_time ? new Date(trip.scheduled_end_time) : null;

            // Helper function to truncate location text at first comma
            const truncateLocation = (location: string) => {
              const commaIndex = location.indexOf(',');
              return commaIndex !== -1 ? location.substring(0, commaIndex) : location;
            };

            // Check timing for different button states
            const now = new Date();

            let buttonState = 'view'; // default state
            let buttonText = 'View';
            let buttonColor = '#3b82f6'; // blue

            if (startTime) {
              const timeDiffMs = now.getTime() - startTime.getTime();
              const timeDiffMinutes = timeDiffMs / (1000 * 60);

              if (timeDiffMinutes >= -60 && timeDiffMinutes <= 15) {
                // Can start normally: 1 hour before to 15 minutes after start time
                buttonState = 'start';
                buttonText = 'Start';
                buttonColor = '#10b981'; // green
              } else if (timeDiffMinutes > 15 && timeDiffMinutes <= 30) {
                // Start late: 15-30 minutes after start time
                buttonState = 'start_late';
                buttonText = 'Start Late';
                buttonColor = '#f59e0b'; // orange/yellow
              } else if (timeDiffMinutes > 30 && timeDiffMinutes <= 45) {
                // Back to view: 30-45 minutes after start time
                buttonState = 'view';
                buttonText = 'View';
                buttonColor = '#3b82f6'; // blue
              }
              // After 45 minutes, stays as 'view'
            }

            const canStart = buttonState === 'start' || buttonState === 'start_late';

            return {
              // Preserve all original API data
              ...trip,
              // Add formatted display properties
              id: trip.id || trip._id,
              name: trip.name || trip.trip_name || `Trip ${trip.id || 'Unknown'}`,
              pickupDisplay: trip.origin?.name || trip.origin?.address || 'Unknown Location',
              destinationDisplay:
                trip.destination?.name || trip.destination?.address || 'Unknown Location',
              pickupShort: truncateLocation(
                trip.origin?.name || trip.origin?.address || 'Unknown Location'
              ),
              destinationShort: truncateLocation(
                trip.destination?.name || trip.destination?.address || 'Unknown Location'
              ),
              startTime: startTime
                ? startTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                : 'TBD',
              endTime: endTime
                ? endTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                : 'TBD',
              startDate: startTime ? startTime.toLocaleDateString() : 'TBD',
              endDate: endTime ? endTime.toLocaleDateString() : 'TBD',
              distance: trip.route_info?.distance
                ? `${Math.round(trip.route_info.distance / 1000)} km` // Convert meters to km
                : trip.estimated_distance
                ? `${trip.estimated_distance} km`
                : 'N/A',
              status: trip.status || 'scheduled',
              canStart: canStart,
              buttonState: buttonState,
              buttonText: buttonText,
              buttonColor: buttonColor,
              startTimeISO: startTime ? startTime.toISOString() : null,
              rawStartTime: startTime, // Keep the Date object for calculations
            };
          });

          return formattedTrips;
        }

        return [];
      } catch (error) {
        console.error('Error fetching upcoming trips silently:', error);
        return [];
      }
    };

    // Initial fetch when userData is available
    if (userData?.id) {
      fetchUpcomingTrips(true); // Pass true for initial load

      // Set up interval to check for upcoming trips changes every 3 seconds
      const interval = setInterval(() => {
        if (userData?.id) {
          fetchUpcomingTrips(false); // Pass false for subsequent loads with change detection
        }
      }, 90000);

      // Cleanup interval on component unmount or when userData changes
      return () => {
        clearInterval(interval);
      };
    }
  }, [userData?.id, trips]);

  const handleStartTrip = async (tripId: string) => {
    Alert.alert('Start Trip', 'Are you ready to start this trip?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Start',
        onPress: async () => {
          try {
            console.log('Starting trip ID:', tripId);
            await updateTrip(tripId);
            console.log('Trip started successfully');

            // Trigger active trip check to update context and navigate
            await checkForActiveTrip();

            onTripStarted?.(tripId);
          } catch (error) {
            console.error('Error starting trip:', error);
            Alert.alert('Error', 'Failed to start trip. Please try again.');
          }
        },
      },
    ]);
  };

  const handleViewTrip = (trip: any) => {
    if (navigation) {
      navigation.navigate('TripDetails', { trip });
    } else {
      Alert.alert('Trip Details', 'Trip details will be available soon!', [
        { text: 'OK', style: 'default' },
      ]);
    }
  };

  return (
    <View style={[styles.sectionContainer, { backgroundColor: theme.cardBackground }]}>
      <View style={styles.sectionHeader}>
        <Text style={[styles.sectionTitle, { color: theme.text }]}>Upcoming Trips</Text>
        <MapPin size={20} color={theme.accent} />
      </View>

      {loading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="small" color={theme.accent} />
          <Text style={[styles.loadingText, { color: theme.textSecondary }]}>Loading trips...</Text>
        </View>
      ) : trips.length > 0 ? (
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.tripsScroll}>
          {trips.map((trip: any) => (
            <View
              key={trip.id}
              style={[
                styles.tripCard,
                { backgroundColor: theme.background, borderColor: theme.border },
              ]}
            >
              <View style={styles.tripHeader}>
                <Text style={[styles.tripName, { color: theme.text }]} numberOfLines={1}>
                  {trip.name}
                </Text>
                <View style={[styles.statusBadgeTrip, { backgroundColor: theme.accent + '20' }]}>
                  <Text style={[styles.statusBadgeText, { color: theme.accent }]}>
                    {trip.status.charAt(0).toUpperCase() + trip.status.slice(1)}
                  </Text>
                </View>
              </View>

              <View style={styles.routeContainer}>
                <View style={styles.locationItem}>
                  <View style={[styles.locationDot, styles.startDot]} />
                  <Text style={[styles.locationText, { color: theme.text }]} numberOfLines={1}>
                    {trip.pickupShort}
                  </Text>
                </View>
                <View style={[styles.routeLine, { backgroundColor: theme.border }]} />
                <View style={styles.locationItem}>
                  <View style={[styles.locationDot, styles.endDot]} />
                  <Text style={[styles.locationText, { color: theme.text }]} numberOfLines={1}>
                    {trip.destinationShort}
                  </Text>
                </View>
              </View>

              <View style={[styles.timeContainer, { backgroundColor: theme.cardBackground }]}>
                <View style={styles.timeSection}>
                  <Text style={[styles.timeLabel, { color: theme.textSecondary }]}>Start</Text>
                  <Text style={[styles.timeValue, { color: theme.text }]}>{trip.startTime}</Text>
                  <Text style={[styles.dateValue, { color: theme.textSecondary }]}>
                    {trip.startDate}
                  </Text>
                </View>
                <View style={[styles.timeDivider, { backgroundColor: theme.border }]} />
                <View style={styles.timeSection}>
                  <Text style={[styles.timeLabel, { color: theme.textSecondary }]}>End</Text>
                  <Text style={[styles.timeValue, { color: theme.text }]}>{trip.endTime}</Text>
                  <Text style={[styles.dateValue, { color: theme.textSecondary }]}>
                    {trip.endDate}
                  </Text>
                </View>
              </View>

              <View style={styles.tripFooter}>
                <View style={styles.distanceContainer}>
                  <MapPin size={14} color={theme.textSecondary} />
                  <Text style={[styles.distanceText, { color: theme.textSecondary }]}>
                    {trip.distance}
                  </Text>
                </View>
                {trip.canStart ? (
                  <TouchableOpacity
                    style={[styles.startButton, { backgroundColor: trip.buttonColor || '#10b981' }]}
                    onPress={() => handleStartTrip(trip.id)}
                  >
                    {trip.buttonState === 'start_late' ? (
                      <AlertCircle size={14} color="#ffffff" />
                    ) : (
                      <Play size={14} color="#ffffff" />
                    )}
                    <Text style={styles.startButtonText}>{trip.buttonText || 'Start'}</Text>
                  </TouchableOpacity>
                ) : (
                  <TouchableOpacity
                    style={[
                      styles.viewButton,
                      {
                        backgroundColor: trip.buttonColor || '#3b82f6',
                        borderColor: trip.buttonColor || '#3b82f6',
                      },
                    ]}
                    onPress={() => handleViewTrip(trip)}
                  >
                    <Eye size={14} color="#ffffff" />
                    <Text style={styles.viewButtonText}>{trip.buttonText || 'View'}</Text>
                  </TouchableOpacity>
                )}
              </View>
            </View>
          ))}
        </ScrollView>
      ) : (
        <Text style={[styles.emptyText, { color: theme.textSecondary }]}>No upcoming trips</Text>
      )}
    </View>
  );
};

// Recent Trips Component
interface RecentTripsProps {
  theme: any;
  userData: any;
  navigation?: any;
}

const RecentTrips: React.FC<RecentTripsProps> = ({ theme, userData, navigation }) => {
  const [recentTrips, setRecentTrips] = useState<any[]>([]);
  const [_loading, setLoading] = useState(false);

  useEffect(() => {
    const getEmployeeID = async (security_id: string) => {
      try {
        const token = await getToken();
        if (!token) return null;

        const response = await fetch(`${API_URL}/management/drivers/employee/${security_id}`, {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });

        if (response.ok) {
          const data = await response.json();
          console.log('Employee ID API response (RecentTrips):', data);
          // Based on API response: {"status":"success","data":{"status":"success","data":"EMP139",...}}
          return { data: data.data?.data || data.data };
        }
      } catch (error) {
        console.error('Error fetching employee ID:', error);
      }
      return null;
    };

    const fetchRecentTrips = async () => {
      try {
        setLoading(true);
        const driverId = userData?.id;

        if (!driverId) {
          console.log('No driver ID found');
          setRecentTrips([]);
          setLoading(false);
          return;
        }

        const employeeID = await getEmployeeID(driverId);
        if (!employeeID) {
          console.log('No employee ID found');
          setRecentTrips([]);
          setLoading(false);
          return;
        }

        const token = await getToken();
        if (!token) {
          setLoading(false);
          return;
        }

        const response = await fetch(`${API_URL}/trips/trips/recent/${employeeID.data}`, {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });

        if (response.ok) {
          const data = await response.json();
          console.log('Recent trips API response:', data);

          // Extract trips data from nested response structure (matching main app logic)
          let tripsData = [];
          if (Array.isArray(data?.data?.data)) {
            tripsData = data.data.data;
          } else if (Array.isArray(data?.data?.data?.data)) {
            tripsData = data.data.data.data;
          } else if (Array.isArray(data?.data)) {
            tripsData = data.data;
          } else if (Array.isArray(data?.trips)) {
            tripsData = data.trips;
          }

          console.log('Extracted recent trips data:', tripsData);

          const formattedTrips = tripsData.slice(0, 3).map((trip: any) => {
            // Helper function to truncate location text at first comma
            const truncateLocation = (location: string) => {
              const commaIndex = location.indexOf(',');
              return commaIndex !== -1 ? location.substring(0, commaIndex) : location;
            };

            const originText = trip.origin?.address || trip.origin?.name || 'Unknown';
            const destinationText =
              trip.destination?.address || trip.destination?.name || 'Unknown';

            const actualStartTime = trip.actual_start_time
              ? new Date(trip.actual_start_time)
              : null;
            const actualEndTime = trip.actual_end_time ? new Date(trip.actual_end_time) : null;

            // Priority color mapping
            const getPriorityColor = (priority: string) => {
              switch (priority?.toLowerCase()) {
                case 'high':
                  return '#ef4444'; // Red
                case 'medium':
                  return '#f59e0b'; // Orange
                case 'low':
                  return '#10b981'; // Green
                default:
                  return '#6b7280'; // Gray for normal/unknown
              }
            };

            const priority = trip.priority || 'normal';
            const priorityColor = getPriorityColor(priority);

            return {
              // Preserve all original API data
              ...trip,
              // Add formatted display properties
              id: trip.id || trip._id,
              name: trip.name || trip.trip_name || `Trip ${trip.id || 'Unknown'}`,
              route: `${originText} → ${destinationText}`,
              pickupShort: truncateLocation(originText),
              destinationShort: truncateLocation(destinationText),
              startTime: actualStartTime
                ? actualStartTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                : 'N/A',
              endTime: actualEndTime
                ? actualEndTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                : 'N/A',
              startDate: actualStartTime ? actualStartTime.toLocaleDateString() : 'N/A',
              endDate: actualEndTime ? actualEndTime.toLocaleDateString() : 'N/A',
              priority: trip.priority || 'normal',
              priorityDisplay:
                trip.priority?.charAt(0).toUpperCase() + trip.priority?.slice(1) || 'Normal',
              priorityColor: priorityColor,
              date: actualStartTime
                ? actualStartTime.toLocaleDateString([], {
                    weekday: 'short',
                    month: 'short',
                    day: 'numeric',
                  })
                : 'Recently',
              status: 'completed',
              distance: trip.estimated_distance
                ? `${Math.round(trip.estimated_distance)} km`
                : 'N/A',
            };
          });

          console.log('Formatted recent trips:', formattedTrips);
          setRecentTrips(formattedTrips);
        }
      } catch (error) {
        console.error('Error fetching recent trips:', error);
      } finally {
        setLoading(false);
      }
    };

    if (userData?.id) {
      fetchRecentTrips();
    }
  }, [userData?.id]);

  const handleViewTrip = (trip: any) => {
    if (navigation) {
      navigation.navigate('TripDetails', { trip });
    } else {
      Alert.alert('Trip Details', 'Trip details will be available soon!', [
        { text: 'OK', style: 'default' },
      ]);
    }
  };

  return (
    <View style={[styles.sectionContainer, { backgroundColor: theme.cardBackground }]}>
      <View style={styles.sectionHeader}>
        <Text style={[styles.sectionTitle, { color: theme.text }]}>Recent Trips</Text>
        <Clock size={20} color={theme.accent} />
      </View>

      {recentTrips.length > 0 ? (
        <View style={styles.recentTripsContainer}>
          {recentTrips.map((trip: any) => (
            <View
              key={trip.id}
              style={[
                styles.recentTripCard,
                { backgroundColor: theme.background, borderColor: theme.border },
              ]}
            >
              <View style={styles.tripHeader}>
                <Text style={[styles.tripName, { color: theme.text }]} numberOfLines={1}>
                  {trip.name || 'Recent Trip'}
                </Text>
                <View
                  style={[styles.statusBadgeTrip, { backgroundColor: trip.priorityColor + '20' }]}
                >
                  <Text style={[styles.statusBadgeText, { color: trip.priorityColor }]}>
                    {trip.priorityDisplay}
                  </Text>
                </View>
              </View>

              <View style={[styles.timeContainer, { backgroundColor: theme.cardBackground }]}>
                <View style={styles.timeSection}>
                  <Text style={[styles.timeLabel, { color: theme.textSecondary }]}>Started</Text>
                  <Text style={[styles.timeValue, { color: theme.text }]}>{trip.startTime}</Text>
                  <Text style={[styles.dateValue, { color: theme.textSecondary }]}>
                    {trip.startDate}
                  </Text>
                  <View style={styles.locationItem}>
                    <View style={[styles.locationDot, styles.startDot]} />
                    <Text style={[styles.locationText, { color: theme.text }]}>
                      {trip.pickupShort || trip.route.split(' → ')[0] || 'Unknown'}
                    </Text>
                  </View>
                </View>
                <View style={[styles.timeDivider, { backgroundColor: theme.border }]} />
                <View style={styles.timeSection}>
                  <Text style={[styles.timeLabel, { color: theme.textSecondary }]}>Completed</Text>
                  <Text style={[styles.timeValue, { color: theme.text }]}>{trip.endTime}</Text>
                  <Text style={[styles.dateValue, { color: theme.textSecondary }]}>
                    {trip.endDate}
                  </Text>
                  <View style={styles.locationItem}>
                    <View style={[styles.locationDot, styles.endDot]} />
                    <Text style={[styles.locationText, { color: theme.text }]}>
                      {trip.destinationShort || trip.route.split(' → ')[1] || 'Unknown'}
                    </Text>
                  </View>
                </View>
              </View>

              <View style={styles.tripFooter}>
                <View style={styles.distanceContainer}>
                  <MapPin size={14} color={theme.textSecondary} />
                  <Text style={[styles.distanceText, { color: theme.textSecondary }]}>
                    {trip.distance}
                  </Text>
                </View>
                <TouchableOpacity
                  style={[
                    styles.viewButton,
                    {
                      backgroundColor: '#3b82f6',
                      borderColor: '#3b82f6',
                    },
                  ]}
                  onPress={() => handleViewTrip(trip)}
                >
                  <Eye size={14} color="#ffffff" />
                  <Text style={styles.viewButtonText}>View</Text>
                </TouchableOpacity>
              </View>
            </View>
          ))}
        </View>
      ) : (
        <Text style={[styles.emptyText, { color: theme.textSecondary }]}>No recent trips</Text>
      )}
    </View>
  );
};

export default function DashboardScreen({ navigation }: { navigation?: any }) {
  const { theme } = useTheme();
  const [userData, setUserData] = useState<any>(null);
  const [performanceData, setPerformanceData] = useState<any>(null);
  const [loading, setLoading] = useState(true); // Only for initial load

  // Use the ActiveTripContext
  const {
    hasActiveTrip,
    activeTrip,
    checkForActiveTrip,
    clearActiveTrip,
    error: activeTripError,
  } = useActiveTripContext();

  const getEmployeeID = useCallback(async (security_id: string) => {
    try {
      const token = await getToken();
      if (!token) {
        console.log('No token available for employee ID fetch');
        return null;
      }

      console.log('Fetching employee ID for security_id:', security_id);
      const response = await fetch(`${API_URL}/management/drivers/employee/${security_id}`, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Employee ID API response (full):', JSON.stringify(data, null, 2));

        // Handle various response formats
        if (data.status === 'success' || data.success) {
          // Try different possible data structures - prioritize the exact structure from API response
          let employeeId = null;

          // Handle the exact structure from your API response: {data: {data: "EMP139"}}
          if (data.data && typeof data.data === 'object' && data.data.data) {
            employeeId = data.data.data;
            console.log('Employee ID found at data.data.data:', employeeId);
          } else if (data.data && typeof data.data === 'string') {
            employeeId = data.data;
            console.log('Employee ID found at data.data:', employeeId);
          } else if (data.employee_id) {
            employeeId = data.employee_id;
            console.log('Employee ID found at employee_id:', employeeId);
          } else if (data.employeeId) {
            employeeId = data.employeeId;
            console.log('Employee ID found at employeeId:', employeeId);
          }

          if (employeeId && employeeId.trim && employeeId.trim() !== '') {
            const cleanEmployeeId = typeof employeeId === 'string' ? employeeId.trim() : employeeId;
            console.log('Successfully retrieved employee ID:', cleanEmployeeId);
            return cleanEmployeeId;
          } else {
            console.log('Employee ID not found in successful response, full response:', data);
          }
        } else {
          console.log('API response indicates failure:', data.message || 'Unknown error');
        }
      } else {
        console.log('Employee ID API response not ok:', response.status, response.statusText);
      }
    } catch (error) {
      console.error('Error fetching employee ID:', error);
    }
    return null;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchUserData = useCallback(async () => {
    try {
      // First load data from storage
      const localUserData = await getUserData();
      if (localUserData) {
        console.log('Local userData:', localUserData);
        setUserData(localUserData);
      }

      // Also try to get fresh data from API
      const token = await getToken();
      if (token) {
        const response = await fetch(`${API_URL}/auth/me`, {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });

        if (response.ok) {
          const apiUserData = await response.json();
          console.log('API userData:', apiUserData);

          // Preserve existing employee ID if present
          if (localUserData?.employee_id) {
            apiUserData.employee_id = localUserData.employee_id;
          } else if (localUserData?.employeeId) {
            apiUserData.employee_id = localUserData.employeeId;
          }

          // If we have user ID, fetch the employee ID if not already present
          if (apiUserData?.id && !apiUserData.employee_id) {
            console.log('No employee ID found, fetching for user ID:', apiUserData.id);
            const employeeId = await getEmployeeID(apiUserData.id);
            if (employeeId) {
              console.log('Successfully fetched employee ID:', employeeId);
              console.log('Type of employeeId:', typeof employeeId);
              // Add employee_id to userData
              apiUserData.employee_id = employeeId;
              apiUserData.employeeId = employeeId; // Also set with alternate property name for compatibility

              // Save updated user data with employee ID
              await saveUserData(apiUserData);
              console.log('Saved user data with employee ID:', employeeId);
              console.log(
                'Full apiUserData after setting employee ID:',
                JSON.stringify(apiUserData, null, 2)
              );
            } else {
              console.log('Failed to fetch employee ID for user:', apiUserData.id);
            }
          } else if (apiUserData.employee_id) {
            console.log('Employee ID already present:', apiUserData.employee_id);
          } else {
            console.log(
              'No user ID available to fetch employee ID, apiUserData.id:',
              apiUserData?.id
            );
          }

          setUserData(apiUserData);
          console.log(
            'Final userData employee ID check:',
            'employee_id:',
            apiUserData.employee_id,
            'employeeId:',
            apiUserData.employeeId,
            'Display value:',
            apiUserData?.employee_id || apiUserData?.employeeId || 'Unknown'
          );
        }
      }
    } catch (error) {
      console.error('Error fetching user data:', error);
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchPerformanceData = useCallback(async () => {
    try {
      const token = await getToken();
      if (!token || !userData?.id) return;

      // Get the employee ID from userData first, if available
      let employeeId = userData.employee_id || userData.employeeId;

      // If not available, fetch it from the API
      if (!employeeId) {
        console.log('No employee ID in userData, fetching from API');
        employeeId = await getEmployeeID(userData.id);

        if (employeeId) {
          // Update userData with the employee ID
          const updatedUserData = {
            ...userData,
            employee_id: employeeId,
            employeeId: employeeId, // For compatibility
          };
          setUserData(updatedUserData);

          // Also persist this update
          await saveUserData(updatedUserData);
          console.log('Saved updated user data with employee ID:', employeeId);
        }
      }

      if (!employeeId) {
        console.log('No employee ID found after attempts');
        setPerformanceData(null);
        return;
      }

      console.log('Using employee ID for performance data fetch:', employeeId);

      // Fetch driver-specific analytics from management service
      const response = await fetch(
        `${API_URL}/management/analytics/driver-performance/${employeeId}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        console.log('Driver performance API response:', data);

        // Extract performance data from the response structure
        const rawPerformanceData = data.data || data;

        // Transform the data to match the expected format
        const transformedData = {
          completed_trips: rawPerformanceData?.performance?.trip_count || 0,
          cancelled_trips: 0, // This might need to be calculated differently
          total_distance: rawPerformanceData?.performance?.total_distance || 0,
          avg_rating: rawPerformanceData?.score?.overall_score || 0,
        };

        console.log('Transformed performance data:', transformedData);
        setPerformanceData(transformedData);
      } else {
        console.log('Failed to fetch performance data:', response.status, response.statusText);
        setPerformanceData(null);
      }
    } catch (error) {
      console.error('Error fetching performance data:', error);
      setPerformanceData(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Manual refresh function (shows loading indicators)
  const refreshDashboard = useCallback(async () => {
    setLoading(true);
    try {
      await fetchUserData();
      if (userData?.id) {
        await fetchPerformanceData();
      }
    } catch (error) {
      console.error('Error refreshing data:', error);
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Silent background refresh function with change detection
  const backgroundRefresh = useCallback(async () => {
    try {
      // Fetch new data without updating state
      const newUserData = await fetchUserDataSilent();
      const newPerformanceData = await fetchPerformanceDataSilent(newUserData);

      // Compare and update only if data has changed
      if (newUserData && JSON.stringify(newUserData) !== JSON.stringify(userData)) {
        console.log('User data changed, updating UI');
      }

      if (
        newPerformanceData &&
        JSON.stringify(newPerformanceData) !== JSON.stringify(performanceData)
      ) {
        console.log('Performance data changed, updating UI');
        setPerformanceData(newPerformanceData);
      }
    } catch (error) {
      console.error('Error in background refresh:', error);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userData, performanceData]);

  // Silent fetch functions that return data without updating state
  const fetchUserDataSilent = useCallback(async () => {
    try {
      // First load data from storage
      let localUserData = await getUserData();

      // Also try to get fresh data from API
      const token = await getToken();
      if (token) {
        const response = await fetch(`${API_URL}/auth/me`, {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });

        if (response.ok) {
          const apiUserData = await response.json();

          // Preserve existing employee ID if present
          if (localUserData?.employee_id) {
            apiUserData.employee_id = localUserData.employee_id;
          } else if (localUserData?.employeeId) {
            apiUserData.employee_id = localUserData.employeeId;
          }

          // If we have user ID, fetch the employee ID if not already present
          if (apiUserData?.id && !apiUserData.employee_id) {
            const employeeId = await getEmployeeID(apiUserData.id);
            if (employeeId) {
              apiUserData.employee_id = employeeId;
              apiUserData.employeeId = employeeId;
            }
          }

          return apiUserData;
        }
      }

      return localUserData;
    } catch (error) {
      console.error('Error fetching user data silently:', error);
      return null;
    }
  }, [getEmployeeID]);

  const fetchPerformanceDataSilent = useCallback(
    async (currentUserData = null) => {
      try {
        const userDataToUse = currentUserData || userData;
        const token = await getToken();
        if (!token || !userDataToUse?.id) return null;

        // Get the employee ID from userData first, if available
        let employeeId = userDataToUse.employee_id || userDataToUse.employeeId;

        // If not available, fetch it from the API
        if (!employeeId) {
          employeeId = await getEmployeeID(userDataToUse.id);
        }

        if (!employeeId) {
          return null;
        }

        // Fetch driver-specific analytics from management service
        const response = await fetch(
          `${API_URL}/management/analytics/driver-performance/${employeeId}`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
          }
        );

        if (response.ok) {
          const data = await response.json();
          return data;
        }

        return null;
      } catch (error) {
        console.error('Error fetching performance data silently:', error);
        return null;
      }
    },
    [userData, getEmployeeID]
  );

  // Create a memoized function to render the refresh button
  const renderRefreshButton = useCallback(() => {
    return (
      <HeaderRefreshButton
        onPress={refreshDashboard}
        isLoading={loading}
        accentColor={theme.accent}
      />
    );
  }, [refreshDashboard, loading, theme.accent]);

  // Load data only once on component mount and set up auto-refresh intervals
  useEffect(() => {
    const initialLoad = async () => {
      try {
        await fetchUserData();
        if (userData?.id) {
          await fetchPerformanceData();
        }
      } catch (error) {
        console.error('Error in initial load:', error);
      } finally {
        setLoading(false); // Only set loading to false after initial load
      }
    };

    initialLoad(); // Initial load

    // Set up interval to refresh dashboard data every 3 seconds (silently)
    const dashboardInterval = setInterval(() => {
      backgroundRefresh(); // Use silent refresh for automatic updates
    }, 900000);

    // Set up interval to check for active trips every 3 seconds
    const activeTripsInterval = setInterval(() => {
      checkForActiveTrip();
    }, 900000);

    // Cleanup intervals on component unmount
    return () => {
      clearInterval(dashboardInterval);
      clearInterval(activeTripsInterval);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Add refresh button to header
  useEffect(() => {
    navigation?.setOptions({
      headerRight: renderRefreshButton,
    });
  }, [navigation, renderRefreshButton]);

  const handleTripStarted = useCallback(
    (tripId: string) => {
      console.log('Trip started:', tripId);
      // Force check for active trip after starting a trip
      setTimeout(() => {
        checkForActiveTrip();
      }, 1000); // Wait 1 second for API to update
    },
    [checkForActiveTrip]
  );

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        {/* Active Trip Banner */}
        {hasActiveTrip && activeTrip && (
          <View style={[styles.activeTripBanner, { backgroundColor: theme.success }]}>
            <View style={styles.activeTripContent}>
              <View style={styles.activeTripInfo}>
                <Text style={[styles.activeTripTitle, { color: '#ffffff' }]}>Active Trip</Text>
                <Text style={[styles.activeTripName, { color: '#ffffff' }]} numberOfLines={1}>
                  {activeTrip.name}
                </Text>
              </View>
              <TouchableOpacity
                style={[styles.activeTripButton, { backgroundColor: 'rgba(255,255,255,0.2)' }]}
                onPress={() => navigation?.navigate('ActiveTrip')}
              >
                <Text style={[styles.activeTripButtonText, { color: '#ffffff' }]}>View Trip</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}

        {/* Driver Score Card */}
        <DriverScoreCard
          theme={theme}
          userData={userData}
          performanceData={performanceData}
          loading={loading && !userData} // Only show loading if no userData yet
          onRefreshUserData={fetchUserData}
        />

        {
          /* Main Content */
          <View style={styles.tripsContainer}>
            {/* Upcoming Trips */}
            <UpcomingTrips
              theme={theme}
              onTripStarted={handleTripStarted}
              userData={userData}
              navigation={navigation}
            />

            {/* Recent Trips */}
            <RecentTrips theme={theme} userData={userData} navigation={navigation} />
          </View>
        }
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollView: {
    flex: 1,
  },
  // Active Trip Banner Styles
  activeTripBanner: {
    margin: 16,
    padding: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  activeTripContent: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  activeTripInfo: {
    flex: 1,
  },
  activeTripTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: 2,
  },
  activeTripName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  activeTripButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
    backgroundColor: 'rgba(255,255,255,0.2)',
  },
  activeTripButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#ffffff',
  },
  // Driver Score Card Styles
  scoreCard: {
    margin: 16,
    padding: 20,
    borderRadius: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  scoreHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  driverInfo: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  avatar: {
    width: 50,
    height: 50,
    borderRadius: 25,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  avatarText: {
    color: '#ffffff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  driverDetails: {
    flex: 1,
  },
  driverName: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  driverRole: {
    fontSize: 14,
    marginTop: 2,
  },
  refreshButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: 8,
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#10b981',
    marginRight: 6,
  },
  statusText: {
    fontSize: 12,
  },
  metricsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  metricItem: {
    alignItems: 'center',
  },
  metricValue: {
    fontSize: 24,
    fontWeight: 'bold',
  },
  metricLabel: {
    fontSize: 12,
    marginTop: 4,
    textAlign: 'center',
  },
  loadingContainer: {
    padding: 20,
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 8,
    fontSize: 14,
  },
  // Main Grid Layout
  mainGrid: {
    flexDirection: width > 768 ? 'row' : 'column',
    padding: 16,
    gap: 16,
  },
  leftColumn: {
    flex: width > 768 ? 1 : undefined,
  },
  rightColumn: {
    flex: width > 768 ? 2 : undefined,
    gap: 16,
  },
  // Section Container Styles
  sectionContainer: {
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  // Trips Styles
  tripsScroll: {
    marginBottom: 16,
  },
  tripCard: {
    width: 300,
    padding: 16,
    borderRadius: 16,
    borderWidth: 1,
    marginRight: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  tripHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  tripName: {
    fontSize: 16,
    fontWeight: 'bold',
    flex: 1,
    marginRight: 8,
  },
  statusBadgeTrip: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  routeContainer: {
    marginBottom: 16,
  },
  locationItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 4,
  },
  locationDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 8,
  },
  startDot: {
    backgroundColor: '#10b981',
  },
  endDot: {
    backgroundColor: '#f59e0b',
  },
  locationText: {
    fontSize: 14,
    fontWeight: '500',
    flex: 1,
  },
  routeLine: {
    width: 2,
    height: 16,
    marginLeft: 3,
    marginVertical: 2,
  },
  timeContainer: {
    flexDirection: 'row',
    borderRadius: 12,
    padding: 12,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: 'rgba(0,0,0,0.1)',
  },
  timeSection: {
    flex: 1,
    alignItems: 'center',
  },
  timeDivider: {
    width: 1,
    marginHorizontal: 12,
  },
  timeLabel: {
    fontSize: 11,
    fontWeight: '500',
    marginBottom: 2,
  },
  timeValue: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 2,
  },
  dateValue: {
    fontSize: 10,
  },
  tripFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  distanceContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  distanceText: {
    fontSize: 14,
    fontWeight: '500',
    marginLeft: 4,
  },
  startButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
    gap: 4,
  },
  startButtonText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '600',
  },
  viewButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
    borderWidth: 1,
    gap: 4,
  },
  viewButtonText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#ffffff',
  },
  // Legacy styles for compatibility
  tripRoute: {
    fontSize: 14,
    fontWeight: '500',
  },
  tripArrow: {
    fontSize: 12,
    marginVertical: 4,
  },
  tripDetails: {
    flexDirection: 'row',
    gap: 16,
    marginBottom: 12,
  },
  tripDetailItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  tripDetailText: {
    fontSize: 12,
  },
  emptyText: {
    textAlign: 'center',
    fontSize: 14,
    padding: 20,
  },
  // Recent Trips Styles
  recentTripItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
  },
  recentTripInfo: {
    flex: 1,
  },
  recentTripRoute: {
    fontSize: 14,
    fontWeight: '500',
  },
  recentTripDate: {
    fontSize: 12,
    marginTop: 2,
  },
  recentTripRight: {
    alignItems: 'flex-end',
  },
  recentTripDistance: {
    fontSize: 12,
    marginBottom: 4,
  },
  statusBadgeSmall: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 10,
    gap: 2,
  },
  statusBadgeText: {
    fontSize: 10,
    fontWeight: '500',
  },
  // Trips Container Style
  tripsContainer: {
    padding: 20,
    gap: 20,
  },
  // Recent Trips Specific Styles
  recentTripsContainer: {
    gap: 12,
  },
  recentTripCard: {
    width: '100%',
    padding: 16,
    borderRadius: 0,
    borderWidth: 1,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
});
