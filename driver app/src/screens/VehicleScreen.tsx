import React, {useEffect, useState} from 'react';
import {
  View,
  StyleSheet,
  ScrollView,
  RefreshControl,
  Alert,
} from 'react-native';
import {
  Card,
  Text,
  Button,
  List,
  Chip,
  ProgressBar,
} from 'react-native-paper';
import {useAuth} from '../context/AuthContext';
import {apiService} from '../services/apiService';
import {theme} from '../theme/theme';

const VehicleScreen = ({navigation}: any) => {
  const {user} = useAuth();
  const [vehicleInfo, setVehicleInfo] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    if (user?.vehicleId) {
      loadVehicleInfo();
    }
  }, [user]);

  const loadVehicleInfo = async () => {
    try {
      if (user?.vehicleId) {
        const vehicle = await apiService.getVehicleInfo(user.vehicleId);
        setVehicleInfo(vehicle);
      }
    } catch (error) {
      console.error('Failed to load vehicle info:', error);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadVehicleInfo();
    setRefreshing(false);
  };

  const handleVehicleInspection = () => {
    navigation.navigate('VehicleInspection');
  };

  const handleReportIssue = () => {
    navigation.navigate('MaintenanceReport');
  };

  const getMaintenanceColor = (percentage: number) => {
    if (percentage >= 80) return '#4CAF50';
    if (percentage >= 60) return '#FF9800';
    return '#F44336';
  };

  if (!user?.vehicleId) {
    return (
      <View style={styles.container}>
        <Card style={styles.card}>
          <Card.Content>
            <Text style={styles.noVehicleText}>
              No vehicle assigned to your account
            </Text>
          </Card.Content>
        </Card>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }>
        {vehicleInfo && (
          <>
            {/* Vehicle Info Card */}
            <Card style={styles.vehicleCard}>
              <Card.Content>
                <Text style={styles.vehicleTitle}>
                  {vehicleInfo.make} {vehicleInfo.model}
                </Text>
                <Text style={styles.vehicleSubtitle}>
                  {vehicleInfo.year} • {vehicleInfo.licensePlate}
                </Text>
                <View style={styles.vehicleDetails}>
                  <Text style={styles.detailText}>
                    Mileage: {vehicleInfo.mileage || 'N/A'} km
                  </Text>
                  <Text style={styles.detailText}>
                    Fuel Level: {vehicleInfo.fuelLevel || 'N/A'}%
                  </Text>
                </View>
              </Card.Content>
            </Card>

            {/* Maintenance Status */}
            <Card style={styles.card}>
              <Card.Content>
                <Text style={styles.sectionTitle}>Maintenance Status</Text>
                
                <View style={styles.maintenanceItem}>
                  <Text style={styles.maintenanceLabel}>Engine Oil</Text>
                  <ProgressBar
                    progress={(vehicleInfo.maintenance?.oilLevel || 0) / 100}
                    color={getMaintenanceColor(vehicleInfo.maintenance?.oilLevel || 0)}
                    style={styles.progressBar}
                  />
                  <Text style={styles.percentageText}>
                    {vehicleInfo.maintenance?.oilLevel || 0}%
                  </Text>
                </View>

                <View style={styles.maintenanceItem}>
                  <Text style={styles.maintenanceLabel}>Brake Condition</Text>
                  <ProgressBar
                    progress={(vehicleInfo.maintenance?.brakeCondition || 0) / 100}
                    color={getMaintenanceColor(vehicleInfo.maintenance?.brakeCondition || 0)}
                    style={styles.progressBar}
                  />
                  <Text style={styles.percentageText}>
                    {vehicleInfo.maintenance?.brakeCondition || 0}%
                  </Text>
                </View>

                <View style={styles.maintenanceItem}>
                  <Text style={styles.maintenanceLabel}>Tire Condition</Text>
                  <ProgressBar
                    progress={(vehicleInfo.maintenance?.tireCondition || 0) / 100}
                    color={getMaintenanceColor(vehicleInfo.maintenance?.tireCondition || 0)}
                    style={styles.progressBar}
                  />
                  <Text style={styles.percentageText}>
                    {vehicleInfo.maintenance?.tireCondition || 0}%
                  </Text>
                </View>
              </Card.Content>
            </Card>

            {/* Recent Issues */}
            <Card style={styles.card}>
              <Card.Content>
                <Text style={styles.sectionTitle}>Recent Issues</Text>
                {vehicleInfo.recentIssues && vehicleInfo.recentIssues.length > 0 ? (
                  vehicleInfo.recentIssues.map((issue: any, index: number) => (
                    <List.Item
                      key={index}
                      title={issue.title}
                      description={issue.description}
                      left={(props) => (
                        <List.Icon {...props} icon="alert-circle" />
                      )}
                      right={() => (
                        <Chip mode="outlined" textStyle={{fontSize: 12}}>
                          {issue.status}
                        </Chip>
                      )}
                    />
                  ))
                ) : (
                  <Text style={styles.emptyText}>No recent issues</Text>
                )}
              </Card.Content>
            </Card>
          </>
        )}

        {/* Action Buttons */}
        <Card style={styles.card}>
          <Card.Content>
            <Text style={styles.sectionTitle}>Vehicle Actions</Text>
            <Button
              mode="contained"
              icon="clipboard-check"
              onPress={handleVehicleInspection}
              style={styles.actionButton}>
              Perform Inspection
            </Button>
            <Button
              mode="outlined"
              icon="alert-circle"
              onPress={handleReportIssue}
              style={styles.actionButton}>
              Report Issue
            </Button>
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
  vehicleCard: {
    marginBottom: 16,
    backgroundColor: theme.colors.primary,
  },
  vehicleTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
  },
  vehicleSubtitle: {
    fontSize: 14,
    color: '#fff',
    opacity: 0.8,
    marginTop: 4,
  },
  vehicleDetails: {
    marginTop: 12,
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  detailText: {
    color: '#fff',
    fontSize: 12,
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
  maintenanceItem: {
    marginBottom: 16,
  },
  maintenanceLabel: {
    fontSize: 14,
    marginBottom: 8,
    color: theme.colors.onSurface,
  },
  progressBar: {
    height: 8,
    borderRadius: 4,
    marginBottom: 4,
  },
  percentageText: {
    fontSize: 12,
    textAlign: 'right',
    color: theme.colors.onSurface,
  },
  actionButton: {
    marginBottom: 8,
  },
  emptyText: {
    textAlign: 'center',
    color: theme.colors.onSurface,
    opacity: 0.6,
    fontStyle: 'italic',
    marginVertical: 16,
  },
  noVehicleText: {
    textAlign: 'center',
    fontSize: 16,
    color: theme.colors.onSurface,
    opacity: 0.7,
  },
});

export default VehicleScreen;
