import React, { useState } from 'react';
import { View, Text, ScrollView, StyleSheet, TouchableOpacity, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTheme } from '../contexts/ThemeContext';
import { DatasetSession } from '../utils/datasetLoader';
import {
  SensorTestHarness,
  SessionTestResult,
  TestConfiguration,
} from '../utils/sensorTestHarness';
import { ValidationMetricsCalculator, ComparisonReport } from '../utils/validationMetrics';
import { DEFAULT_ACCELEROMETER_SETTINGS } from '../utils/accelerometerSettings';

interface DemoScreenProps {
  navigation: {
    goBack: () => void;
  };
}

const DemoScreen: React.FC<DemoScreenProps> = ({ navigation }) => {
  const { theme } = useTheme();
  const [isRunningTests, setIsRunningTests] = useState(false);
  const [testProgress, setTestProgress] = useState(0);
  const [currentTest, setCurrentTest] = useState('');
  const [testResults, setTestResults] = useState<ComparisonReport[]>([]);
  const [selectedReport, setSelectedReport] = useState<ComparisonReport | null>(null);

  const metricsCalculator = new ValidationMetricsCalculator();

  // Test configurations to compare
  const testConfigurations: TestConfiguration[] = [
    {
      name: 'Original (Pre-Fix)',
      description: 'Original settings with issues',
      settings: {
        ...DEFAULT_ACCELEROMETER_SETTINGS,
        accelerationThreshold: 4.5, // Old aggressive threshold
        brakingThreshold: -4.5, // Old aggressive threshold
        enableSensorFusion: false, // Simulating original Z-axis assumption
        enableMultistageFiltering: false,
      },
    },
    {
      name: 'Improved (Post-Fix)',
      description: 'Fixed settings with improvements',
      settings: {
        ...DEFAULT_ACCELEROMETER_SETTINGS,
        accelerationThreshold: 6.5, // Improved threshold
        brakingThreshold: -6.5, // Improved threshold
        enableSensorFusion: true,
        enableMultistageFiltering: true,
      },
    },
    {
      name: 'Sensitive Mode',
      description: 'More sensitive detection for testing',
      settings: {
        ...DEFAULT_ACCELEROMETER_SETTINGS,
        accelerationThreshold: 5.0,
        brakingThreshold: -5.0,
        enableSensorFusion: true,
        enableMultistageFiltering: true,
      },
    },
    {
      name: 'Relaxed Mode',
      description: 'Less sensitive for highway driving',
      settings: {
        ...DEFAULT_ACCELEROMETER_SETTINGS,
        accelerationThreshold: 8.0,
        brakingThreshold: -8.0,
        enableSensorFusion: true,
        enableMultistageFiltering: true,
      },
    },
  ];

  const runDemoTests = async () => {
    setIsRunningTests(true);
    setTestProgress(0);
    setTestResults([]);

    try {
      // Load sample datasets (using mock data for demo since file reading is complex in RN)
      const sampleSessions = await loadSampleSessions();
      const totalConfigs = testConfigurations.length;

      const results: ComparisonReport[] = [];
      let baseline: ComparisonReport | null = null;

      for (let i = 0; i < testConfigurations.length; i++) {
        const config = testConfigurations[i];
        setCurrentTest(`Testing ${config.name}...`);
        setTestProgress((i / totalConfigs) * 100);

        // Run tests with this configuration
        const testHarness = new SensorTestHarness(config.settings);
        const sessionResults: SessionTestResult[] = [];

        for (const session of sampleSessions) {
          const result = await testHarness.runSessionTest(session);
          sessionResults.push(result);
        }

        // Generate comparison report
        const report = metricsCalculator.generateComparisonReport(
          config.name,
          sessionResults,
          baseline?.metrics
        );

        if (i === 0) baseline = report; // Use first config as baseline
        results.push(report);

        // Small delay for demo effect
        await new Promise<void>(resolve => setTimeout(resolve, 500));
      }

      setTestResults(results);
      setSelectedReport(results[1]); // Show improved results by default
      setCurrentTest('Tests completed!');
      setTestProgress(100);
    } catch (error) {
      console.error('Test execution failed:', error);
      Alert.alert('Test Failed', 'An error occurred while running the tests.');
    } finally {
      setIsRunningTests(false);
    }
  };

  // Mock function to create sample sessions for demo
  const loadSampleSessions = async (): Promise<DatasetSession[]> => {
    // In a real implementation, this would load from the actual CSV files
    // For demo purposes, we'll create representative mock data

    const createMockSession = (
      name: string,
      type: 'safe' | 'risky',
      violationLevel: number
    ): DatasetSession => {
      const data = [];
      const baseTime = Date.now();

      // Generate mock accelerometer data for ~2 minutes
      for (let i = 0; i < 1200; i++) {
        // 10Hz for 2 minutes
        const time = baseTime + i * 100;

        // Base acceleration (simulate gravity + small variations)
        let x = (Math.random() - 0.5) * 2;
        let y = (Math.random() - 0.5) * 2;
        let z = 9.81 + (Math.random() - 0.5) * 1;

        // Add violations based on type and level
        if (type === 'risky' && Math.random() < violationLevel) {
          // Simulate aggressive acceleration/braking
          z += (Math.random() > 0.5 ? 1 : -1) * (4 + Math.random() * 6);
        }

        data.push({
          timestamp: time,
          accelerometer: { x, y, z },
          gyroscope: {
            x: (Math.random() - 0.5) * 0.2,
            y: (Math.random() - 0.5) * 0.2,
            z: (Math.random() - 0.5) * 0.2,
          },
        });
      }

      return {
        name,
        type,
        data,
        duration: 120000, // 2 minutes
        totalSamples: data.length,
        averageSamplingRate: 10,
      };
    };

    return [
      createMockSession('Safe-Drive-1', 'safe', 0.01),
      createMockSession('Safe-Drive-2', 'safe', 0.005),
      createMockSession('Safe-Drive-3', 'safe', 0.02),
      createMockSession('Risky-Drive-1', 'risky', 0.08),
      createMockSession('Risky-Drive-2', 'risky', 0.12),
      createMockSession('Risky-Drive-3', 'risky', 0.06),
    ];
  };

  const renderMetricCard = (title: string, value: string, improvement?: number) => {
    const improvementColor =
      improvement !== undefined ? (improvement > 0 ? '#4CAF50' : '#F44336') : theme.text;

    return (
      <View style={[styles.metricCard, { backgroundColor: theme.cardBackground }]}>
        <Text style={[styles.metricTitle, { color: theme.text }]}>{title}</Text>
        <Text style={[styles.metricValue, { color: theme.accent }]}>{value}</Text>
        {improvement !== undefined && (
          <Text style={[styles.improvement, { color: improvementColor }]}>
            {improvement > 0 ? '+' : ''}
            {improvement.toFixed(1)}%
          </Text>
        )}
      </View>
    );
  };

  const renderResultSummary = (report: ComparisonReport) => (
    <ScrollView style={styles.resultsContainer}>
      <Text style={[styles.sectionTitle, { color: theme.text }]}>
        {report.configurationName} Results
      </Text>

      {/* Classification Performance */}
      <Text style={[styles.subsectionTitle, { color: theme.text }]}>
        Classification Performance
      </Text>
      <View style={styles.metricsGrid}>
        {renderMetricCard('Accuracy', `${(report.metrics.accuracy * 100).toFixed(1)}%`)}
        {renderMetricCard('Precision', `${(report.metrics.precision * 100).toFixed(1)}%`)}
        {renderMetricCard('Recall', `${(report.metrics.recall * 100).toFixed(1)}%`)}
        {renderMetricCard('F1 Score', `${(report.metrics.f1Score * 100).toFixed(1)}%`)}
      </View>

      {/* Behavior Detection */}
      <Text style={[styles.subsectionTitle, { color: theme.text }]}>Behavior Detection</Text>
      <View style={styles.metricsGrid}>
        {renderMetricCard(
          'Safe Sessions Avg',
          `${report.safeSessions.avgViolationRate.toFixed(2)}/min`
        )}
        {renderMetricCard(
          'Risky Sessions Avg',
          `${report.riskySessions.avgViolationRate.toFixed(2)}/min`
        )}
        {renderMetricCard(
          'False Positive Rate',
          `${(report.metrics.falsePositiveRate * 100).toFixed(1)}%`,
          report.improvements.falsePositiveReduction
        )}
        {renderMetricCard(
          'Data Quality',
          `${(report.metrics.avgDataQuality * 100).toFixed(1)}%`,
          report.improvements.qualityImprovement
        )}
      </View>

      {/* System Performance */}
      <Text style={[styles.subsectionTitle, { color: theme.text }]}>System Performance</Text>
      <View style={styles.metricsGrid}>
        {renderMetricCard(
          'Calibration Success',
          `${(report.metrics.calibrationSuccessRate * 100).toFixed(1)}%`,
          report.improvements.calibrationImprovement
        )}
        {renderMetricCard(
          'Calibration Time',
          `${(report.metrics.avgCalibrationTime / 1000).toFixed(1)}s`
        )}
        {renderMetricCard('Samples Skipped', `${report.metrics.samplesSkippedRate.toFixed(1)}%`)}
        {renderMetricCard('Overall Score', `${report.improvements.overallScore.toFixed(1)}/100`)}
      </View>

      {/* Key Insights */}
      <Text style={[styles.subsectionTitle, { color: theme.text }]}>Key Insights</Text>
      <View style={[styles.insightsCard, { backgroundColor: theme.cardBackground }]}>
        <Text style={[styles.insightText, { color: theme.text }]}>
          • Risky sessions show{' '}
          {(
            (report.riskySessions.avgViolationRate / report.safeSessions.avgViolationRate) *
            100
          ).toFixed(0)}
          % more violations than safe sessions
        </Text>
        <Text style={[styles.insightText, { color: theme.text }]}>
          • Algorithm achieves {(report.metrics.accuracy * 100).toFixed(0)}% classification accuracy
        </Text>
        <Text style={[styles.insightText, { color: theme.text }]}>
          • {(report.metrics.calibrationSuccessRate * 100).toFixed(0)}% successful calibration rate
        </Text>
        <Text style={[styles.insightText, { color: theme.text }]}>
          • {report.improvements.falsePositiveReduction.toFixed(0)}% reduction in false positives
        </Text>
      </View>
    </ScrollView>
  );

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
      {/* Header */}
      <View style={[styles.header, { backgroundColor: theme.accent }]}>
        <TouchableOpacity onPress={navigation.goBack} style={styles.backButton}>
          <Text style={styles.backButtonText}>←</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Sensor Algorithm Demo</Text>
      </View>

      {/* Control Panel */}
      <View style={[styles.controlPanel, { backgroundColor: theme.cardBackground }]}>
        <TouchableOpacity
          style={[
            styles.runTestButton,
            { backgroundColor: isRunningTests ? theme.buttonDisabled : theme.buttonPrimary },
          ]}
          onPress={runDemoTests}
          disabled={isRunningTests}
        >
          <Text style={styles.buttonText}>
            {isRunningTests ? 'Running Tests...' : 'Run Algorithm Validation'}
          </Text>
        </TouchableOpacity>

        {isRunningTests && (
          <View style={styles.progressContainer}>
            <Text style={[styles.progressText, { color: theme.text }]}>{currentTest}</Text>
            <View style={[styles.progressBar, { backgroundColor: theme.border }]}>
              <View
                style={[
                  styles.progressFill,
                  { backgroundColor: theme.accent, width: `${testProgress}%` },
                ]}
              />
            </View>
            <Text style={[styles.progressText, { color: theme.text }]}>
              {testProgress.toFixed(0)}% Complete
            </Text>
          </View>
        )}
      </View>

      {/* Configuration Selector */}
      {testResults.length > 0 && (
        <View style={[styles.configSelector, { backgroundColor: theme.cardBackground }]}>
          <Text style={[styles.selectorTitle, { color: theme.text }]}>View Results:</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            {testResults.map((result, index) => {
              const isSelected = selectedReport?.configurationName === result.configurationName;
              const buttonTextColor = isSelected ? '#FFFFFF' : theme.text;

              return (
                <TouchableOpacity
                  key={index}
                  style={[
                    styles.configButton,
                    {
                      backgroundColor: isSelected ? theme.accent : theme.buttonSecondary,
                    },
                  ]}
                  onPress={() => setSelectedReport(result)}
                >
                  <Text style={[styles.configButtonText, { color: buttonTextColor }]}>
                    {result.configurationName}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </ScrollView>
        </View>
      )}

      {/* Results Display */}
      {selectedReport && renderResultSummary(selectedReport)}
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
    padding: 16,
    elevation: 4,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
  },
  backButton: {
    marginRight: 16,
    padding: 8,
  },
  backButtonText: {
    fontSize: 24,
    color: '#FFFFFF',
    fontWeight: 'bold',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  controlPanel: {
    padding: 16,
    margin: 16,
    borderRadius: 12,
    elevation: 2,
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
  },
  runTestButton: {
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  buttonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: 'bold',
  },
  progressContainer: {
    marginTop: 16,
  },
  progressText: {
    textAlign: 'center',
    fontSize: 14,
    marginBottom: 8,
  },
  progressBar: {
    height: 8,
    borderRadius: 4,
    marginBottom: 8,
  },
  progressFill: {
    height: '100%',
    borderRadius: 4,
  },
  configSelector: {
    padding: 16,
    marginHorizontal: 16,
    borderRadius: 12,
    elevation: 2,
  },
  selectorTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 12,
  },
  configButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    marginRight: 8,
    borderRadius: 8,
  },
  configButtonText: {
    fontSize: 14,
    fontWeight: '500',
  },
  resultsContainer: {
    flex: 1,
    padding: 16,
  },
  sectionTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 16,
    textAlign: 'center',
  },
  subsectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginTop: 20,
    marginBottom: 12,
  },
  metricsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  metricCard: {
    width: '48%',
    padding: 16,
    marginBottom: 12,
    borderRadius: 8,
    elevation: 1,
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 1,
  },
  metricTitle: {
    fontSize: 12,
    marginBottom: 4,
  },
  metricValue: {
    fontSize: 20,
    fontWeight: 'bold',
  },
  improvement: {
    fontSize: 12,
    marginTop: 4,
    fontWeight: '500',
  },
  insightsCard: {
    padding: 16,
    borderRadius: 8,
    elevation: 1,
  },
  insightText: {
    fontSize: 14,
    marginBottom: 8,
    lineHeight: 20,
  },
});

export default DemoScreen;
