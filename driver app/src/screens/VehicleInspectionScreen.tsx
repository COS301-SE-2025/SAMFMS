import React, {useState} from 'react';
import {
  View,
  StyleSheet,
  ScrollView,
  Alert,
} from 'react-native';
import {
  Card,
  Text,
  Button,
  Checkbox,
  TextInput,
  RadioButton,
} from 'react-native-paper';
import {useAuth} from '../context/AuthContext';
import {apiService} from '../services/apiService';
import {theme} from '../theme/theme';

const VehicleInspectionScreen = ({navigation}: any) => {
  const {user} = useAuth();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [inspection, setInspection] = useState({
    engineOil: 'good',
    brakes: 'good',
    tires: 'good',
    lights: 'good',
    mirrors: true,
    seatbelts: true,
    airConditioning: 'good',
    fuel: 'good',
    battery: 'good',
    windshield: true,
    notes: '',
  });

  const handleSubmit = async () => {
    if (!user?.vehicleId) {
      Alert.alert('Error', 'No vehicle assigned to your account');
      return;
    }

    setIsSubmitting(true);
    try {
      await apiService.submitVehicleInspection(user.vehicleId, {
        ...inspection,
        timestamp: new Date().toISOString(),
        driverId: user.id,
      });
      
      Alert.alert(
        'Success',
        'Vehicle inspection submitted successfully',
        [
          {
            text: 'OK',
            onPress: () => navigation.goBack(),
          },
        ]
      );
    } catch (error) {
      Alert.alert('Error', 'Failed to submit inspection. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const updateInspection = (field: string, value: any) => {
    setInspection(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  const renderConditionCheck = (label: string, field: string) => (
    <Card style={styles.checkCard}>
      <Card.Content>
        <Text style={styles.checkLabel}>{label}</Text>
        <RadioButton.Group
          onValueChange={(value) => updateInspection(field, value)}
          value={inspection[field as keyof typeof inspection] as string}>
          <View style={styles.radioRow}>
            <View style={styles.radioItem}>
              <RadioButton value="good" />
              <Text>Good</Text>
            </View>
            <View style={styles.radioItem}>
              <RadioButton value="fair" />
              <Text>Fair</Text>
            </View>
            <View style={styles.radioItem}>
              <RadioButton value="poor" />
              <Text>Poor</Text>
            </View>
          </View>
        </RadioButton.Group>
      </Card.Content>
    </Card>
  );

  const renderBooleanCheck = (label: string, field: string) => (
    <Card style={styles.checkCard}>
      <Card.Content>
        <View style={styles.checkboxRow}>
          <Checkbox
            status={
              inspection[field as keyof typeof inspection] ? 'checked' : 'unchecked'
            }
            onPress={() =>
              updateInspection(field, !inspection[field as keyof typeof inspection])
            }
          />
          <Text style={styles.checkboxLabel}>{label}</Text>
        </View>
      </Card.Content>
    </Card>
  );

  return (
    <View style={styles.container}>
      <ScrollView style={styles.scrollView}>
        <Card style={styles.headerCard}>
          <Card.Content>
            <Text style={styles.headerTitle}>Vehicle Inspection</Text>
            <Text style={styles.headerSubtitle}>
              Please check all vehicle components before starting your trip
            </Text>
          </Card.Content>
        </Card>

        {renderConditionCheck('Engine Oil Level', 'engineOil')}
        {renderConditionCheck('Brake System', 'brakes')}
        {renderConditionCheck('Tire Condition', 'tires')}
        {renderConditionCheck('Lights (Headlights, Taillights, Indicators)', 'lights')}
        {renderConditionCheck('Air Conditioning', 'airConditioning')}
        {renderConditionCheck('Fuel Level', 'fuel')}
        {renderConditionCheck('Battery', 'battery')}

        {renderBooleanCheck('Mirrors (Clean and Properly Adjusted)', 'mirrors')}
        {renderBooleanCheck('Seatbelts (All Working)', 'seatbelts')}
        {renderBooleanCheck('Windshield (Clean and Intact)', 'windshield')}

        <Card style={styles.notesCard}>
          <Card.Content>
            <Text style={styles.notesLabel}>Additional Notes</Text>
            <TextInput
              mode="outlined"
              multiline
              numberOfLines={4}
              placeholder="Any additional observations or concerns..."
              value={inspection.notes}
              onChangeText={(text) => updateInspection('notes', text)}
              style={styles.notesInput}
            />
          </Card.Content>
        </Card>

        <Button
          mode="contained"
          onPress={handleSubmit}
          loading={isSubmitting}
          disabled={isSubmitting}
          style={styles.submitButton}
          contentStyle={styles.buttonContent}>
          Submit Inspection
        </Button>
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
  headerCard: {
    marginBottom: 16,
    backgroundColor: theme.colors.primary,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#fff',
    opacity: 0.8,
    marginTop: 4,
  },
  checkCard: {
    marginBottom: 12,
  },
  checkLabel: {
    fontSize: 16,
    fontWeight: '500',
    marginBottom: 12,
    color: theme.colors.onSurface,
  },
  radioRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  radioItem: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  checkboxRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  checkboxLabel: {
    fontSize: 16,
    marginLeft: 8,
    flex: 1,
    color: theme.colors.onSurface,
  },
  notesCard: {
    marginBottom: 16,
  },
  notesLabel: {
    fontSize: 16,
    fontWeight: '500',
    marginBottom: 12,
    color: theme.colors.onSurface,
  },
  notesInput: {
    backgroundColor: theme.colors.surface,
  },
  submitButton: {
    marginBottom: 20,
  },
  buttonContent: {
    paddingVertical: 8,
  },
});

export default VehicleInspectionScreen;
