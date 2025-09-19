import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { View, Text, StyleSheet, Alert, Vibration } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import {
  finishTrip,
  pauseTrip,
  resumeTrip,
  cancelTrip,
  completeTrip,
  reportSpeedViolation,
  getUserData,
} from '../utils/api';
import { useActiveTripContext } from '../contexts/ActiveTripContext';
import { useTheme } from '../contexts/ThemeContext';

// Import new components and hooks
import { TripHeader, DirectionsCard, TripMap, TripControls } from '../components/trip';
import {
  useLocationTracking,
  useSpeedLimitTracking,
  useVehicleData,
  useAccelerometerMonitoring,
} from '../hooks';

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
  const [lastSpeedViolationAlert, setLastSpeedViolationAlert] = useState<number>(0);
  const [lastSpeedViolationReport, setLastSpeedViolationReport] = useState<number>(0);
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
    vehicleLocation,
    isWebViewLoaded,
    liveInstruction,
    liveInstructionDistance,
    liveSpeed,
    liveSpeedLimit,
    setIsWebViewLoaded,
    fetchVehicleData,
    handleWebViewLoad,
    webViewRef,
  } = useVehicleData(activeTrip, currentSpeed, directions, currentDirectionIndex);

  // Callback for accelerometer violations (no popup, just logging)
  const handleAccelerometerViolation = useCallback(
    (params: {
      type: 'acceleration' | 'braking';
      value: number;
      threshold: number;
      timestamp: Date;
    }) => {
      const violationType =
        params.type === 'acceleration' ? 'Excessive Acceleration' : 'Excessive Braking';
      const intensity =
        Math.abs(params.value) > Math.abs(params.threshold) * 1.5 ? 'High' : 'Moderate';

      // Log the violation for debugging/analytics (no popup shown to user)
      console.log(
        `⚠️ ${violationType} Detected: ${intensity} ${params.type} - ${Math.abs(
          params.value
        ).toFixed(2)} m/s² (threshold: ${Math.abs(params.threshold).toFixed(2)} m/s²)`
      );

      // Note: Vibration and counter updates are handled in the useAccelerometerMonitoring hook
      // No popup alert shown to avoid interrupting the driver
    },
    []
  );

  // Use accelerometer monitoring for driving behavior
  const {
    isMonitoring: isAccelMonitoring,
    startMonitoring: startAccelMonitoring,
    stopMonitoring: stopAccelMonitoring,
    excessiveAcceleration,
    excessiveBraking,
    currentAcceleration,
    violations,
    isCalibrated,
    calibrationProgress,
    dataQuality,
  } = useAccelerometerMonitoring(handleAccelerometerViolation);

  // Debug effect to log calibration status changes
  useEffect(() => {
    console.log(
      `📊 Accelerometer Status: Calibrated=${isCalibrated}, Progress=${Math.round(
        calibrationProgress * 100
      )}%, Quality=${Math.round(dataQuality * 100)}%`
    );
    if (isCalibrated) {
      console.log(`✅ Accelerometer fully calibrated! Violation detection is now ACTIVE.`);
    }
  }, [isCalibrated, calibrationProgress, dataQuality]);

  // Calculate remaining cooldown time for display
  const [cooldownRemaining, setCooldownRemaining] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      if (violations.lastViolationTime) {
        const timeSinceViolation = Date.now() - violations.lastViolationTime.getTime();
        const cooldownPeriod = 30000; // 30 seconds in milliseconds
        const remaining = Math.max(0, cooldownPeriod - timeSinceViolation);
        setCooldownRemaining(Math.ceil(remaining / 1000));
      } else {
        setCooldownRemaining(0);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [violations.lastViolationTime]);

  // Calculate distance between two coordinates in meters using Haversine formula
  const calculateDistance = useCallback(
    (lat1: number, lon1: number, lat2: number, lon2: number): number => {
      // Haversine formula
      const R = 6371e3; // Earth's radius in meters
      const φ1 = (lat1 * Math.PI) / 180; // Convert lat1 to radians
      const φ2 = (lat2 * Math.PI) / 180; // Convert lat2 to radians
      const Δφ = ((lat2 - lat1) * Math.PI) / 180; // Latitude difference in radians
      const Δλ = ((lon2 - lon1) * Math.PI) / 180; // Longitude difference in radians

      const a =
        Math.sin(Δφ / 2) * Math.sin(Δφ / 2) +
        Math.cos(φ1) * Math.cos(φ2) * Math.sin(Δλ / 2) * Math.sin(Δλ / 2);
      const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

      const distance = R * c; // Distance in meters

      return distance;
    },
    []
  );

  // Check if driver is within 400m of destination - optimized to reduce recalculations
  const isNearDestination = useMemo(() => {
    // Reduced console logging
    // console.log('🔍 isNearDestination calculation started');

    if (!activeTrip?.destination?.location?.coordinates) {
      // console.log('❌ Missing destination data:', {
      //   hasDestination: !!activeTrip?.destination?.location?.coordinates,
      //   destination: activeTrip?.destination,
      // });
      return false;
    }

    // Determine which location source to use for distance calculation
    // Priority: 1) Live vehicle data from API, 2) Current location from GPS tracking
    let activeVehicleLocation = null;

    // Check if we have live vehicle data from the API (this is the most accurate)
    if (vehicleLocation?.position) {
      activeVehicleLocation = {
        latitude: vehicleLocation.position[0],
        longitude: vehicleLocation.position[1],
      };
    } else if (currentLocation) {
      activeVehicleLocation = currentLocation;
    }

    if (!activeVehicleLocation) {
      // console.log('❌ No vehicle location available');
      return false;
    }

    const destCoords = activeTrip.destination.location.coordinates;
    // Reduced logging
    // console.log('📍 Coordinates:', {
    //   vehicle: { lat: activeVehicleLocation.latitude, lng: activeVehicleLocation.longitude },
    //   destination: { lat: destCoords[1], lng: destCoords[0] },
    //   destCoords,
    //   locationSource,
    // });

    const distance = calculateDistance(
      activeVehicleLocation.latitude,
      activeVehicleLocation.longitude,
      destCoords[1], // destination latitude (GeoJSON: [lng, lat])
      destCoords[0] // destination longitude (GeoJSON: [lng, lat])
    );

    // Check if we're using mock location (Pretoria coordinates)
    const isMockLocation =
      Math.abs(activeVehicleLocation.latitude - -25.7479) < 0.001 &&
      Math.abs(activeVehicleLocation.longitude - 28.2293) < 0.001;

    let isNear = distance <= 500; // Set to 500m for testing - adjust based on actual needs

    // Reduced logging - only log when actually near
    if (isNear) {
      console.log('📏 Near destination:', {
        distance: Math.round(distance),
        threshold: 500,
        isNear,
      });
    }

    // For demo purposes: If using mock location, only enable completion if very close (within 1km)
    // This provides a more realistic demo experience
    if (isMockLocation && distance > 400) {
      // console.log('🎭 Mock location detected, but distance too far for completion');
      isNear = false;
    }

    // console.log('✅ Final isNearDestination result:', isNear);
    return isNear;
  }, [
    // Essential dependencies only
    activeTrip?.destination,
    currentLocation,
    vehicleLocation,
    calculateDistance,
  ]);

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
            startAccelMonitoring(); // Resume accelerometer monitoring
            console.log('🎯 Resumed accelerometer monitoring after trip resume');
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
          stopAccelMonitoring(); // Pause accelerometer monitoring
          console.log('⏸️ Paused accelerometer monitoring with trip');
        }
      }
    } catch (err) {
      Alert.alert('Error', `Failed to ${isPaused ? 'resume' : 'pause'} trip`);
    } finally {
      setPausingTrip(false);
    }
  }, [
    activeTrip?.id,
    isPaused,
    startLocationPing,
    stopLocationPing,
    stopSpeedLimitChecking,
    startAccelMonitoring,
    stopAccelMonitoring,
  ]);

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
              stopAccelMonitoring(); // Stop accelerometer monitoring
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
    stopAccelMonitoring,
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
            // Log accelerometer violations before completing trip
            console.log('🎯 Trip completion - Accelerometer violations:', {
              totalAccelerationViolations: violations.accelerationCount,
              totalBrakingViolations: violations.brakingCount,
              totalViolations: violations.accelerationCount + violations.brakingCount,
              lastViolationTime: violations.lastViolationTime,
            });

            const response = await completeTrip(activeTrip.id);
            if (response?.data?.success) {
              stopLocationPing();
              stopSpeedLimitChecking();
              stopStatusMonitoring();
              stopAccelMonitoring(); // Stop accelerometer monitoring
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
    violations.accelerationCount,
    violations.brakingCount,
    violations.lastViolationTime,
    stopLocationPing,
    stopSpeedLimitChecking,
    stopStatusMonitoring,
    stopAccelMonitoring,
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

  // Use refs to store functions to avoid dependency issues
  const startLocationPingRef = useRef(startLocationPing);
  const extractDirectionsRef = useRef(extractDirections);
  const startAccelMonitoringRef = useRef(startAccelMonitoring);
  const stopLocationPingRef = useRef(stopLocationPing);
  const stopSpeedLimitCheckingRef = useRef(stopSpeedLimitChecking);
  const stopStatusMonitoringRef = useRef(stopStatusMonitoring);
  const stopAccelMonitoringRef = useRef(stopAccelMonitoring);

  // Update refs on each render
  startLocationPingRef.current = startLocationPing;
  extractDirectionsRef.current = extractDirections;
  startAccelMonitoringRef.current = startAccelMonitoring;
  stopLocationPingRef.current = stopLocationPing;
  stopSpeedLimitCheckingRef.current = stopSpeedLimitChecking;
  stopStatusMonitoringRef.current = stopStatusMonitoring;
  stopAccelMonitoringRef.current = stopAccelMonitoring;

  // Start location tracking and other monitoring when trip is active
  const startTripMonitoring = useCallback(() => {
    if (activeTrip?.id && !isPaused) {
      const tripId = activeTrip.id;
      startLocationPingRef.current(tripId, isPaused);
      extractDirectionsRef.current();

      // Start accelerometer monitoring for driving behavior
      startAccelMonitoringRef.current();
      console.log('🎯 Started accelerometer monitoring for trip:', tripId);
    }
  }, [activeTrip?.id, isPaused]); // Only depend on state, not functions

  const stopTripMonitoring = useCallback(() => {
    stopLocationPingRef.current();
    stopSpeedLimitCheckingRef.current();
    stopStatusMonitoringRef.current();
    stopAccelMonitoringRef.current();
    console.log('🛑 Stopped all trip monitoring');
  }, []); // No dependencies needed since we use refs

  // Use refs to track monitoring state to avoid effect recreation
  const isMonitoringActiveRef = useRef(false);

  useEffect(() => {
    if (activeTrip?.id && !isPaused && !isMonitoringActiveRef.current) {
      startTripMonitoring();
      isMonitoringActiveRef.current = true;
    } else if ((!activeTrip?.id || isPaused) && isMonitoringActiveRef.current) {
      stopTripMonitoring();
      isMonitoringActiveRef.current = false;
    }

    // Cleanup on unmount
    return () => {
      if (isMonitoringActiveRef.current) {
        stopTripMonitoring();
        isMonitoringActiveRef.current = false;
      }
    };
  }, [activeTrip?.id, isPaused, startTripMonitoring, stopTripMonitoring]); // Include the stable callbacks

  // Periodically fetch vehicle data - use ref to avoid dependency issues
  const fetchVehicleDataRef = useRef(fetchVehicleData);
  fetchVehicleDataRef.current = fetchVehicleData;

  useEffect(() => {
    if (activeTrip?.id && !isPaused) {
      const vehicleInterval = setInterval(() => {
        fetchVehicleDataRef.current();
      }, 5000); // Reduced frequency: Every 5 seconds instead of 3

      return () => clearInterval(vehicleInterval);
    }
  }, [activeTrip?.id, isPaused]);

  // Function to play beep sound
  const playBeepSound = useCallback(() => {
    // Vibration for immediate feedback (no popup)
    try {
      // Short vibration for immediate feedback
      Vibration.vibrate(100);
    } catch (beepError) {
      // Fallback: Multiple vibrations if single vibration fails
      Vibration.vibrate([0, 200, 100, 200]);
    }
  }, []);

  // Function to report speed violation to API
  const reportViolation = useCallback(
    async (
      speed: number,
      currentSpeedLimit: number,
      location: { latitude: number; longitude: number }
    ) => {
      if (!activeTrip?.id) {
        console.warn('Cannot report violation: missing trip data', {
          hasActiveTrip: !!activeTrip,
          tripId: activeTrip?.id,
          fullTripData: activeTrip,
        });
        return;
      }

      // Get the current user/employee data to use as driver ID
      const userData = await getUserData();
      const employeeId = userData?.employee_id || userData?.id || userData?.user_id;

      if (!employeeId) {
        console.warn('Cannot report violation: missing employee ID from user data', {
          userData,
          availableFields: Object.keys(userData || {}),
        });
        return;
      }

      try {
        await reportSpeedViolation({
          trip_id: activeTrip.id,
          driver_id: employeeId,
          speed: speed,
          speed_limit: currentSpeedLimit,
          location: {
            type: 'Point',
            coordinates: [location.longitude, location.latitude], // GeoJSON format: [lng, lat]
          },
          time: new Date().toISOString(),
        });

        console.log(
          `Speed violation reported: ${Math.round(speed)} km/h in ${currentSpeedLimit} km/h zone`
        );
      } catch (violationError) {
        console.error('Failed to report speed violation:', violationError);
      }
    },
    [activeTrip]
  );

  // Speed limit violation monitoring with beep alert and violation reporting
  // Split into smaller effects to reduce re-renders
  const currentSpeedValue = useMemo(() => {
    return liveSpeed !== null ? liveSpeed : currentSpeed;
  }, [liveSpeed, currentSpeed]);

  const currentSpeedLimitValue = useMemo(() => {
    return liveSpeedLimit !== null ? liveSpeedLimit : speedLimit;
  }, [liveSpeedLimit, speedLimit]);

  useEffect(() => {
    const now = Date.now();

    // Check if driver is speeding (only when trip is active and not paused)
    if (
      activeTrip?.id &&
      !isPaused &&
      currentSpeedLimitValue &&
      currentSpeedValue > currentSpeedLimitValue &&
      now - lastSpeedViolationAlert > 3000 // Only alert every 3 seconds
    ) {
      // Update the last alert time to prevent spam
      setLastSpeedViolationAlert(now);

      // Trigger beep sound and vibration
      playBeepSound();

      // Check if this is a reportable violation (5+ km/h over limit)
      const speedExcess = currentSpeedValue - currentSpeedLimitValue;
      if (
        speedExcess >= 5 &&
        currentLocation &&
        now - lastSpeedViolationReport > 30000 // Only report every 30 seconds
      ) {
        setLastSpeedViolationReport(now);

        // Report the violation to the API
        reportViolation(currentSpeedValue, currentSpeedLimitValue, currentLocation);

        console.warn(
          `REPORTABLE Speed violation: ${Math.round(currentSpeedValue)} km/h (${Math.round(
            speedExcess
          )} km/h over ${currentSpeedLimitValue} km/h limit)`
        );
      } else {
        // Just log minor violations
        console.warn(
          `Speed limit exceeded: ${Math.round(
            currentSpeedValue
          )} km/h (limit: ${currentSpeedLimitValue} km/h)`
        );
      }
    }
  }, [
    // Reduced dependencies using memoized values
    currentSpeedValue,
    currentSpeedLimitValue,
    activeTrip?.id,
    isPaused,
    lastSpeedViolationAlert,
    lastSpeedViolationReport,
    playBeepSound,
    currentLocation,
    reportViolation,
  ]);

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
        accelerometerData={{
          excessiveAcceleration,
          excessiveBraking,
          currentAcceleration,
          violations,
          isCalibrated,
          calibrationProgress,
          dataQuality,
        }}
      />

      {/* Debug Info Display - Commented out for clean interface */}
      {/* 
      {__DEV__ && (
        <View
          style={[
            styles.debugContainer,
            { backgroundColor: theme.cardBackground, borderColor: theme.border },
          ]}
        >
          <Text style={[styles.debugTitle, { color: theme.text }]}>
            🔧 Behavior Analytics Debug
          </Text>
          <View style={styles.debugRow}>
            <Text style={[styles.debugLabel, { color: theme.textSecondary }]}>Calibrated:</Text>
            <Text
              style={[styles.debugValue, { color: isCalibrated ? theme.success : theme.danger }]}
            >
              {isCalibrated ? 'YES' : 'NO'}
            </Text>
          </View>
          <View style={styles.debugRow}>
            <Text style={[styles.debugLabel, { color: theme.textSecondary }]}>Progress:</Text>
            <Text style={[styles.debugValue, { color: theme.text }]}>
              {Math.round(calibrationProgress * 100)}%
            </Text>
          </View>
          <View style={styles.debugRow}>
            <Text style={[styles.debugLabel, { color: theme.textSecondary }]}>Quality:</Text>
            <Text style={[styles.debugValue, { color: theme.text }]}>
              {Math.round(dataQuality * 100)}%
            </Text>
          </View>
          <View style={styles.debugRow}>
            <Text style={[styles.debugLabel, { color: theme.textSecondary }]}>Acceleration:</Text>
            <Text style={[styles.debugValue, { color: theme.text }]}>
              {currentAcceleration.toFixed(2)} m/s²
            </Text>
          </View>
          <View style={styles.debugRow}>
            <Text style={[styles.debugLabel, { color: theme.textSecondary }]}>Violations:</Text>
            <Text style={[styles.debugValue, { color: theme.text }]}>
              ACC: {violations.accelerationCount}, BRK: {violations.brakingCount}
            </Text>
          </View>
          <View style={styles.debugRow}>
            <Text style={[styles.debugLabel, { color: theme.textSecondary }]}>Cooldown:</Text>
            <Text
              style={[
                styles.debugValue,
                { color: cooldownRemaining > 0 ? theme.warning : theme.success },
              ]}
            >
              {cooldownRemaining > 0 ? `${cooldownRemaining}s` : 'Ready'}
            </Text>
          </View>
        </View>
      )}
      */}

      {!isCalibrated && calibrationProgress > 0 && (
        <View style={[styles.calibrationBanner, { backgroundColor: theme.warning || '#ffd43b' }]}>
          <Text style={[styles.calibrationText, { color: theme.background || '#000' }]}>
            🔧 Calibrating Behavior Analytics... {Math.round(calibrationProgress * 100)}%
          </Text>
          <View style={styles.progressBarContainer}>
            <View style={styles.progressBarBackground} />
            <View
              style={[
                styles.progressBar,
                {
                  backgroundColor: theme.background || '#000',
                  width: `${calibrationProgress * 100}%`,
                },
              ]}
            />
          </View>
          <Text style={[styles.calibrationSubtext, { color: theme.textSecondary || '#666' }]}>
            Drive normally - violations alerts are disabled during calibration
          </Text>
        </View>
      )}

      {/* Temporary Debug Info for Testing - Commented out for clean interface */}
      {/* 
      {isCalibrated && (
        <View style={[styles.debugContainer, { backgroundColor: theme.cardBackground }]}>
          <Text style={[styles.debugText, { color: theme.text }]}>
            DEBUG: ACC={currentAcceleration.toFixed(2)} | Quality={Math.round(dataQuality * 100)}% |
            Violations: ACC={violations.accelerationCount} BRK={violations.brakingCount}
          </Text>
        </View>
      )}
      */}

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
  calibrationBanner: {
    paddingVertical: 12,
    paddingHorizontal: 16,
    alignItems: 'center',
    justifyContent: 'center',
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(0,0,0,0.1)',
  },
  calibrationText: {
    fontSize: 14,
    fontWeight: '600',
    textAlign: 'center',
    marginBottom: 8,
  },
  progressBarContainer: {
    width: '100%',
    height: 4,
    borderRadius: 2,
    marginBottom: 8,
    overflow: 'hidden',
    position: 'relative',
  },
  progressBarBackground: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.2)',
  },
  progressBar: {
    height: '100%',
    borderRadius: 2,
    position: 'absolute',
    top: 0,
    left: 0,
  },
  calibrationSubtext: {
    fontSize: 12,
    textAlign: 'center',
    fontStyle: 'italic',
  },
  debugContainer: {
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(0,0,0,0.1)',
  },
  debugTitle: {
    fontSize: 12,
    fontWeight: '600',
    marginBottom: 8,
    textAlign: 'center',
  },
  debugRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  debugLabel: {
    fontSize: 11,
    fontWeight: '500',
    flex: 1,
  },
  debugValue: {
    fontSize: 11,
    fontWeight: '600',
    flex: 1,
    textAlign: 'right',
  },
  debugText: {
    fontSize: 10,
    fontFamily: 'monospace',
    textAlign: 'center',
  },
});

export default ActiveTripScreen;
