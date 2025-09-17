import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createStackNavigator } from '@react-navigation/stack';
import { Home, Settings, User, HelpCircle } from 'lucide-react-native';
import { useTheme } from '../contexts/ThemeContext';
import { useActiveTripContext } from '../contexts/ActiveTripContext';

import DashboardScreen from '../screens/DashboardScreen';
import SettingsScreen from '../screens/SettingsScreen';
import AccelerometerSettingsScreen from '../screens/AccelerometerSettingsScreen';
import AccountScreen from '../screens/AccountScreen';
import HelpScreen from '../screens/HelpScreen';
import TripDetailsScreen from '../screens/TripDetailsScreen';
import ActiveTripScreen from '../screens/ActiveTripScreen';
import SwipeNavigationWrapper from '../components/SwipeNavigationWrapper';
import { ActiveTripProvider } from '../contexts/ActiveTripContext';

const Tab = createBottomTabNavigator();
const Stack = createStackNavigator();

// Stack navigator for Dashboard tab
function DashboardStack() {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="DashboardHome" component={DashboardScreen} />
      <Stack.Screen name="TripDetails" component={TripDetailsScreen} />
      <Stack.Screen name="ActiveTrip" component={ActiveTripScreen} />
    </Stack.Navigator>
  );
}

// Stack navigator for Settings tab
function SettingsStack() {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="SettingsHome" component={SettingsScreen} />
      <Stack.Screen name="AccelerometerSettings" component={AccelerometerSettingsScreen} />
    </Stack.Navigator>
  );
}

// Icon components defined outside render to avoid recreation
const DashboardIcon = ({ color, size }: { color: string; size: number }) => (
  <Home color={color} size={size} />
);

const AccountIcon = ({ color, size }: { color: string; size: number }) => (
  <User color={color} size={size} />
);

const SettingsIcon = ({ color, size }: { color: string; size: number }) => (
  <Settings color={color} size={size} />
);

const HelpIcon = ({ color, size }: { color: string; size: number }) => (
  <HelpCircle color={color} size={size} />
);

// Main tab navigator component that can access ActiveTripContext
function TabNavigator() {
  const { theme } = useTheme();
  const { hasActiveTrip } = useActiveTripContext();

  const tabBarTheme = {
    tabBarActiveTintColor: theme.accent,
    tabBarInactiveTintColor: theme.textSecondary,
    tabBarStyle: hasActiveTrip
      ? { display: 'none' as const }
      : {
          backgroundColor: theme.cardBackground,
          borderTopColor: theme.border,
        },
  };

  const getTabBarIcon = (routeName: string) => {
    switch (routeName) {
      case 'Dashboard':
        return DashboardIcon;
      case 'Account':
        return AccountIcon;
      case 'Settings':
        return SettingsIcon;
      case 'Help':
        return HelpIcon;
      default:
        return DashboardIcon;
    }
  };

  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: getTabBarIcon(route.name),
        tabBarActiveTintColor: tabBarTheme.tabBarActiveTintColor,
        tabBarInactiveTintColor: tabBarTheme.tabBarInactiveTintColor,
        tabBarStyle: tabBarTheme.tabBarStyle,
        headerShown: false,
      })}
    >
      <Tab.Screen name="Dashboard" component={DashboardStack} />
      <Tab.Screen name="Account" component={AccountScreen} />
      <Tab.Screen name="Settings" component={SettingsStack} />
      <Tab.Screen name="Help" component={HelpScreen} />
    </Tab.Navigator>
  );
}

export default function MainNavigator() {
  return (
    <NavigationContainer>
      <ActiveTripProvider>
        <SwipeNavigationWrapper>
          <TabNavigator />
        </SwipeNavigationWrapper>
      </ActiveTripProvider>
    </NavigationContainer>
  );
}
