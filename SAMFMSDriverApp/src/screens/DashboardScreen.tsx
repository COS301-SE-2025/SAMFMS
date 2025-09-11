import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  useColorScheme,
  StyleSheet,
  Dimensions,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import {
  MapPin,
  Clock,
  Play,
  CheckCircle,
  Eye,
  AlertCircle,
  Activity,
  RefreshCw,
} from 'lucide-react-native';
import {
  getUserData,
  setUserData as saveUserData,
  API_URL,
  getToken,
  updateTrip,
} from '../utils/api';
import { useActiveTripContext } from '../contexts/ActiveTripContext';
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
}

const DriverScoreCard: React.FC<DriverScoreCardProps> = ({
  theme,
  userData,
  performanceData,
  loading,
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

    const fetchUpcomingTrips = async () => {
      try {
        setLoading(true);
        const driverId = userData?.id;

        if (!driverId) {
          console.log('No driver ID found');
          setTrips([]);
          setLoading(false);
          return;
        }

        const employeeID = await getEmployeeID(driverId);
        if (!employeeID) {
          console.log('No employee ID found');
          setTrips([]);
          setLoading(false);
          return;
        }

        const token = await getToken();
        if (!token) {
          setTrips([]);
          setLoading(false);
          return;
        }

        const response = await fetch(`${API_URL}/trips/trips/upcomming/${employeeID.data}`, {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });

        if (response.ok) {
          const data = await response.json();
          console.log('Upcoming trips API response:', data);

          // Extract trips data from nested response structure
          // Based on API response: {"status": "success", "data": {"status": "success", "data": [...]}}
          let tripsData = [];
          if (Array.isArray(data?.data?.data)) {
            tripsData = data.data.data;
          } else if (Array.isArray(data?.data)) {
            tripsData = data.data;
          } else if (Array.isArray(data?.trips)) {
            tripsData = data.trips;
          }

          console.log('Extracted trips data:', tripsData);

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
              // Add formatted display properties (using different names to avoid conflicts)
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

          console.log('Formatted trips:', formattedTrips);
          setTrips(formattedTrips);
        } else {
          console.log('Failed to fetch upcoming trips:', response.status, response.statusText);
          setTrips([]);
        }
      } catch (error) {
        console.error('Error fetching trips:', error);
        setTrips([]);
      } finally {
        setLoading(false);
      }
    };

    if (userData?.id) {
      fetchUpcomingTrips();
    }
  }, [userData?.id]);

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
}

const RecentTrips: React.FC<RecentTripsProps> = ({ theme, userData }) => {
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

          const formattedTrips = tripsData.slice(0, 3).map((trip: any) => ({
            id: trip.id || trip._id,
            route: `${trip.origin?.address || trip.origin?.name || 'Unknown'} → ${
              trip.destination?.address || trip.destination?.name || 'Unknown'
            }`,
            date: trip.actual_start_time
              ? new Date(trip.actual_start_time).toLocaleDateString([], {
                  weekday: 'short',
                  hour: '2-digit',
                  minute: '2-digit',
                })
              : 'Recently',
            status: 'completed',
            distance: trip.estimated_distance ? `${trip.estimated_distance} km` : 'N/A',
          }));

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

  return (
    <View style={[styles.sectionContainer, { backgroundColor: theme.cardBackground }]}>
      <View style={styles.sectionHeader}>
        <Text style={[styles.sectionTitle, { color: theme.text }]}>Recent Trips</Text>
        <Clock size={20} color={theme.accent} />
      </View>

      {recentTrips.length > 0 ? (
        recentTrips.map(trip => (
          <View key={trip.id} style={[styles.recentTripItem, { borderBottomColor: theme.border }]}>
            <View style={styles.recentTripInfo}>
              <Text style={[styles.recentTripRoute, { color: theme.text }]}>{trip.route}</Text>
              <Text style={[styles.recentTripDate, { color: theme.textSecondary }]}>
                {trip.date}
              </Text>
            </View>
            <View style={styles.recentTripRight}>
              <Text style={[styles.recentTripDistance, { color: theme.textSecondary }]}>
                {trip.distance}
              </Text>
              <View style={[styles.statusBadgeSmall, { backgroundColor: theme.accent + '20' }]}>
                <CheckCircle size={12} color={theme.accent} />
                <Text style={[styles.statusBadgeText, { color: theme.accent }]}>Done</Text>
              </View>
            </View>
          </View>
        ))
      ) : (
        <Text style={[styles.emptyText, { color: theme.textSecondary }]}>No recent trips</Text>
      )}
    </View>
  );
};

export default function DashboardScreen({ navigation }: { navigation?: any }) {
  const isDarkMode = useColorScheme() === 'dark';
  const [userData, setUserData] = useState<any>(null);
  const [performanceData, setPerformanceData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Use the ActiveTripContext
  const {
    hasActiveTrip,
    activeTrip,
    checkForActiveTrip,
    clearActiveTrip,
    error: activeTripError,
  } = useActiveTripContext();

  const theme = {
    background: isDarkMode ? '#0f172a' : '#f8fafc',
    cardBackground: isDarkMode ? '#1e293b' : '#ffffff',
    text: isDarkMode ? '#f1f5f9' : '#1e293b',
    textSecondary: isDarkMode ? '#94a3b8' : '#64748b',
    accent: '#3b82f6',
    border: isDarkMode ? '#334155' : '#e2e8f0',
    success: '#10b981',
    warning: '#f59e0b',
    error: '#ef4444',
  };

  const getEmployeeID = useCallback(async (security_id: string) => {
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
        console.log('Employee ID API response (main):', data);
        // Handle nested structure: {"status":"success","data":{"data":"EMP139"}}
        if (data.status === 'success') {
          if (data.data && typeof data.data === 'object' && data.data.data) {
            console.log('Employee ID (data.data.data):', data.data.data);
            // Don't modify userData directly here - we'll update it properly in the calling function
            return data.data.data;
          } else if (data.data && typeof data.data === 'string') {
            console.log('Employee ID (data.data string):', data.data);
            return data.data;
          }
        }
        return null;
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
            console.log('Fetching employee ID for user:', apiUserData.id);
            const employeeId = await getEmployeeID(apiUserData.id);
            if (employeeId) {
              // Add employee_id to userData
              apiUserData.employee_id = employeeId;
              apiUserData.employeeId = employeeId; // Also set with alternate property name for compatibility

              // Save updated user data with employee ID
              await saveUserData(apiUserData);
              console.log('Saved user data with employee ID:', employeeId);
            }
          }

          setUserData(apiUserData);
          console.log(
            'Updated userData with employee ID:',
            apiUserData.employee_id || apiUserData.employeeId || 'Not found'
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

  // Manual refresh function
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

  // Load data only once on component mount
  useEffect(() => {
    refreshDashboard();
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
          loading={loading}
        />

        {/* Behavior Monitoring Button */}
        <View
          style={[styles.behaviorMonitoringContainer, { backgroundColor: theme.cardBackground }]}
        >
          <TouchableOpacity
            style={[styles.behaviorMonitoringButton, { backgroundColor: theme.accent }]}
            onPress={() => navigation?.navigate('BehaviorMonitoring')}
          >
            <Activity size={24} color="#ffffff" />
            <Text style={styles.behaviorMonitoringText}>Behavior Monitoring</Text>
          </TouchableOpacity>
        </View>

        {/* Main Content */}
        <View style={styles.tripsContainer}>
          {/* Upcoming Trips */}
          <UpcomingTrips
            theme={theme}
            onTripStarted={handleTripStarted}
            userData={userData}
            navigation={navigation}
          />

          {/* Recent Trips */}
          <RecentTrips theme={theme} userData={userData} />
        </View>
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
  // Behavior Monitoring Styles
  behaviorMonitoringContainer: {
    margin: 16,
    padding: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  behaviorMonitoringButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 14,
    paddingHorizontal: 20,
    borderRadius: 10,
    gap: 10,
  },
  behaviorMonitoringText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
});
