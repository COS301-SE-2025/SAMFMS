/**
 * SAMFMS Driver App
 * Smart Automotive Fleet Management System
 * by Firewall Five
 *
 * @format
 */

import React, { useState, useEffect, useMemo } from 'react';
import {
  StatusBar,
  StyleSheet,
  useColorScheme,
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  Dimensions,
  Animated,
} from 'react-native';
import { SafeAreaProvider, useSafeAreaInsets } from 'react-native-safe-area-context';
import SamfmsLogo from './src/components/SamfmsLogo';
import LoginModal from './src/components/LoginModal';
import MainNavigator from './src/navigation/MainNavigator';
import { AuthProvider, useAuth } from './src/contexts/AuthContext';

const { width } = Dimensions.get('window');

function AppContent() {
  const isDarkMode = useColorScheme() === 'dark';
  const { isLoggedIn, login } = useAuth();

  if (isLoggedIn) {
    return (
      <SafeAreaProvider>
        <StatusBar
          barStyle={isDarkMode ? 'light-content' : 'dark-content'}
          backgroundColor={isDarkMode ? '#0f172a' : '#f8fafc'}
        />
        <MainNavigator />
      </SafeAreaProvider>
    );
  }

  return (
    <SafeAreaProvider>
      <StatusBar
        barStyle={isDarkMode ? 'light-content' : 'dark-content'}
        backgroundColor={isDarkMode ? '#0f172a' : '#f8fafc'}
      />
      <SAMFMSLanding onLoginSuccess={login} />
    </SafeAreaProvider>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

function SAMFMSLanding({ onLoginSuccess }: { onLoginSuccess: () => void }) {
  const safeAreaInsets = useSafeAreaInsets();
  const isDarkMode = useColorScheme() === 'dark';
  const [currentSlogan, setCurrentSlogan] = useState(0);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const fadeAnim = useMemo(() => new Animated.Value(1), []);

  const slogans = [
    'Smart Fleet Management',
    'Optimize Vehicle Operations',
    'Track Assets in Real-time',
    'Streamline Operations',
  ];

  const features = [
    {
      icon: '🚗',
      title: 'Vehicle Tracking',
      description: 'Real-time GPS tracking and route optimization',
    },
    {
      icon: '🛡️',
      title: 'Security & Safety',
      description: 'Advanced security features and driver monitoring',
    },
    {
      icon: '📊',
      title: 'Analytics & Reports',
      description: 'Comprehensive analytics for data-driven decisions',
    },
    {
      icon: '⚡',
      title: 'Smart Automation',
      description: 'Automated maintenance and intelligent alerts',
    },
  ];

  useEffect(() => {
    const interval = setInterval(() => {
      Animated.sequence([
        Animated.timing(fadeAnim, {
          toValue: 0,
          duration: 500,
          useNativeDriver: true,
        }),
        Animated.timing(fadeAnim, {
          toValue: 1,
          duration: 500,
          useNativeDriver: true,
        }),
      ]).start();

      setCurrentSlogan(prev => (prev + 1) % slogans.length);
    }, 4000);

    return () => clearInterval(interval);
  }, [fadeAnim, slogans.length]);

  const theme = {
    background: isDarkMode ? '#0f172a' : '#f8fafc',
    cardBackground: isDarkMode ? '#1e293b' : '#ffffff',
    text: isDarkMode ? '#f1f5f9' : '#1e293b',
    textSecondary: isDarkMode ? '#94a3b8' : '#64748b',
    accent: '#3b82f6',
    accentHover: '#2563eb',
    border: isDarkMode ? '#334155' : '#e2e8f0',
  };

  return (
    <View style={[styles.container, { backgroundColor: theme.background }]}>
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={{ paddingTop: safeAreaInsets.top }}
        showsVerticalScrollIndicator={false}
      >
        {/* Header Section */}
        <View style={styles.header}>
          <View style={styles.logoContainer}>
            <View style={styles.logoPlaceholder}>
              <SamfmsLogo width={250} height={75} />
            </View>
            <Text style={[styles.companyText, { color: theme.textSecondary }]}>
              by Firewall Five
            </Text>
          </View>
        </View>

        {/* Hero Section */}
        <View style={styles.heroSection}>
          <Animated.View style={[styles.sloganContainer, { opacity: fadeAnim }]}>
            <Text style={[styles.heroTitle, { color: theme.text }]}>{slogans[currentSlogan]}</Text>
          </Animated.View>

          <Text style={[styles.heroSubtitle, { color: theme.textSecondary }]}>
            Streamline your fleet operations, optimize vehicle maintenance, and track your assets
            with our comprehensive management system.
          </Text>

          <TouchableOpacity
            style={[styles.primaryButton, { backgroundColor: theme.accent }]}
            onPress={() => setShowLoginModal(true)}
          >
            <Text style={styles.buttonText}>Login</Text>
          </TouchableOpacity>

          <View style={styles.secondaryButtons}>
            <TouchableOpacity style={[styles.secondaryButton, { borderColor: theme.border }]}>
              <Text style={[styles.secondaryButtonText, { color: theme.text }]}>📖 User Guide</Text>
            </TouchableOpacity>
            <TouchableOpacity style={[styles.secondaryButton, { borderColor: theme.border }]}>
              <Text style={[styles.secondaryButtonText, { color: theme.text }]}>🔗 GitHub</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Features Grid */}
        <View style={styles.featuresSection}>
          <Text style={[styles.sectionTitle, { color: theme.text }]}>Key Features</Text>

          <View style={styles.featuresGrid}>
            {features.map((feature, index) => (
              <View
                key={index}
                style={[
                  styles.featureCard,
                  {
                    backgroundColor: theme.cardBackground,
                    borderColor: theme.border,
                  },
                ]}
              >
                <Text style={styles.featureIcon}>{feature.icon}</Text>
                <Text style={[styles.featureTitle, { color: theme.text }]}>{feature.title}</Text>
                <Text style={[styles.featureDescription, { color: theme.textSecondary }]}>
                  {feature.description}
                </Text>
              </View>
            ))}
          </View>
        </View>

        {/* Stats Section */}
        <View style={styles.statsSection}>
          <Text style={[styles.sectionTitle, { color: theme.text }]}>Why Choose SAMFMS?</Text>

          <View style={styles.statsGrid}>
            <View
              style={[
                styles.statCard,
                { backgroundColor: theme.cardBackground, borderColor: theme.border },
              ]}
            >
              <Text style={[styles.statNumber, { color: theme.accent }]}>99.9%</Text>
              <Text style={[styles.statLabel, { color: theme.textSecondary }]}>Uptime</Text>
            </View>
            <View
              style={[
                styles.statCard,
                { backgroundColor: theme.cardBackground, borderColor: theme.border },
              ]}
            >
              <Text style={[styles.statNumber, { color: theme.accent }]}>Real-time</Text>
              <Text style={[styles.statLabel, { color: theme.textSecondary }]}>Tracking</Text>
            </View>
            <View
              style={[
                styles.statCard,
                { backgroundColor: theme.cardBackground, borderColor: theme.border },
              ]}
            >
              <Text style={[styles.statNumber, { color: theme.accent }]}>24/7</Text>
              <Text style={[styles.statLabel, { color: theme.textSecondary }]}>Support</Text>
            </View>
          </View>
        </View>

        {/* Footer */}
        <View style={styles.footer}>
          <Text style={[styles.footerText, { color: theme.textSecondary }]}>
            © 2025 SAMFMS by Firewall Five. All rights reserved.
          </Text>
        </View>
      </ScrollView>

      {/* Login Modal */}
      <LoginModal
        visible={showLoginModal}
        onClose={() => setShowLoginModal(false)}
        onSuccess={() => {
          setShowLoginModal(false);
          onLoginSuccess();
        }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollView: {
    flex: 1,
  },
  header: {
    paddingHorizontal: 20,
    paddingVertical: 20,
  },
  logoContainer: {
    alignItems: 'center',
  },
  logoPlaceholder: {
    width: 120,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
  },
  logoText: {
    fontSize: 28,
    fontWeight: 'bold',
    letterSpacing: 2,
  },
  companyText: {
    fontSize: 14,
    fontStyle: 'italic',
  },
  heroSection: {
    paddingHorizontal: 20,
    paddingVertical: 40,
    alignItems: 'center',
  },
  sloganContainer: {
    marginBottom: 20,
  },
  heroTitle: {
    fontSize: 32,
    fontWeight: 'bold',
    textAlign: 'center',
    lineHeight: 40,
  },
  heroSubtitle: {
    fontSize: 16,
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: 40,
    paddingHorizontal: 10,
  },
  primaryButton: {
    paddingHorizontal: 40,
    paddingVertical: 16,
    borderRadius: 12,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  buttonText: {
    color: '#ffffff',
    fontSize: 18,
    fontWeight: '600',
  },
  secondaryButtons: {
    flexDirection: 'row',
    gap: 15,
  },
  secondaryButton: {
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 8,
    borderWidth: 1,
  },
  secondaryButtonText: {
    fontSize: 14,
    fontWeight: '500',
  },
  featuresSection: {
    paddingHorizontal: 20,
    paddingVertical: 40,
  },
  sectionTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 30,
  },
  featuresGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    gap: 15,
  },
  featureCard: {
    width: (width - 55) / 2,
    padding: 20,
    borderRadius: 12,
    borderWidth: 1,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  featureIcon: {
    fontSize: 32,
    marginBottom: 12,
  },
  featureTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 8,
    textAlign: 'center',
  },
  featureDescription: {
    fontSize: 12,
    textAlign: 'center',
    lineHeight: 16,
  },
  statsSection: {
    paddingHorizontal: 20,
    paddingVertical: 40,
  },
  statsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 15,
  },
  statCard: {
    flex: 1,
    padding: 20,
    borderRadius: 12,
    borderWidth: 1,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  statNumber: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 12,
    textAlign: 'center',
  },
  footer: {
    paddingHorizontal: 20,
    paddingVertical: 30,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 12,
    textAlign: 'center',
  },
});

export default App;
