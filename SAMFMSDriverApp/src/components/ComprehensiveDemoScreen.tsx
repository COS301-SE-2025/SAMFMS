import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import DemoScreen from '../screens/DemoScreen';
import { ValidationDemoScreen } from './ValidationDemoScreen';

type DemoMode = 'menu' | 'basic_demo' | 'validation_demo';

interface ComprehensiveDemoScreenProps {
  navigation: {
    goBack: () => void;
  };
}

/**
 * Master demo navigation screen that provides access to all testing capabilities
 */
export const ComprehensiveDemoScreen: React.FC<ComprehensiveDemoScreenProps> = ({
  navigation: _navigation,
}) => {
  const [currentMode, setCurrentMode] = useState<DemoMode>('menu');

  if (currentMode === 'basic_demo') {
    return <DemoScreen navigation={{ goBack: () => setCurrentMode('menu') }} />;
  }

  if (currentMode === 'validation_demo') {
    return <ValidationDemoScreen onBack={() => setCurrentMode('menu')} />;
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Driver Behavior Algorithm Demo</Text>
        <Text style={styles.subtitle}>Comprehensive Testing & Validation Suite</Text>
      </View>

      <View style={styles.content}>
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>🎯 Available Demo Modes</Text>

          <TouchableOpacity
            style={[styles.demoCard, styles.basicDemo]}
            onPress={() => setCurrentMode('basic_demo')}
          >
            <View style={styles.cardHeader}>
              <Text style={styles.cardIcon}>🔍</Text>
              <Text style={styles.cardTitle}>Basic Algorithm Demo</Text>
            </View>
            <Text style={styles.cardDescription}>
              Interactive demonstration of sensor fusion and violation detection algorithms. Test
              individual configurations and see real-time results.
            </Text>
            <View style={styles.cardFeatures}>
              <Text style={styles.feature}>• Interactive parameter testing</Text>
              <Text style={styles.feature}>• Real-time metrics display</Text>
              <Text style={styles.feature}>• Configuration comparison</Text>
            </View>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.demoCard, styles.validationDemo]}
            onPress={() => setCurrentMode('validation_demo')}
          >
            <View style={styles.cardHeader}>
              <Text style={styles.cardIcon}>🏆</Text>
              <Text style={styles.cardTitle}>Comprehensive Validation Demo</Text>
            </View>
            <Text style={styles.cardDescription}>
              Complete validation workflow demonstrating algorithm improvements. Includes
              before/after analysis and presentation-ready reports.
            </Text>
            <View style={styles.cardFeatures}>
              <Text style={styles.feature}>• Full algorithm validation</Text>
              <Text style={styles.feature}>• Before/after comparison</Text>
              <Text style={styles.feature}>• Executive summary reports</Text>
              <Text style={styles.feature}>• Presentation slides</Text>
            </View>
          </TouchableOpacity>
        </View>

        <View style={styles.infoSection}>
          <Text style={styles.infoTitle}>📋 Testing Coverage</Text>
          <View style={styles.infoGrid}>
            <View style={styles.infoItem}>
              <Text style={styles.infoLabel}>Issues Fixed</Text>
              <Text style={styles.infoValue}>6/6</Text>
            </View>
            <View style={styles.infoItem}>
              <Text style={styles.infoLabel}>Test Configurations</Text>
              <Text style={styles.infoValue}>Multiple</Text>
            </View>
            <View style={styles.infoItem}>
              <Text style={styles.infoLabel}>Dataset Sessions</Text>
              <Text style={styles.infoValue}>10 sessions</Text>
            </View>
            <View style={styles.infoItem}>
              <Text style={styles.infoLabel}>Validation Metrics</Text>
              <Text style={styles.infoValue}>8+ metrics</Text>
            </View>
          </View>
        </View>

        <View style={styles.technicalDetails}>
          <Text style={styles.technicalTitle}>🔧 Algorithm Improvements</Text>
          <Text style={styles.technicalText}>
            ✅ Device orientation handling{'\n'}✅ Dynamic axis detection{'\n'}✅ Extended
            calibration period{'\n'}✅ Improved quality thresholds{'\n'}✅ Optimized violation
            detection{'\n'}✅ Enhanced gravity compensation
          </Text>
        </View>
      </View>

      <View style={styles.footer}>
        <Text style={styles.footerText}>
          Driver behavior detection algorithm validation and testing framework
        </Text>
        <Text style={styles.footerSubtext}>Ready for production deployment and demonstration</Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
  },
  header: {
    backgroundColor: '#1e40af',
    paddingTop: 50,
    paddingBottom: 30,
    paddingHorizontal: 20,
  },
  title: {
    fontSize: 26,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 8,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 16,
    color: '#bfdbfe',
    textAlign: 'center',
  },
  content: {
    flex: 1,
    padding: 20,
  },
  section: {
    marginBottom: 25,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1f2937',
    marginBottom: 15,
    textAlign: 'center',
  },
  demoCard: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 20,
    marginBottom: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
    borderLeftWidth: 4,
  },
  basicDemo: {
    borderLeftColor: '#10b981',
  },
  validationDemo: {
    borderLeftColor: '#f59e0b',
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  cardIcon: {
    fontSize: 24,
    marginRight: 12,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1f2937',
    flex: 1,
  },
  cardDescription: {
    fontSize: 14,
    color: '#6b7280',
    lineHeight: 20,
    marginBottom: 12,
  },
  cardFeatures: {
    paddingLeft: 10,
  },
  feature: {
    fontSize: 13,
    color: '#374151',
    marginBottom: 4,
  },
  infoSection: {
    backgroundColor: 'white',
    borderRadius: 8,
    padding: 20,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
  },
  infoTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1f2937',
    marginBottom: 15,
    textAlign: 'center',
  },
  infoGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  infoItem: {
    width: '48%',
    backgroundColor: '#f9fafb',
    padding: 12,
    borderRadius: 6,
    marginBottom: 8,
    alignItems: 'center',
  },
  infoLabel: {
    fontSize: 12,
    color: '#6b7280',
    marginBottom: 4,
  },
  infoValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1e40af',
  },
  technicalDetails: {
    backgroundColor: '#ecfdf5',
    borderRadius: 8,
    padding: 20,
    borderColor: '#10b981',
    borderWidth: 1,
  },
  technicalTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#065f46',
    marginBottom: 10,
    textAlign: 'center',
  },
  technicalText: {
    fontSize: 14,
    color: '#047857',
    lineHeight: 22,
  },
  footer: {
    padding: 20,
    alignItems: 'center',
    backgroundColor: 'white',
    borderTopWidth: 1,
    borderTopColor: '#e5e7eb',
  },
  footerText: {
    fontSize: 14,
    color: '#6b7280',
    textAlign: 'center',
    marginBottom: 4,
  },
  footerSubtext: {
    fontSize: 12,
    color: '#9ca3af',
    textAlign: 'center',
  },
});
