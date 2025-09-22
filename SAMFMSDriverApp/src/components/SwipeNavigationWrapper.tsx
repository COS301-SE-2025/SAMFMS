import React, { ReactNode } from 'react';
import { View, PanResponder, Dimensions, StyleSheet } from 'react-native';
import { useNavigation } from '@react-navigation/native';

interface SwipeNavigationWrapperProps {
  children: ReactNode;
}

const SwipeNavigationWrapper: React.FC<SwipeNavigationWrapperProps> = ({ children }) => {
  const navigation = useNavigation();
  const screenWidth = Dimensions.get('window').width;

  // Define the tab order for swipe navigation
  const tabOrder = ['Dashboard', 'Account', 'Settings', 'Help'];

  // Check if we're on a screen where swipe should be disabled
  const shouldDisableSwipe = () => {
    try {
      const navState = navigation.getState();
      if (navState && navState.routes) {
        const currentRoute = navState.routes[navState.index];
        // Check if we're in a stack navigator and the current screen is TripDetails
        if (
          currentRoute.state &&
          currentRoute.state.routes &&
          currentRoute.state.index !== undefined
        ) {
          const stackRoute = currentRoute.state.routes[currentRoute.state.index];
          return stackRoute.name === 'TripDetails';
        }
      }
    } catch (error) {
      console.warn('Error checking navigation state:', error);
    }
    return false;
  };

  const panResponder = PanResponder.create({
    onMoveShouldSetPanResponder: (evt, gestureState) => {
      // Disable swipe on TripDetails screen
      if (shouldDisableSwipe()) {
        return false;
      }
      // Return true if user is making a horizontal swipe
      return (
        Math.abs(gestureState.dx) > Math.abs(gestureState.dy) && Math.abs(gestureState.dx) > 10
      );
    },
    onPanResponderMove: () => {
      // Optional: Add visual feedback during swipe
    },
    onPanResponderRelease: (evt, gestureState) => {
      const swipeThreshold = screenWidth * 0.25; // 25% of screen width
      const navState = navigation.getState();

      if (navState && navState.routes && navState.routes[navState.index]) {
        const currentRouteName = navState.routes[navState.index].name;
        const currentIndex = tabOrder.indexOf(currentRouteName);

        if (gestureState.dx > swipeThreshold && currentIndex > 0) {
          // Swipe right - go to previous tab
          const previousTab = tabOrder[currentIndex - 1];
          navigation.navigate(previousTab as never);
        } else if (gestureState.dx < -swipeThreshold && currentIndex < tabOrder.length - 1) {
          // Swipe left - go to next tab
          const nextTab = tabOrder[currentIndex + 1];
          navigation.navigate(nextTab as never);
        }
      }
    },
  });

  return (
    <View style={styles.container} {...panResponder.panHandlers}>
      {children}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
});

export default SwipeNavigationWrapper;
