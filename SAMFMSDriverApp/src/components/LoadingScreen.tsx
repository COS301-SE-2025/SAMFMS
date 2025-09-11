import React from 'react';
import { View, Text, ActivityIndicator, StyleSheet, useColorScheme } from 'react-native';
import SamfmsLogo from './SamfmsLogo';

interface LoadingScreenProps {
  message?: string;
}

const LoadingScreen: React.FC<LoadingScreenProps> = ({ message = 'Loading...' }) => {
  const isDarkMode = useColorScheme() === 'dark';

  const theme = {
    background: isDarkMode ? '#0f172a' : '#f8fafc',
    text: isDarkMode ? '#f1f5f9' : '#1e293b',
    accent: '#3b82f6',
  };

  return (
    <View style={[styles.container, { backgroundColor: theme.background }]}>
      <SamfmsLogo width={200} height={60} />
      <ActivityIndicator size="large" color={theme.accent} style={styles.spinner} />
      <Text style={[styles.loadingText, { color: theme.text }]}>{message}</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  spinner: {
    marginTop: 30,
    marginBottom: 20,
  },
  loadingText: {
    fontSize: 18,
    fontWeight: '600',
  },
});

export default LoadingScreen;
