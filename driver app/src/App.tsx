import React from 'react';
import {NavigationContainer} from '@react-navigation/native';
import {createStackNavigator} from '@react-navigation/stack';
import {Provider as PaperProvider} from 'react-native-paper';
import {SafeAreaProvider} from 'react-native-safe-area-context';

import LoginScreen from './screens/LoginScreen';
import MainTabNavigator from './navigation/MainTabNavigator';
import VehicleInspectionScreen from './screens/VehicleInspectionScreen';
import TripDetailsScreen from './screens/TripDetailsScreen';
import MaintenanceReportScreen from './screens/MaintenanceReportScreen';
import {AuthProvider} from './context/AuthContext';
import {theme} from './theme/theme';

const Stack = createStackNavigator();

const App = () => {
  return (
    <SafeAreaProvider>
      <PaperProvider theme={theme}>
        <AuthProvider>
          <NavigationContainer>
            <Stack.Navigator
              initialRouteName="Login"
              screenOptions={{
                headerStyle: {
                  backgroundColor: theme.colors.primary,
                },
                headerTintColor: '#fff',
                headerTitleStyle: {
                  fontWeight: 'bold',
                },
              }}>
              <Stack.Screen 
                name="Login" 
                component={LoginScreen} 
                options={{headerShown: false}}
              />
              <Stack.Screen 
                name="Main" 
                component={MainTabNavigator} 
                options={{headerShown: false}}
              />
              <Stack.Screen 
                name="VehicleInspection" 
                component={VehicleInspectionScreen}
                options={{title: 'Vehicle Inspection'}}
              />
              <Stack.Screen 
                name="TripDetails" 
                component={TripDetailsScreen}
                options={{title: 'Trip Details'}}
              />
              <Stack.Screen 
                name="MaintenanceReport" 
                component={MaintenanceReportScreen}
                options={{title: 'Report Issue'}}
              />
            </Stack.Navigator>
          </NavigationContainer>
        </AuthProvider>
      </PaperProvider>
    </SafeAreaProvider>
  );
};

export default App;
