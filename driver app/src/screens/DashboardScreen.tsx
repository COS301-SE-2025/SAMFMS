import React, {useEffect, useState} from 'react';
import {
  View,
  StyleSheet,
  ScrollView,
  RefreshControl,
} from 'react-native';
import {
  Card,
  Text,
  Button,
  FAB,
  List,
  Chip,
} from 'react-native-paper';
import {useAuth} from '../context/AuthContext';
import {apiService} from '../services/apiService';
import {theme} from '../theme/theme';

const DashboardScreen = ({navigation}: any) => {
  const {user} = useAuth();
  const [activeTrips, setActiveTrips] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const [tripsData, notificationsData] = await Promise.all([
        apiService.getActiveTrips(),
        apiService.getNotifications(),
      ]);
      setActiveTrips(tripsData);
      setNotifications(notificationsData.slice(0, 5)); // Show only 5 recent notifications
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadDashboardData();
    setRefreshing(false);
  };

  const handleStartTrip = (tripId: string) => {
    navigation.navigate('TripDetails', {tripId});
  };

  const handleVehicleInspection = () => {
    navigation.navigate('VehicleInspection');
  };

  return (
    <View style={styles.container}>
      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }>
        {/* Welcome Card */}
        <Card style={styles.welcomeCard}>
          <Card.Content>
            <Text style={styles.welcomeText}>
              Welcome back, {user?.username}!
            </Text>
            <Text style={styles.subText}>
              Ready to start your day?
            </Text>
          </Card.Content>
        </Card>

        {/* Quick Actions */}
        <Card style={styles.card}>
          <Card.Content>
            <Text style={styles.sectionTitle}>Quick Actions</Text>
            <View style={styles.actionButtons}>
              <Button
                mode="outlined"
                icon="car"
                onPress={handleVehicleInspection}
                style={styles.actionButton}>
                Vehicle Check
              </Button>
              <Button
                mode="outlined"
                icon="map"
                onPress={() => navigation.navigate('Trips')}
                style={styles.actionButton}>
                View Trips
              </Button>
            </View>
          </Card.Content>
        </Card>

        {/* Active Trips */}
        <Card style={styles.card}>
          <Card.Content>
            <Text style={styles.sectionTitle}>Active Trips</Text>
            {activeTrips.length > 0 ? (
              activeTrips.map((trip: any) => (
                <List.Item
                  key={trip.id}
                  title={`Trip to ${trip.destination}`}
                  description={`Starts at ${trip.startTime}`}
                  left={(props) => <List.Icon {...props} icon="navigation" />}
                  right={() => (
                    <Chip mode="outlined" textStyle={{fontSize: 12}}>
                      {trip.status}
                    </Chip>
                  )}
                  onPress={() => handleStartTrip(trip.id)}
                />
              ))
            ) : (
              <Text style={styles.emptyText}>No active trips</Text>
            )}
          </Card.Content>
        </Card>

        {/* Recent Notifications */}
        <Card style={styles.card}>
          <Card.Content>
            <Text style={styles.sectionTitle}>Recent Notifications</Text>
            {notifications.length > 0 ? (
              notifications.map((notification: any) => (
                <List.Item
                  key={notification.id}
                  title={notification.title}
                  description={notification.message}
                  left={(props) => (
                    <List.Icon
                      {...props}
                      icon={notification.read ? 'bell-outline' : 'bell'}
                    />
                  )}
                />
              ))
            ) : (
              <Text style={styles.emptyText}>No notifications</Text>
            )}
          </Card.Content>
        </Card>
      </ScrollView>

      <FAB
        style={styles.fab}
        icon="plus"
        onPress={() => navigation.navigate('MaintenanceReport')}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  scrollView: {
    flex: 1,
    padding: 16,
  },
  welcomeCard: {
    marginBottom: 16,
    backgroundColor: theme.colors.primary,
  },
  welcomeText: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
  },
  subText: {
    fontSize: 14,
    color: '#fff',
    opacity: 0.8,
    marginTop: 4,
  },
  card: {
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 12,
    color: theme.colors.primary,
  },
  actionButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  actionButton: {
    flex: 1,
    marginHorizontal: 4,
  },
  emptyText: {
    textAlign: 'center',
    color: theme.colors.onSurface,
    opacity: 0.6,
    fontStyle: 'italic',
    marginVertical: 16,
  },
  fab: {
    position: 'absolute',
    margin: 16,
    right: 0,
    bottom: 0,
    backgroundColor: theme.colors.primary,
  },
});

export default DashboardScreen;
