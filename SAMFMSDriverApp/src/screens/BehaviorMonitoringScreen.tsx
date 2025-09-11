import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  useColorScheme,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import {
  Play,
  Square,
  AlertTriangle,
  Clock,
  Smartphone,
  Activity,
  Trash2,
  ArrowLeft,
} from 'lucide-react-native';
import { useBehaviorMonitoring } from '../contexts/BehaviorMonitoringContext';

// Import NavigationProp type
import { NavigationProp, ParamListBase } from '@react-navigation/native';

interface BehaviorMonitoringScreenProps {
  navigation: NavigationProp<ParamListBase>;
}

const BehaviorMonitoringScreen: React.FC<BehaviorMonitoringScreenProps> = ({ navigation }) => {
  const {
    isMonitoringActive,
    currentBehaviorMetrics,
    startMonitoring,
    stopMonitoring,
    clearViolations,
  } = useBehaviorMonitoring();

  // Handle going back when monitoring is active
  const handleGoBack = React.useCallback(() => {
    if (isMonitoringActive) {
      // Alert user that monitoring will continue in background
      Alert.alert(
        'Behavior Monitoring Active',
        'Monitoring will continue in the background. Your driving behavior is still being tracked.',
        [{ text: 'OK', onPress: () => navigation.goBack() }]
      );
    } else {
      navigation.goBack();
    }
  }, [isMonitoringActive, navigation]);

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

  // Format duration in seconds to human readable format
  const formatDuration = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const remainingSeconds = seconds % 60;

    if (hours > 0) {
      return `${hours}h ${minutes}m ${remainingSeconds}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${remainingSeconds}s`;
    } else {
      return `${remainingSeconds}s`;
    }
  };

  // Format timestamp to readable format
  const formatTimestamp = (date: Date): string => {
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    });
  };

  // Get violation type icon and color
  const getViolationDetails = (type: string) => {
    switch (type) {
      case 'app_background':
        return {
          icon: Smartphone,
          color: theme.danger,
          title: 'App Backgrounded',
        };
      case 'screen_interaction_loss':
        return {
          icon: Activity,
          color: theme.warning,
          title: 'No Screen Interaction',
        };
      case 'call_detected':
        return {
          icon: AlertTriangle,
          color: theme.danger,
          title: 'Call Detected',
        };
      case 'notification_interaction':
        return {
          icon: AlertTriangle,
          color: theme.warning,
          title: 'Notification Interaction',
        };
      case 'grace_period_exceeded':
        return {
          icon: AlertTriangle,
          color: theme.danger,
          title: 'Grace Period Exceeded',
        };
      case 'extended_background':
        return {
          icon: Smartphone,
          color: theme.danger,
          title: 'Extended Background',
        };
      default:
        return {
          icon: AlertTriangle,
          color: theme.warning,
          title: 'Unknown Violation',
        };
    }
  };

  // Handle start/stop monitoring
  const handleToggleMonitoring = () => {
    if (isMonitoringActive) {
      Alert.alert('Stop Monitoring', 'Are you sure you want to stop behavior monitoring?', [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Stop',
          style: 'destructive',
          onPress: stopMonitoring,
        },
      ]);
    } else {
      // Starting monitoring with background support
      Alert.alert(
        'Start Monitoring',
        'Behavior monitoring will continue even when the app is in the background. You will receive notifications of any violations.',
        [
          { text: 'Cancel', style: 'cancel' },
          {
            text: 'Start',
            onPress: () => {
              startMonitoring();
              // Inform user that monitoring has started
              Alert.alert(
                'Monitoring Active',
                'Your driving behavior is now being monitored. You can return to the dashboard and monitoring will continue in the background.'
              );
            },
          },
        ]
      );
    }
  };

  // Handle clear violations
  const handleClearViolations = () => {
    if (currentBehaviorMetrics.phoneUsageViolations.length === 0) return;

    Alert.alert('Clear Violations', 'Are you sure you want to clear all recorded violations?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Clear',
        style: 'destructive',
        onPress: clearViolations,
      },
    ]);
  };

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
          style={[styles.backButton, { backgroundColor: theme.accent + '20' }]}
          onPress={handleGoBack}
        >
          <ArrowLeft size={20} color={theme.accent} />
        </TouchableOpacity>
        <Text style={[styles.headerTitle, { color: theme.text }]}>Behavior Monitoring</Text>
        <View style={styles.headerSpacer} />
      </View>

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {/* Status Card */}
        <View style={[styles.card, { backgroundColor: theme.cardBackground }]}>
          <View style={styles.statusHeader}>
            <View style={styles.statusInfo}>
              <Text style={[styles.statusTitle, { color: theme.text }]}>Monitoring Status</Text>
              <Text
                style={[
                  styles.statusText,
                  { color: isMonitoringActive ? theme.success : theme.textSecondary },
                ]}
              >
                {isMonitoringActive ? 'Active' : 'Inactive'}
              </Text>
            </View>
            <TouchableOpacity
              style={[
                styles.toggleButton,
                {
                  backgroundColor: isMonitoringActive ? theme.danger : theme.success,
                },
              ]}
              onPress={handleToggleMonitoring}
            >
              {isMonitoringActive ? (
                <Square size={24} color="#ffffff" />
              ) : (
                <Play size={24} color="#ffffff" />
              )}
              <Text style={styles.toggleButtonText}>{isMonitoringActive ? 'Stop' : 'Start'}</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Background Warning - This replaces the Grace Period Warning */}
        {false && (
          <View
            style={[
              styles.graceWarningCard,
              { backgroundColor: theme.warning + '20', borderColor: theme.warning },
            ]}
          >
            <View style={styles.graceWarningHeader}>
              <AlertTriangle size={24} color={theme.warning} />
              <Text style={[styles.graceWarningTitle, { color: theme.warning }]}>
                Background Usage Warning
              </Text>
            </View>
            <Text style={[styles.graceWarningText, { color: theme.text }]}>
              Minimizing this app for more than 1 minute will result in a violation.
            </Text>
          </View>
        )}

        {/* Metrics Cards */}
        <View style={styles.metricsContainer}>
          <View style={[styles.metricCard, { backgroundColor: theme.cardBackground }]}>
            <Clock size={20} color={theme.accent} />
            <Text style={[styles.metricValue, { color: theme.text }]}>
              {formatDuration(currentBehaviorMetrics.totalMonitoringTime)}
            </Text>
            <Text style={[styles.metricLabel, { color: theme.textSecondary }]}>Total Time</Text>
          </View>

          <View style={[styles.metricCard, { backgroundColor: theme.cardBackground }]}>
            <AlertTriangle size={20} color={theme.danger} />
            <Text style={[styles.metricValue, { color: theme.text }]}>
              {currentBehaviorMetrics.phoneUsageViolations.length}
            </Text>
            <Text style={[styles.metricLabel, { color: theme.textSecondary }]}>Violations</Text>
          </View>

          <View style={[styles.metricCard, { backgroundColor: theme.cardBackground }]}>
            <Smartphone size={20} color={theme.warning} />
            <Text style={[styles.metricValue, { color: theme.text }]}>
              {formatDuration(currentBehaviorMetrics.appBackgroundTime)}
            </Text>
            <Text style={[styles.metricLabel, { color: theme.textSecondary }]}>
              Background Time
            </Text>
          </View>
        </View>

        {/* Violations Section */}
        <View style={[styles.card, { backgroundColor: theme.cardBackground }]}>
          <View style={styles.violationsHeader}>
            <Text style={[styles.sectionTitle, { color: theme.text }]}>Phone Usage Violations</Text>
            {currentBehaviorMetrics.phoneUsageViolations.length > 0 && (
              <TouchableOpacity
                style={[styles.clearButton, { borderColor: theme.danger }]}
                onPress={handleClearViolations}
              >
                <Trash2 size={16} color={theme.danger} />
                <Text style={[styles.clearButtonText, { color: theme.danger }]}>Clear</Text>
              </TouchableOpacity>
            )}
          </View>

          {currentBehaviorMetrics.phoneUsageViolations.length === 0 ? (
            <View style={styles.emptyState}>
              <Activity size={48} color={theme.textSecondary} style={styles.emptyIcon} />
              <Text style={[styles.emptyText, { color: theme.textSecondary }]}>
                No violations detected
              </Text>
              <Text style={[styles.emptySubtext, { color: theme.textSecondary }]}>
                {isMonitoringActive
                  ? 'Keep the app active and avoid phone usage while monitoring'
                  : 'Start monitoring to track phone usage violations'}
              </Text>
            </View>
          ) : (
            <View style={styles.violationsList}>
              {currentBehaviorMetrics.phoneUsageViolations
                .slice()
                .reverse()
                .map((violation, _index) => {
                  const details = getViolationDetails(violation.type);
                  const IconComponent = details.icon;

                  return (
                    <View
                      key={violation.id}
                      style={[
                        styles.violationItem,
                        { borderLeftColor: details.color, backgroundColor: theme.background },
                      ]}
                    >
                      <View style={styles.violationHeader}>
                        <View style={styles.violationTitleRow}>
                          <IconComponent size={16} color={details.color} />
                          <Text style={[styles.violationTitle, { color: theme.text }]}>
                            {details.title}
                          </Text>
                        </View>
                        <Text style={[styles.violationTime, { color: theme.textSecondary }]}>
                          {formatTimestamp(violation.timestamp)}
                        </Text>
                      </View>
                      <Text style={[styles.violationDescription, { color: theme.textSecondary }]}>
                        {violation.description}
                      </Text>
                      {violation.duration && (
                        <Text style={[styles.violationDuration, { color: details.color }]}>
                          Duration: {formatDuration(violation.duration)}
                        </Text>
                      )}
                    </View>
                  );
                })}
            </View>
          )}
        </View>

        {/* Instructions Card */}
        <View style={[styles.card, { backgroundColor: theme.cardBackground }]}>
          <Text style={[styles.sectionTitle, { color: theme.text }]}>How It Works</Text>
          <View style={styles.instructionsList}>
            <Text style={[styles.instructionItem, { color: theme.textSecondary }]}>
              • Tap "Start" to begin monitoring phone usage behavior
            </Text>
            <Text style={[styles.instructionItem, { color: theme.textSecondary }]}>
              • Keep the app active and in foreground during monitoring
            </Text>
            <Text style={[styles.instructionItem, { color: theme.textSecondary }]}>
              • Violations are recorded when you switch away from the app
            </Text>
            <Text style={[styles.instructionItem, { color: theme.textSecondary }]}>
              • Background time and interaction gaps are tracked
            </Text>
            <Text style={[styles.instructionItem, { color: theme.textSecondary }]}>
              • Tap "Stop" to end monitoring and review results
            </Text>
          </View>
        </View>
      </ScrollView>
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
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginLeft: 16,
  },
  headerSpacer: {
    flex: 1,
  },
  content: {
    flex: 1,
    padding: 16,
  },
  card: {
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  statusHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  statusInfo: {
    flex: 1,
  },
  statusTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  statusText: {
    fontSize: 14,
    fontWeight: '500',
  },
  toggleButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 8,
    gap: 8,
  },
  toggleButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
  metricsContainer: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 16,
  },
  metricCard: {
    flex: 1,
    alignItems: 'center',
    padding: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  metricValue: {
    fontSize: 18,
    fontWeight: '700',
    marginTop: 8,
    marginBottom: 4,
  },
  metricLabel: {
    fontSize: 12,
    textAlign: 'center',
  },
  violationsHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
  },
  clearButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    borderWidth: 1,
    gap: 4,
  },
  clearButtonText: {
    fontSize: 12,
    fontWeight: '500',
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 32,
  },
  emptyIcon: {
    marginBottom: 12,
  },
  emptyText: {
    fontSize: 16,
    fontWeight: '500',
    marginBottom: 8,
  },
  emptySubtext: {
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 20,
  },
  violationsList: {
    gap: 12,
  },
  violationItem: {
    borderLeftWidth: 4,
    borderRadius: 8,
    padding: 12,
  },
  violationHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  violationTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  violationTitle: {
    fontSize: 14,
    fontWeight: '600',
  },
  violationTime: {
    fontSize: 12,
  },
  violationDescription: {
    fontSize: 13,
    lineHeight: 18,
    marginBottom: 4,
  },
  violationDuration: {
    fontSize: 12,
    fontWeight: '500',
  },
  instructionsList: {
    gap: 8,
    marginTop: 12,
  },
  instructionItem: {
    fontSize: 14,
    lineHeight: 20,
  },
  graceWarningCard: {
    margin: 16,
    padding: 16,
    borderRadius: 12,
    borderWidth: 2,
  },
  graceWarningHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  graceWarningTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginLeft: 8,
  },
  graceWarningText: {
    fontSize: 16,
    marginBottom: 12,
    textAlign: 'center',
  },
  countdownContainer: {
    alignItems: 'center',
    marginVertical: 8,
  },
  countdownText: {
    fontSize: 32,
    fontWeight: 'bold',
  },
  countdownLabel: {
    fontSize: 14,
    marginTop: 4,
  },
  graceWarningSubtext: {
    fontSize: 12,
    textAlign: 'center',
    fontStyle: 'italic',
    marginTop: 8,
  },
});

export default BehaviorMonitoringScreen;
