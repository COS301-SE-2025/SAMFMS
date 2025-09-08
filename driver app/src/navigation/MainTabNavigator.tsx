import React from 'react';
import {createBottomTabNavigator} from '@react-navigation/bottom-tabs';
import Icon from 'react-native-vector-icons/MaterialIcons';

import DashboardScreen from '../screens/DashboardScreen';
import TripScreen from '../screens/TripScreen';
import VehicleScreen from '../screens/VehicleScreen';
import ProfileScreen from '../screens/ProfileScreen';
import {theme} from '../theme/theme';

const Tab = createBottomTabNavigator();

const MainTabNavigator = () => {
  return (
    <Tab.Navigator
      screenOptions={({route}) => ({
        tabBarIcon: ({focused, color, size}) => {
          let iconName = '';

          switch (route.name) {
            case 'Dashboard':
              iconName = 'dashboard';
              break;
            case 'Trips':
              iconName = 'directions-car';
              break;
            case 'Vehicle':
              iconName = 'build';
              break;
            case 'Profile':
              iconName = 'person';
              break;
          }

          return <Icon name={iconName} size={size} color={color} />;
        },
        tabBarActiveTintColor: theme.colors.primary,
        tabBarInactiveTintColor: 'gray',
        headerStyle: {
          backgroundColor: theme.colors.primary,
        },
        headerTintColor: '#fff',
        headerTitleStyle: {
          fontWeight: 'bold',
        },
      })}>
      <Tab.Screen 
        name="Dashboard" 
        component={DashboardScreen}
        options={{title: 'Dashboard'}}
      />
      <Tab.Screen 
        name="Trips" 
        component={TripScreen}
        options={{title: 'My Trips'}}
      />
      <Tab.Screen 
        name="Vehicle" 
        component={VehicleScreen}
        options={{title: 'Vehicle'}}
      />
      <Tab.Screen 
        name="Profile" 
        component={ProfileScreen}
        options={{title: 'Profile'}}
      />
    </Tab.Navigator>
  );
};

export default MainTabNavigator;
