import React, {useEffect, useState} from 'react';
import {
  View,
  StyleSheet,
  ScrollView,
  Alert,
  Platform,
} from 'react-native';
import {
  Card,
  Text,
  Button,
  Chip,
  List,
  FAB,
} from 'react-native-paper';
import {apiService} from '../services/apiService';
import {theme} from '../theme/theme';

const TripDetailsScreen = ({route, navigation}: any) => {
  const {tripId} = route.params;
  const [trip, setTrip] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadTripDetails();
  }, [tripId]);

  const loadTripDetails = async () => {
    try {
      // This would be implemented in your API service
      // const tripData = await apiService.getTripDetails(tripId);
      // For now, using mock data
      const mockTripData = {
        id: tripId,
        startLocation: 'Depot A',
        destination: 'Client Office Downtown',
        scheduledStartTime: '09:00 AM',
        estimatedDuration: '45 mins',
        distance: '12.5 km',
        status: 'scheduled',
        route: 'Route via Main Street',
        passengers: 0,
        maxPassengers: 4,
        priority: 'normal',
        instructions: 'Pick up documents from reception desk',
        contact: {
          name: 'John Smith',
          phone: '+1234567890',
        },
      };
      setTrip(mockTripData);
    } catch (error) {
      console.error('Failed to load trip details:', error);
      Alert.alert('Error', 'Failed to load trip details');
    } finally {
      setIsLoading(false);
    }
  };

  const handleStartTrip = async () => {
    try {
      await apiService.startTrip(tripId);
      Alert.alert('Success', 'Trip started successfully');
      loadTripDetails(); // Refresh trip data
    } catch (error) {
      Alert.alert('Error', 'Failed to start trip');
    }
  };

  const handleEndTrip = async () => {
    Alert.alert(
      'End Trip',
      'Are you sure you want to end this trip?',
      [
        {
          text: 'Cancel',
          style: 'cancel',
        },
        {
          text: 'End Trip',
          onPress: async () => {
            try {
              await apiService.endTrip(tripId, {
                // Current location would be obtained from GPS
                latitude: 0,
                longitude: 0,
                timestamp: new Date().toISOString(),
              });
              Alert.alert('Success', 'Trip ended successfully');
              navigation.goBack();
            } catch (error) {
              Alert.alert('Error', 'Failed to end trip');
            }
          },
        },
      ]
    );
  };

  const getStatusColor = (status: string) => {
    switch (status) {
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

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return '#F44336';
      case 'medium':
        return '#FF9800';
      case 'low':
        return '#4CAF50';
      default:
        return theme.colors.onSurface;
    }
  };

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <Text>Loading trip details...</Text>
      </View>
    );
  }

  if (!trip) {
    return (
      <View style={styles.errorContainer}>
        <Text>Trip not found</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <ScrollView style={styles.scrollView}>
        {/* Trip Status Card */}
        <Card style={styles.statusCard}>
          <Card.Content>
            <View style={styles.statusHeader}>
              <Text style={styles.tripId}>Trip #{trip.id}</Text>
              <Chip
                mode="outlined"
                textStyle={{
                  color: getStatusColor(trip.status),
                  fontSize: 12,
                }}>
                {trip.status.replace('_', ' ').toUpperCase()}
              </Chip>
            </View>
            <Text style={styles.route}>
              {trip.startLocation} → {trip.destination}
            </Text>
          </Card.Content>
        </Card>

        {/* Trip Details */}
        <Card style={styles.card}>
          <Card.Content>
            <Text style={styles.sectionTitle}>Trip Information</Text>
            <List.Item
              title="Scheduled Start"
              description={trip.scheduledStartTime}
              left={(props) => <List.Icon {...props} icon="clock" />}
            />
            <List.Item
              title="Estimated Duration"
              description={trip.estimatedDuration}
              left={(props) => <List.Icon {...props} icon="timer" />}
            />
            <List.Item
              title="Distance"
              description={trip.distance}
              left={(props) => <List.Icon {...props} icon="map-marker-distance" />}
            />
            <List.Item
              title="Route"
              description={trip.route}
              left={(props) => <List.Icon {...props} icon="directions" />}
            />
            <List.Item
              title="Priority"
              description={
                <Chip
                  mode="outlined"
                  textStyle={{
                    color: getPriorityColor(trip.priority),
                    fontSize: 12,
                  }}>
                  {trip.priority.toUpperCase()}
                </Chip>
              }
              left={(props) => <List.Icon {...props} icon="flag" />}
            />
          </Card.Content>
        </Card>

        {/* Contact Information */}
        <Card style={styles.card}>
          <Card.Content>
            <Text style={styles.sectionTitle}>Contact Information</Text>
            <List.Item
              title={trip.contact.name}
              description={trip.contact.phone}
              left={(props) => <List.Icon {...props} icon="account" />}
              right={(props) => <List.Icon {...props} icon="phone" />}
              onPress={() => {
                // Handle phone call
                console.log('Call contact');
              }}
            />
          </Card.Content>
        </Card>

        {/* Instructions */}
        {trip.instructions && (
          <Card style={styles.card}>
            <Card.Content>
              <Text style={styles.sectionTitle}>Special Instructions</Text>
              <Text style={styles.instructions}>{trip.instructions}</Text>
            </Card.Content>
          </Card>
        )}

        {/* Action Buttons */}
        <Card style={styles.card}>
          <Card.Content>
            <View style={styles.actionButtons}>
              {trip.status === 'scheduled' && (
                <Button
                  mode="contained"
                  onPress={handleStartTrip}
                  style={styles.actionButton}
                  icon="play">
                  Start Trip
                </Button>
              )}
              {trip.status === 'in_progress' && (
                <Button
                  mode="contained"
                  onPress={handleEndTrip}
                  style={styles.actionButton}
                  buttonColor="#F44336"
                  icon="stop">
                  End Trip
                </Button>
              )}
              <Button
                mode="outlined"
                onPress={() => {
                  // Open navigation app
                  console.log('Navigate');
                }}
                style={styles.actionButton}
                icon="navigation">
                Navigate
              </Button>
            </View>
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
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  statusCard: {
    marginBottom: 16,
    backgroundColor: theme.colors.primary,
  },
  statusHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  tripId: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
  },
  route: {
    fontSize: 16,
    color: '#fff',
    opacity: 0.9,
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
  instructions: {
    fontSize: 14,
    lineHeight: 20,
    color: theme.colors.onSurface,
  },
  actionButtons: {
    gap: 8,
  },
  actionButton: {
    marginBottom: 8,
  },
});

export default TripDetailsScreen;
