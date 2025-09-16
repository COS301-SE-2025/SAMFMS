import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { View, StyleSheet, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { finishTrip, pauseTrip, resumeTrip, cancelTrip, completeTrip } from '../utils/api';
import { useActiveTripContext } from '../contexts/ActiveTripContext';
import { useTheme } from '../contexts/ThemeContext';

// Import new components and hooks
import { TripHeader, DirectionsCard, TripMap, TripControls } from '../components/trip';
import { useLocationTracking, useSpeedLimitTracking, useVehicleData } from '../hooks';

interface ActiveTripScreenProps {
  navigation: {
    goBack: () => void;
    navigate: (screen: string, params?: any) => void;
  };
}

const ActiveTripScreen: React.FC<ActiveTripScreenProps> = ({ navigation }) => {
  // Use the ActiveTripContext instead of local state
  const { activeTrip, isCheckingActiveTrip, error, clearActiveTrip } = useActiveTripContext();

  // Keep local state for screen-specific functionality
  const [endingTrip, setEndingTrip] = useState(false);
  const [canEndTrip, _setCanEndTrip] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [pausingTrip, setPausingTrip] = useState(false);
  const [cancelingTrip, setCancelingTrip] = useState(false);
  const [statusCheckInterval, setStatusCheckInterval] = useState<ReturnType<
    typeof setInterval
  > | null>(null);

  // Determine if back button should be visible (when trip is paused or cancelled)
  const shouldShowBackButton = isPaused || activeTrip?.status === 'cancelled';

  // Turn-by-turn directions state
  const [directions, setDirections] = useState<any[]>([]);
  const [currentDirectionIndex, setCurrentDirectionIndex] = useState<number>(0);
  const [_nextDirection, setNextDirection] = useState<any | null>(null);

  const { theme } = useTheme();

  // Use custom hooks
  const { currentLocation, currentSpeed, startLocationPing, stopLocationPing } =
    useLocationTracking();
  const { speedLimit, stopSpeedLimitChecking } = useSpeedLimitTracking();
  const {
    isWebViewLoaded,
    liveInstruction,
    liveInstructionDistance,
    liveSpeed,
    liveSpeedLimit,
    currentRoadName,
    setIsWebViewLoaded,
    fetchVehicleData,
    handleWebViewLoad,
    webViewRef,
  } = useVehicleData(activeTrip, currentSpeed, directions, currentDirectionIndex);

  // Calculate distance between two coordinates in meters using Haversine formula
  const calculateDistance = useCallback(
    (lat1: number, lon1: number, lat2: number, lon2: number): number => {
      const R = 6371e3; // Earth's radius in meters
      const φ1 = (lat1 * Math.PI) / 180; // φ, λ in radians
      const φ2 = (lat2 * Math.PI) / 180;
      const Δφ = ((lat2 - lat1) * Math.PI) / 180;
      const Δλ = ((lon2 - lon1) * Math.PI) / 180;

      const a =
        Math.sin(Δφ / 2) * Math.sin(Δφ / 2) +
        Math.cos(φ1) * Math.cos(φ2) * Math.sin(Δλ / 2) * Math.sin(Δλ / 2);
      const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

      return R * c; // Distance in meters
    },
    []
  );

  // Check if driver is within 250m of destination
  const isNearDestination = useMemo(() => {
    if (!currentLocation || !activeTrip?.destination?.location?.coordinates) {
      return false;
    }

    const destCoords = activeTrip.destination.location.coordinates;

    const distance = calculateDistance(
      currentLocation.latitude,
      currentLocation.longitude,
      destCoords[1], // destination latitude (GeoJSON: [lng, lat])
      destCoords[0] // destination longitude (GeoJSON: [lng, lat])
    );

    const isNear = distance <= 10000; // Temporarily 10km for testing

    return isNear;
  }, [currentLocation, activeTrip?.destination?.location?.coordinates, calculateDistance]);

  // Extract turn-by-turn directions from raw route response
  const extractDirections = useCallback(() => {
    if (!activeTrip?.raw_route_response) {
      setDirections([]);
      setCurrentDirectionIndex(0);
      setNextDirection(null);
      return;
    }

    try {
      const routeData = activeTrip.raw_route_response;
      const steps = routeData?.results?.[0]?.legs?.[0]?.steps;

      if (!steps || !Array.isArray(steps)) {
        setDirections([]);
        return;
      }

      // Extract directions with instructions
      const extractedDirections = steps
        .filter((step: any) => step.instruction && step.instruction.text)
        .map((step: any, index: number) => ({
          id: index,
          instruction: step.instruction.text,
          distance: step.distance || 0,
          time: step.time || 0,
          from_index: step.from_index,
          to_index: step.to_index,
          speed_limit: step.speed_limit,
          road_name: step.name,
          maneuver_type: step.instruction.type || 'continue',
          coordinates: routeData.results[0].geometry?.[0]?.[step.from_index] || null,
        }));

      setDirections(extractedDirections);
      setCurrentDirectionIndex(0);

      // Set initial next direction
      if (extractedDirections.length > 0) {
        setNextDirection(extractedDirections[0]);
      }
    } catch (extractError) {
      setDirections([]);
    }
  }, [activeTrip?.raw_route_response]);

  const stopStatusMonitoring = useCallback(() => {
    if (statusCheckInterval) {
      clearInterval(statusCheckInterval);
      setStatusCheckInterval(null);
    }
  }, [statusCheckInterval]);

  // Backup mechanism - if WebView doesn't load within 10 seconds, force it to be ready
  useEffect(() => {
    const backupTimer = setTimeout(() => {
      if (!isWebViewLoaded) {
        setIsWebViewLoaded(true);
        // Try to fetch vehicle data anyway
        fetchVehicleData();
      }
    }, 10000); // 10 seconds timeout

    return () => clearTimeout(backupTimer);
  }, [isWebViewLoaded, fetchVehicleData, setIsWebViewLoaded]);

  // Trip control handlers
  const handlePauseResumeTrip = useCallback(async () => {
    if (!activeTrip?.id) return;

    setPausingTrip(true);
    try {
      if (isPaused) {
        const response = await resumeTrip(activeTrip.id);
        if (response?.data?.success) {
          setIsPaused(false);
          // Restart tracking when trip resumes
          if (activeTrip.id) {
            const tripId = activeTrip.id;
            startLocationPing(tripId, false);
            // startSpeedLimitChecking(activeTrip, getCurrentLocation, false);
          }
        }
      } else {
        const response = await pauseTrip(activeTrip.id);
        if (response?.data?.success) {
          setIsPaused(true);
          // Stop tracking when trip is paused
          stopLocationPing();
          stopSpeedLimitChecking();
        }
      }
    } catch (err) {
      Alert.alert('Error', `Failed to ${isPaused ? 'resume' : 'pause'} trip`);
    } finally {
      setPausingTrip(false);
    }
  }, [activeTrip?.id, isPaused, startLocationPing, stopLocationPing, stopSpeedLimitChecking]);

  const handleCancelTrip = useCallback(async () => {
    if (!activeTrip?.id) return;

    Alert.alert('Cancel Trip', 'Are you sure you want to cancel this trip?', [
      { text: 'No', style: 'cancel' },
      {
        text: 'Yes',
        style: 'destructive',
        onPress: async () => {
          setCancelingTrip(true);
          try {
            const response = await cancelTrip(activeTrip.id);
            if (response?.data?.success) {
              stopLocationPing();
              stopSpeedLimitChecking();
              stopStatusMonitoring();
              clearActiveTrip();
              navigation.navigate('Dashboard');
            }
          } catch (err) {
            Alert.alert('Error', 'Failed to cancel trip');
          } finally {
            setCancelingTrip(false);
          }
        },
      },
    ]);
  }, [
    activeTrip?.id,
    stopLocationPing,
    stopSpeedLimitChecking,
    stopStatusMonitoring,
    clearActiveTrip,
    navigation,
  ]);

  const handleCompleteTrip = useCallback(async () => {
    if (!activeTrip?.id) return;

    Alert.alert('Complete Trip', 'Are you sure you want to mark this trip as completed?', [
      { text: 'No', style: 'cancel' },
      {
        text: 'Yes',
        onPress: async () => {
          setEndingTrip(true);
          try {
            const response = await completeTrip(activeTrip.id);
            if (response?.data?.success) {
              stopLocationPing();
              stopSpeedLimitChecking();
              stopStatusMonitoring();
              clearActiveTrip();
              navigation.navigate('Dashboard');
            }
          } catch (err) {
            Alert.alert('Error', 'Failed to complete trip');
          } finally {
            setEndingTrip(false);
          }
        },
      },
    ]);
  }, [
    activeTrip?.id,
    stopLocationPing,
    stopSpeedLimitChecking,
    stopStatusMonitoring,
    clearActiveTrip,
    navigation,
  ]);

  const handleEndTrip = useCallback(async () => {
    if (!activeTrip?.id) return;

    Alert.alert('End Trip', 'Are you sure you want to end this trip?', [
      { text: 'No', style: 'cancel' },
      {
        text: 'Yes',
        style: 'destructive',
        onPress: async () => {
          setEndingTrip(true);
          try {
            const response = await finishTrip(activeTrip.id, 'Trip ended by driver');
            if (response?.data?.success) {
              stopLocationPing();
              stopSpeedLimitChecking();
              stopStatusMonitoring();
              clearActiveTrip();
              navigation.navigate('Dashboard');
            }
          } catch (err) {
            Alert.alert('Error', 'Failed to end trip');
          } finally {
            setEndingTrip(false);
          }
        },
      },
    ]);
  }, [
    activeTrip?.id,
    stopLocationPing,
    stopSpeedLimitChecking,
    stopStatusMonitoring,
    clearActiveTrip,
    navigation,
  ]);

  // Start location tracking and other monitoring when trip is active
  useEffect(() => {
    if (activeTrip?.id && !isPaused) {
      const tripId = activeTrip.id;
      startLocationPing(tripId, isPaused);
      // startSpeedLimitChecking(activeTrip, getCurrentLocation, isPaused);
      extractDirections();
    }

    return () => {
      stopLocationPing();
      stopSpeedLimitChecking();
      stopStatusMonitoring();
    };
  }, [
    activeTrip?.id,
    isPaused,
    startLocationPing,
    stopLocationPing,
    stopSpeedLimitChecking,
    stopStatusMonitoring,
    extractDirections,
  ]);

  // Periodically fetch vehicle data
  useEffect(() => {
    if (activeTrip?.id && !isPaused) {
      const vehicleInterval = setInterval(() => {
        fetchVehicleData();
      }, 3000); // Every 3 seconds

      return () => clearInterval(vehicleInterval);
    }
  }, [activeTrip?.id, isPaused, fetchVehicleData]);

  // Show loading or error states
  if (isCheckingActiveTrip) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
        <View style={styles.loadingContainer}>{/* Loading content */}</View>
      </SafeAreaView>
    );
  }

  if (error || !activeTrip) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
        <View style={styles.errorContainer}>{/* Error content */}</View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
      <TripHeader
        shouldShowBackButton={shouldShowBackButton}
        onBackPress={() => navigation.goBack()}
        activeTrip={activeTrip}
        currentSpeed={liveSpeed !== null ? liveSpeed : currentSpeed}
        speedLimit={liveSpeedLimit !== null ? liveSpeedLimit : speedLimit}
      />

      <DirectionsCard
        liveInstruction={liveInstruction}
        liveInstructionDistance={liveInstructionDistance}
      />

      <TripMap
        activeTrip={activeTrip}
        isWebViewLoaded={isWebViewLoaded}
        onWebViewLoad={handleWebViewLoad}
        onWebViewLoadEnd={() => {
          if (!isWebViewLoaded) {
            handleWebViewLoad();
          }
        }}
        onWebViewError={(webViewError: any) => {
          console.error('WebView error:', webViewError);
        }}
        onWebViewMessage={(event: any) => {
          try {
            const data = JSON.parse(event.nativeEvent.data);
            if (data.type === 'debug') {
              console.log('WebView Debug:', data.message);
            } else if (data.type === 'error') {
              console.error('WebView Error:', data.message);
            }
          } catch (e) {
            // Ignore non-JSON messages
          }
        }}
        webViewRef={webViewRef}
      />

      <TripControls
        isPaused={isPaused}
        isNearDestination={isNearDestination}
        canEndTrip={canEndTrip}
        pausingTrip={pausingTrip}
        cancelingTrip={cancelingTrip}
        endingTrip={endingTrip}
        onPauseResume={handlePauseResumeTrip}
        onCancelComplete={isNearDestination ? handleCompleteTrip : handleCancelTrip}
        onEndTrip={handleEndTrip}
      />
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
});

export default ActiveTripScreen;
