import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useColorScheme, Appearance } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

type ThemeMode = 'light' | 'dark' | 'system';

interface Theme {
  // Background colors
  background: string;
  cardBackground: string;
  surfaceBackground: string;

  // Text colors
  text: string;
  textSecondary: string;
  textTertiary: string;
  textInverse: string;

  // Border and divider colors
  border: string;
  divider: string;

  // Accent and action colors
  accent: string;
  accentSecondary: string;

  // Status colors
  success: string;
  warning: string;
  danger: string;
  info: string;

  // Shadow and overlay colors
  shadow: string;
  overlay: string;

  // Navigation colors
  tabBarBackground: string;
  tabBarActive: string;
  tabBarInactive: string;

  // Input colors
  inputBackground: string;
  inputBorder: string;
  inputPlaceholder: string;

  // Button colors
  buttonPrimary: string;
  buttonSecondary: string;
  buttonDisabled: string;
}

interface ThemeContextType {
  theme: Theme;
  themeMode: ThemeMode;
  setThemeMode: (mode: ThemeMode) => void;
  isDarkMode: boolean;
}

const lightTheme: Theme = {
  // Background colors
  background: '#f8fafc',
  cardBackground: '#ffffff',
  surfaceBackground: '#f1f5f9',

  // Text colors
  text: '#1e293b',
  textSecondary: '#64748b',
  textTertiary: '#94a3b8',
  textInverse: '#ffffff',

  // Border and divider colors
  border: '#e2e8f0',
  divider: '#f1f5f9',

  // Accent and action colors
  accent: '#6366f1',
  accentSecondary: '#3b82f6',

  // Status colors
  success: '#10b981',
  warning: '#f59e0b',
  danger: '#dc2626',
  info: '#3b82f6',

  // Shadow and overlay colors
  shadow: '#64748b',
  overlay: 'rgba(0, 0, 0, 0.5)',

  // Navigation colors
  tabBarBackground: '#ffffff',
  tabBarActive: '#6366f1',
  tabBarInactive: '#94a3b8',

  // Input colors
  inputBackground: '#ffffff',
  inputBorder: '#d1d5db',
  inputPlaceholder: '#9ca3af',

  // Button colors
  buttonPrimary: '#6366f1',
  buttonSecondary: '#e5e7eb',
  buttonDisabled: '#d1d5db',
};

const darkTheme: Theme = {
  // Background colors
  background: '#0f0f23',
  cardBackground: '#1a1a2e',
  surfaceBackground: '#16213e',

  // Text colors
  text: '#f1f5f9',
  textSecondary: '#94a3b8',
  textTertiary: '#64748b',
  textInverse: '#1e293b',

  // Border and divider colors
  border: '#334155',
  divider: '#1e293b',

  // Accent and action colors
  accent: '#6366f1',
  accentSecondary: '#3b82f6',

  // Status colors
  success: '#10b981',
  warning: '#f59e0b',
  danger: '#dc2626',
  info: '#3b82f6',

  // Shadow and overlay colors
  shadow: '#000000',
  overlay: 'rgba(0, 0, 0, 0.7)',

  // Navigation colors
  tabBarBackground: '#1a1a2e',
  tabBarActive: '#6366f1',
  tabBarInactive: '#64748b',

  // Input colors
  inputBackground: '#1e293b',
  inputBorder: '#374151',
  inputPlaceholder: '#6b7280',

  // Button colors
  buttonPrimary: '#6366f1',
  buttonSecondary: '#374151',
  buttonDisabled: '#4b5563',
};

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

const THEME_STORAGE_KEY = '@theme_mode';

interface ThemeProviderProps {
  children: ReactNode;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  const systemColorScheme = useColorScheme();
  const [themeMode, setThemeModeState] = useState<ThemeMode>('system');

  // Determine if we should use dark mode
  const isDarkMode =
    themeMode === 'dark' || (themeMode === 'system' && systemColorScheme === 'dark');

  // Select the appropriate theme
  const theme = isDarkMode ? darkTheme : lightTheme;

  // Load saved theme preference
  useEffect(() => {
    const loadThemeMode = async () => {
      try {
        const savedThemeMode = await AsyncStorage.getItem(THEME_STORAGE_KEY);
        if (savedThemeMode && ['light', 'dark', 'system'].includes(savedThemeMode)) {
          setThemeModeState(savedThemeMode as ThemeMode);
        }
      } catch (error) {
        console.error('Error loading theme mode:', error);
      }
    };

    loadThemeMode();
  }, []);

  // Save theme preference when it changes
  const setThemeMode = async (mode: ThemeMode) => {
    try {
      setThemeModeState(mode);
      await AsyncStorage.setItem(THEME_STORAGE_KEY, mode);
    } catch (error) {
      console.error('Error saving theme mode:', error);
    }
  };

  // Listen for system theme changes when in system mode
  useEffect(() => {
    if (themeMode === 'system') {
      const subscription = Appearance.addChangeListener(() => {
        // Force re-render when system theme changes
        // The context will automatically update based on the new systemColorScheme
      });

      return () => subscription?.remove();
    }
  }, [themeMode]);

  const value: ThemeContextType = {
    theme,
    themeMode,
    setThemeMode,
    isDarkMode,
  };

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
};

export const useTheme = (): ThemeContextType => {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

export type { Theme, ThemeMode };
