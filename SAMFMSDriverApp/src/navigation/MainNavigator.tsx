import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createStackNavigator } from '@react-navigation/stack';
import { Home, Settings, User, HelpCircle } from 'lucide-react-native';
import { useColorScheme } from 'react-native';

import DashboardScreen from '../screens/DashboardScreen';
import SettingsScreen from '../screens/SettingsScreen';
import AccountScreen from '../screens/AccountScreen';
import HelpScreen from '../screens/HelpScreen';
import TripDetailsScreen from '../screens/TripDetailsScreen';
import ActiveTripScreen from '../screens/ActiveTripScreen';
import BehaviorMonitoringScreen from '../screens/BehaviorMonitoringScreen';
import SwipeNavigationWrapper from '../components/SwipeNavigationWrapper';

const Tab = createBottomTabNavigator();
const Stack = createStackNavigator();

// Stack navigator for Dashboard tab
function DashboardStack() {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="DashboardHome" component={DashboardScreen} />
      <Stack.Screen name="TripDetails" component={TripDetailsScreen} />
      <Stack.Screen name="ActiveTrip" component={ActiveTripScreen} />
      <Stack.Screen name="BehaviorMonitoring" component={BehaviorMonitoringScreen} />
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

export default function MainNavigator() {
  const isDarkMode = useColorScheme() === 'dark';

  const theme = {
    tabBarActiveTintColor: '#3b82f6',
    tabBarInactiveTintColor: isDarkMode ? '#94a3b8' : '#64748b',
    tabBarStyle: {
      backgroundColor: isDarkMode ? '#1e293b' : '#ffffff',
      borderTopColor: isDarkMode ? '#334155' : '#e2e8f0',
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
    <NavigationContainer>
      <SwipeNavigationWrapper>
        <Tab.Navigator
          screenOptions={({ route }) => ({
            tabBarIcon: getTabBarIcon(route.name),
            tabBarActiveTintColor: theme.tabBarActiveTintColor,
            tabBarInactiveTintColor: theme.tabBarInactiveTintColor,
            tabBarStyle: theme.tabBarStyle,
            headerShown: false,
          })}
        >
          <Tab.Screen name="Dashboard" component={DashboardStack} />
          <Tab.Screen name="Account" component={AccountScreen} />
          <Tab.Screen name="Settings" component={SettingsScreen} />
          <Tab.Screen name="Help" component={HelpScreen} />
        </Tab.Navigator>
      </SwipeNavigationWrapper>
    </NavigationContainer>
  );
}
