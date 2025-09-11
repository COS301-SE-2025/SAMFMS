import React, { useEffect } from 'react';
import { useActiveTripContext } from '../contexts/ActiveTripContext';
import { useNavigation } from '@react-navigation/native';

interface ActiveTripGuardProps {
  children: React.ReactNode;
  allowActiveTrip?: boolean; // If true, doesn't redirect when there's an active trip
}

/**
 * Component that automatically redirects to active trip screen when there's an active trip
 * Wrap any screen that should redirect when there's an active trip
 */
export const ActiveTripGuard: React.FC<ActiveTripGuardProps> = ({
  children,
  allowActiveTrip = false,
}) => {
  const { hasActiveTrip, activeTrip, checkForActiveTrip } = useActiveTripContext();
  const navigation = useNavigation();

  useEffect(() => {
    if (!allowActiveTrip && hasActiveTrip && activeTrip) {
      console.log('ActiveTripGuard: Redirecting to active trip screen');

      // Get current route to avoid unnecessary navigation
      const currentRoute = navigation
        .getState()
        ?.routes?.find(route => route.state?.index !== undefined)?.state?.routes[
        navigation.getState()?.routes?.find(route => route.state?.index !== undefined)?.state
          ?.index || 0
      ]?.name;

      if (currentRoute !== 'ActiveTrip') {
        // Use a timeout to ensure navigation state is stable
        setTimeout(() => {
          try {
            (navigation as any).navigate('Dashboard', {
              screen: 'ActiveTrip',
            });
          } catch (navError) {
            console.error('ActiveTripGuard navigation error:', navError);
            // Fallback navigation
            try {
              (navigation as any).navigate('ActiveTrip');
            } catch (fallbackError) {
              console.error('ActiveTripGuard fallback navigation error:', fallbackError);
            }
          }
        }, 100);
      }
    }
  }, [hasActiveTrip, activeTrip, allowActiveTrip, navigation]);

  // Check for active trips when component mounts
  useEffect(() => {
    checkForActiveTrip();
  }, [checkForActiveTrip]);

  return <>{children}</>;
};

export default ActiveTripGuard;
