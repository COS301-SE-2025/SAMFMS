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
  TextInput,
  RadioButton,
  Chip,
} from 'react-native-paper';
import {useAuth} from '../context/AuthContext';
import {apiService} from '../services/apiService';
import {theme} from '../theme/theme';

const MaintenanceReportScreen = ({navigation}: any) => {
  const {user} = useAuth();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [report, setReport] = useState({
    category: 'mechanical',
    severity: 'medium',
    title: '',
    description: '',
    location: '',
  });

  const categories = [
    {value: 'mechanical', label: 'Mechanical'},
    {value: 'electrical', label: 'Electrical'},
    {value: 'body', label: 'Body/Exterior'},
    {value: 'interior', label: 'Interior'},
    {value: 'safety', label: 'Safety'},
    {value: 'other', label: 'Other'},
  ];

  const severities = [
    {value: 'low', label: 'Low', color: '#4CAF50'},
    {value: 'medium', label: 'Medium', color: '#FF9800'},
    {value: 'high', label: 'High', color: '#F44336'},
    {value: 'critical', label: 'Critical', color: '#9C27B0'},
  ];

  const handleSubmit = async () => {
    if (!report.title.trim() || !report.description.trim()) {
      Alert.alert('Error', 'Please fill in all required fields');
      return;
    }

    if (!user?.vehicleId) {
      Alert.alert('Error', 'No vehicle assigned to your account');
      return;
    }

    setIsSubmitting(true);
    try {
      await apiService.reportMaintenanceIssue(user.vehicleId, {
        ...report,
        timestamp: new Date().toISOString(),
        reportedBy: user.id,
        driverName: user.username,
      });

      Alert.alert(
        'Success',
        'Maintenance issue reported successfully',
        [
          {
            text: 'OK',
            onPress: () => navigation.goBack(),
          },
        ]
      );
    } catch (error) {
      Alert.alert('Error', 'Failed to submit report. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const updateReport = (field: string, value: string) => {
    setReport(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  return (
    <View style={styles.container}>
      <ScrollView style={styles.scrollView}>
        <Card style={styles.headerCard}>
          <Card.Content>
            <Text style={styles.headerTitle}>Report Maintenance Issue</Text>
            <Text style={styles.headerSubtitle}>
              Help us keep vehicles in optimal condition
            </Text>
          </Card.Content>
        </Card>

        {/* Category Selection */}
        <Card style={styles.card}>
          <Card.Content>
            <Text style={styles.sectionTitle}>Issue Category</Text>
            <View style={styles.chipContainer}>
              {categories.map((category) => (
                <Chip
                  key={category.value}
                  mode={report.category === category.value ? 'flat' : 'outlined'}
                  selected={report.category === category.value}
                  onPress={() => updateReport('category', category.value)}
                  style={styles.chip}>
                  {category.label}
                </Chip>
              ))}
            </View>
          </Card.Content>
        </Card>

        {/* Severity Selection */}
        <Card style={styles.card}>
          <Card.Content>
            <Text style={styles.sectionTitle}>Severity Level</Text>
            <RadioButton.Group
              onValueChange={(value) => updateReport('severity', value)}
              value={report.severity}>
              {severities.map((severity) => (
                <View key={severity.value} style={styles.radioRow}>
                  <RadioButton value={severity.value} />
                  <Text style={[styles.radioLabel, {color: severity.color}]}>
                    {severity.label}
                  </Text>
                </View>
              ))}
            </RadioButton.Group>
          </Card.Content>
        </Card>

        {/* Issue Details */}
        <Card style={styles.card}>
          <Card.Content>
            <Text style={styles.sectionTitle}>Issue Details</Text>
            
            <TextInput
              label="Issue Title *"
              value={report.title}
              onChangeText={(text) => updateReport('title', text)}
              mode="outlined"
              style={styles.input}
              placeholder="Brief description of the issue"
            />

            <TextInput
              label="Detailed Description *"
              value={report.description}
              onChangeText={(text) => updateReport('description', text)}
              mode="outlined"
              multiline
              numberOfLines={4}
              style={styles.input}
              placeholder="Provide detailed information about the issue..."
            />

            <TextInput
              label="Location on Vehicle"
              value={report.location}
              onChangeText={(text) => updateReport('location', text)}
              mode="outlined"
              style={styles.input}
              placeholder="e.g., Front left tire, Dashboard, Engine bay"
            />
          </Card.Content>
        </Card>

        {/* Tips Card */}
        <Card style={styles.tipsCard}>
          <Card.Content>
            <Text style={styles.tipsTitle}>Reporting Tips</Text>
            <Text style={styles.tipsText}>
              • Be as specific as possible{'\n'}
              • Include when the issue first occurred{'\n'}
              • Mention if it affects vehicle safety{'\n'}
              • Note any unusual sounds, smells, or behaviors
            </Text>
          </Card.Content>
        </Card>

        <Button
          mode="contained"
          onPress={handleSubmit}
          loading={isSubmitting}
          disabled={isSubmitting}
          style={styles.submitButton}
          contentStyle={styles.buttonContent}>
          Submit Report
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
  card: {
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 12,
    color: theme.colors.onSurface,
  },
  chipContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  chip: {
    marginBottom: 8,
  },
  radioRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  radioLabel: {
    fontSize: 16,
    marginLeft: 8,
    fontWeight: '500',
  },
  input: {
    marginBottom: 12,
  },
  tipsCard: {
    marginBottom: 16,
    backgroundColor: '#E3F2FD',
  },
  tipsTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: theme.colors.primary,
    marginBottom: 8,
  },
  tipsText: {
    fontSize: 14,
    lineHeight: 20,
    color: theme.colors.onSurface,
  },
  submitButton: {
    marginBottom: 20,
  },
  buttonContent: {
    paddingVertical: 8,
  },
});

export default MaintenanceReportScreen;
