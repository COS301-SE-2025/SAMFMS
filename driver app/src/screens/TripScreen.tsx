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
  List,
  Chip,
  FAB,
} from 'react-native-paper';
import {apiService} from '../services/apiService';
import {theme} from '../theme/theme';

const TripScreen = ({navigation}: any) => {
  const [trips, setTrips] = useState([]);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadTrips();
  }, []);

  const loadTrips = async () => {
    try {
      const tripsData = await apiService.getTripHistory();
      setTrips(tripsData);
    } catch (error) {
      console.error('Failed to load trips:', error);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadTrips();
    setRefreshing(false);
  };

  const handleTripPress = (tripId: string) => {
    navigation.navigate('TripDetails', {tripId});
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return theme.colors.primary;
      case 'in_progress':
        return '#4CAF50';
      case 'scheduled':
        return '#FF9800';
      case 'cancelled':
        return '#F44336';
      default:
        return theme.colors.onSurface;
    }
  };

  return (
    <View style={styles.container}>
      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }>
        <Card style={styles.statsCard}>
          <Card.Content>
            <Text style={styles.statsTitle}>Trip Statistics</Text>
            <View style={styles.statsRow}>
              <View style={styles.statItem}>
                <Text style={styles.statNumber}>
                  {trips.filter((t: any) => t.status === 'completed').length}
                </Text>
                <Text style={styles.statLabel}>Completed</Text>
              </View>
              <View style={styles.statItem}>
                <Text style={styles.statNumber}>
                  {trips.filter((t: any) => t.status === 'in_progress').length}
                </Text>
                <Text style={styles.statLabel}>In Progress</Text>
              </View>
              <View style={styles.statItem}>
                <Text style={styles.statNumber}>
                  {trips.filter((t: any) => t.status === 'scheduled').length}
                </Text>
                <Text style={styles.statLabel}>Scheduled</Text>
              </View>
            </View>
          </Card.Content>
        </Card>

        <Card style={styles.card}>
          <Card.Content>
            <Text style={styles.sectionTitle}>All Trips</Text>
            {trips.length > 0 ? (
              trips.map((trip: any) => (
                <List.Item
                  key={trip.id}
                  title={`${trip.startLocation} → ${trip.destination}`}
                  description={`${trip.date} • ${trip.distance || 'N/A'} km`}
                  left={(props) => (
                    <List.Icon {...props} icon="map-marker-path" />
                  )}
                  right={() => (
                    <Chip
                      mode="outlined"
                      textStyle={{
                        fontSize: 12,
                        color: getStatusColor(trip.status),
                      }}>
                      {trip.status}
                    </Chip>
                  )}
                  onPress={() => handleTripPress(trip.id)}
                  style={styles.tripItem}
                />
              ))
            ) : (
              <Text style={styles.emptyText}>No trips found</Text>
            )}
          </Card.Content>
        </Card>
      </ScrollView>
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
  statsCard: {
    marginBottom: 16,
    backgroundColor: theme.colors.primary,
  },
  statsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 16,
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  statItem: {
    alignItems: 'center',
  },
  statNumber: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
  },
  statLabel: {
    fontSize: 12,
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
  tripItem: {
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.backdrop,
  },
  emptyText: {
    textAlign: 'center',
    color: theme.colors.onSurface,
    opacity: 0.6,
    fontStyle: 'italic',
    marginVertical: 16,
  },
});

export default TripScreen;
