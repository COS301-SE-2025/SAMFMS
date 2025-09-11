import React, { createContext, useContext, useState, useRef, useEffect, ReactNode } from 'react';
import { AppState, AppStateStatus, Platform, Vibration } from 'react-native';
import NotificationService from '../services/NotificationService';
import BackgroundTimer from 'react-native-background-timer';

interface PhoneUsageViolation {
  id: string;
  timestamp: Date;
  type:
    | 'app_background'
    | 'screen_interaction_loss'
    | 'call_detected'
    | 'notification_interaction'
    | 'grace_period_exceeded'
    | 'extended_background';
  duration?: number; // in seconds
  description: string;
}

interface BehaviorMetrics {
  totalMonitoringTime: number; // in seconds
  phoneUsageViolations: PhoneUsageViolation[];
  appBackgroundTime: number; // total time app was in background during monitoring
  lastActivity: Date | null;
}

interface BehaviorMonitoringContextType {
  isMonitoringActive: boolean;
  currentBehaviorMetrics: BehaviorMetrics;
  startMonitoring: () => void;
  stopMonitoring: () => void;
  clearViolations: () => void;
}

const BehaviorMonitoringContext = createContext<BehaviorMonitoringContextType | undefined>(
  undefined
);

export const useBehaviorMonitoring = () => {
  const context = useContext(BehaviorMonitoringContext);
  if (context === undefined) {
    throw new Error('useBehaviorMonitoring must be used within a BehaviorMonitoringProvider');
  }
  return context;
};

interface BehaviorMonitoringProviderProps {
  children: ReactNode;
}

export const BehaviorMonitoringProvider: React.FC<BehaviorMonitoringProviderProps> = ({
  children,
}) => {
  const [isMonitoringActive, setIsMonitoringActive] = useState(false);
  const [currentBehaviorMetrics, setCurrentBehaviorMetrics] = useState<BehaviorMetrics>({
    totalMonitoringTime: 0,
    phoneUsageViolations: [],
    appBackgroundTime: 0,
    lastActivity: null,
  });

  // Refs for monitoring state
  const monitoringStartTime = useRef<Date | null>(null);
  const backgroundStartTime = useRef<Date | null>(null);
  const backgroundCheckTimer = useRef<ReturnType<typeof setInterval> | null>(null);
  const monitoringInterval = useRef<ReturnType<typeof setInterval> | null>(null);
  const lastActivityTime = useRef<Date>(new Date());
  const appStateRef = useRef<AppStateStatus>(AppState.currentState);
  const isMonitoringRef = useRef<boolean>(false);

  // Generate unique ID for violations
  const generateViolationId = () => {
    return `violation_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  };

  // Add a new violation
  // Add a violation directly to state - unified function
  const addViolation = React.useCallback(
    (type: PhoneUsageViolation['type'], description: string, duration?: number) => {
      // Skip adding violations if monitoring is not active
      if (!isMonitoringRef.current || !isMonitoringActive) {
        console.log('Skipping violation, monitoring is not active:', type, description);
        return;
      }

      console.log('Adding violation:', type, description);
      const violation: PhoneUsageViolation = {
        id: generateViolationId(),
        timestamp: new Date(),
        type,
        description,
        duration,
      };

      // Show a notification for this violation
      NotificationService.showViolationAlert(`${type} - ${description}`);

      // Update state to include the new violation
      setCurrentBehaviorMetrics(prev => {
        console.log('Current violations count:', prev.phoneUsageViolations.length);
        console.log('Adding new violation to state:', violation);
        return {
          ...prev,
          phoneUsageViolations: [...prev.phoneUsageViolations, violation],
        };
      });

      // Force a console log after state update to verify
      setTimeout(() => {
        console.log('Violation should now be added, checking state next...');
      }, 100);
    },
    [isMonitoringActive]
  );

  // Handle app state changes
  const handleAppStateChange = React.useCallback(
    (nextAppState: AppStateStatus) => {
      console.log(
        'App state changed:',
        appStateRef.current,
        '->',
        nextAppState,
        'Monitoring:',
        isMonitoringRef.current
      );

      // Double check monitoring state - exit early if monitoring is not active
      if (!isMonitoringRef.current || !isMonitoringActive) {
        // Update app state reference even when not monitoring
        appStateRef.current = nextAppState;
        return;
      }

      // Confirm we're in active monitoring state
      console.log('Processing app state change during active monitoring');

      const now = new Date();

      if (appStateRef.current === 'active' && nextAppState.match(/inactive|background/)) {
        // App going to background - start tracking background time
        console.log('App going to background, tracking background time');
        backgroundStartTime.current = now;

        // Make sure background timer is running
        // This ensures our monitoring continues even when app is in background
        BackgroundTimer.start();

        // Create background check timer that runs every minute to check background duration
        backgroundCheckTimer.current = BackgroundTimer.setInterval(() => {
          // Check if we're still monitoring
          if (!isMonitoringRef.current) {
            if (backgroundCheckTimer.current) {
              BackgroundTimer.clearInterval(backgroundCheckTimer.current);
              backgroundCheckTimer.current = null;
            }
            return;
          }

          // Check if we have a background start time
          if (backgroundStartTime.current) {
            const backgroundDuration = Math.floor(
              (new Date().getTime() - backgroundStartTime.current.getTime()) / 1000
            );

            // If background time exceeds 60 seconds (1 minute), add a violation
            if (backgroundDuration >= 60) {
              console.log('⚠️ BACKGROUND TIME EXCEEDED 1 MINUTE, ADDING VIOLATION');

              // Create violation
              const violation: PhoneUsageViolation = {
                id: generateViolationId(),
                timestamp: new Date(),
                type: 'app_background',
                description: `App in background for ${Math.floor(
                  backgroundDuration / 60
                )} minute(s)`,
                duration: backgroundDuration,
              };

              // Show violation notification with vibration
              try {
                Vibration.vibrate([1000, 500, 1000, 500, 1000]);
              } catch (e) {
                console.error('Vibration failed:', e);
              }

              NotificationService.showViolationAlert(
                `Background Violation - App minimized for ${Math.floor(
                  backgroundDuration / 60
                )} minute(s)`
              );

              // Add violation to state
              setCurrentBehaviorMetrics(prev => ({
                ...prev,
                phoneUsageViolations: [...prev.phoneUsageViolations, violation],
              }));

              // Reset background start time to only create a violation every minute
              backgroundStartTime.current = new Date();
            }
          }
        }, 60000); // Check every minute
      } else if (appStateRef.current.match(/inactive|background/) && nextAppState === 'active') {
        // App coming to foreground - calculate background time
        console.log('App coming to foreground, calculating background time');

        // Cancel background check timer
        if (backgroundCheckTimer.current) {
          try {
            BackgroundTimer.clearInterval(backgroundCheckTimer.current);
            backgroundCheckTimer.current = null;
          } catch (e) {
            console.error('Error clearing background check timer:', e);
          }
        }

        // Calculate time spent in background if we have a start time
        if (backgroundStartTime.current) {
          const backgroundDuration = Math.floor(
            (now.getTime() - backgroundStartTime.current.getTime()) / 1000
          );

          // Add violation if background time was 60 seconds or more
          if (backgroundDuration >= 60) {
            console.log('⚠️ BACKGROUND TIME EXCEEDED 1 MINUTE ON RETURN, ADDING VIOLATION');

            // Create violation
            const violation: PhoneUsageViolation = {
              id: generateViolationId(),
              timestamp: new Date(),
              type: 'app_background',
              description: `App in background for ${Math.floor(backgroundDuration / 60)} minute(s)`,
              duration: backgroundDuration,
            };

            // Show violation notification
            NotificationService.showViolationAlert(
              `Background Violation - App minimized for ${Math.floor(
                backgroundDuration / 60
              )} minute(s)`
            );

            // Add violation to state
            setCurrentBehaviorMetrics(prev => ({
              ...prev,
              phoneUsageViolations: [...prev.phoneUsageViolations, violation],
              appBackgroundTime: prev.appBackgroundTime + backgroundDuration,
            }));
          } else {
            // Just update background time without adding violation
            setCurrentBehaviorMetrics(prev => ({
              ...prev,
              appBackgroundTime: prev.appBackgroundTime + backgroundDuration,
            }));
          }

          backgroundStartTime.current = null;
        }
      }

      appStateRef.current = nextAppState;
    },
    [isMonitoringActive]
  );

  // Track user activity
  const trackActivity = React.useCallback(() => {
    // Exit immediately if monitoring is not active
    if (!isMonitoringRef.current || !isMonitoringActive) {
      console.log('Skipping activity tracking - monitoring not active');
      return;
    }

    const now = new Date();
    const timeSinceLastActivity = now.getTime() - lastActivityTime.current.getTime();
    const inactiveSeconds = Math.floor(timeSinceLastActivity / 1000);

    console.log(`Time since last activity: ${inactiveSeconds} seconds`);

    // If more than 30 seconds since last activity, consider it a potential violation
    if (timeSinceLastActivity > 30000) {
      console.log('SCREEN INTERACTION LOSS DETECTED - creating violation');

      // Create violation
      const violation: PhoneUsageViolation = {
        id: generateViolationId(),
        timestamp: new Date(),
        type: 'screen_interaction_loss',
        description: `No screen interaction detected for ${inactiveSeconds} seconds`,
        duration: inactiveSeconds,
      };

      // Show notification for this specific violation with more detailed message
      NotificationService.showViolationAlert(
        `Screen Interaction Loss - No activity for ${inactiveSeconds}s`
      );

      // Make sure violation gets recorded by updating the state directly
      setCurrentBehaviorMetrics(prev => {
        // Log the current state before update
        console.log(`Current violations before update: ${prev.phoneUsageViolations.length}`);

        const updatedViolations = [...prev.phoneUsageViolations, violation];
        console.log(`Violations after update: ${updatedViolations.length}`);

        return {
          ...prev,
          phoneUsageViolations: updatedViolations,
          lastActivity: now,
        };
      });

      console.log('Added screen interaction loss violation:', violation);
    } else {
      // Normal activity update
      lastActivityTime.current = now;
      setCurrentBehaviorMetrics(prev => ({
        ...prev,
        lastActivity: now,
      }));
    }
  }, [isMonitoringActive]);

  // Start monitoring
  const startMonitoring = () => {
    if (isMonitoringActive) return;

    const now = new Date();

    // Clear any existing background check timer
    if (backgroundCheckTimer.current) {
      console.log('Clearing existing background check timer before starting monitoring');
      try {
        BackgroundTimer.clearInterval(backgroundCheckTimer.current);
      } catch (e) {
        console.error('Error clearing existing background check timer:', e);
      }
      backgroundCheckTimer.current = null;
    }

    monitoringStartTime.current = now;
    lastActivityTime.current = now;
    setIsMonitoringActive(true);
    isMonitoringRef.current = true;

    // Reset metrics
    setCurrentBehaviorMetrics({
      totalMonitoringTime: 0,
      phoneUsageViolations: [],
      appBackgroundTime: 0,
      lastActivity: now,
    });

    // Start BackgroundTimer service to ensure it keeps running in background
    // This ensures our JavaScript will continue to execute even when the app is in background
    BackgroundTimer.start();

    // Show notification that monitoring is active
    // This helps to keep the app in a semi-active state in the background on some devices
    NotificationService.showOngoingMonitoring();

    // Start monitoring interval using BackgroundTimer to update total time even when app is in background
    monitoringInterval.current = BackgroundTimer.setInterval(() => {
      if (monitoringStartTime.current) {
        const totalTime = Math.floor(
          (new Date().getTime() - monitoringStartTime.current.getTime()) / 1000
        );
        setCurrentBehaviorMetrics(prev => ({
          ...prev,
          totalMonitoringTime: totalTime,
        }));
      }
    }, 1000);

    console.log('Behavior monitoring started with background timer');
  };

  // Stop monitoring
  const stopMonitoring = () => {
    if (!isMonitoringActive) return;

    console.log('Stopping behavior monitoring completely');

    // Immediately update monitoring state flags to prevent any new violations
    setIsMonitoringActive(false);
    isMonitoringRef.current = false;

    // Reset all app state tracking variables
    monitoringStartTime.current = null;
    backgroundStartTime.current = null;
    lastActivityTime.current = new Date(); // Reset to avoid false violations

    // Important: Also reset the app state reference to prevent false background violations
    appStateRef.current = AppState.currentState;

    // Cancel all notifications
    NotificationService.cancelAllNotifications();

    // Clear all timers
    if (monitoringInterval.current) {
      try {
        BackgroundTimer.clearInterval(monitoringInterval.current);
      } catch (e) {
        console.error('Error clearing monitoring interval:', e);
      }
      monitoringInterval.current = null;
    }

    // Clear background check timer
    if (backgroundCheckTimer.current) {
      try {
        console.log('Stopping monitoring: Clearing background check timer');
        BackgroundTimer.clearInterval(backgroundCheckTimer.current);
      } catch (e) {
        console.error('Error clearing background check timer:', e);
      } finally {
        backgroundCheckTimer.current = null;
      }
    }

    // Fully reset all metrics to ensure clean state after stopping
    console.log('Final state reset');
    setCurrentBehaviorMetrics({
      totalMonitoringTime: 0,
      phoneUsageViolations: [],
      appBackgroundTime: 0,
      lastActivity: new Date(),
    });

    // Ensure BackgroundTimer is completely stopped
    try {
      BackgroundTimer.stop();
    } catch (e) {
      console.error('Error stopping background timer:', e);
    }

    // Make sure we log when behavior monitoring stops
    console.log('Behavior monitoring stopped completely');
  };

  // Clear violations
  const clearViolations = () => {
    setCurrentBehaviorMetrics(prev => ({
      ...prev,
      phoneUsageViolations: [],
      appBackgroundTime: 0,
    }));
  };

  // Set up app state listener
  useEffect(() => {
    const subscription = AppState.addEventListener('change', handleAppStateChange);

    return () => {
      subscription?.remove();
    };
  }, [handleAppStateChange]);

  // Track screen interactions (this is a simplified version)
  useEffect(() => {
    if (isMonitoringActive) {
      trackActivity();
    }
  }, [isMonitoringActive, trackActivity]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      // Clean up all timers
      if (monitoringInterval.current) {
        BackgroundTimer.clearInterval(monitoringInterval.current);
        monitoringInterval.current = null;
      }
      if (backgroundCheckTimer.current) {
        BackgroundTimer.clearInterval(backgroundCheckTimer.current);
        backgroundCheckTimer.current = null;
      }

      // Make sure to stop background timer service to prevent battery drain
      BackgroundTimer.stop();

      // Reset monitoring state
      isMonitoringRef.current = false;
    };
  }, []);

  const value = {
    isMonitoringActive,
    currentBehaviorMetrics,
    startMonitoring,
    stopMonitoring,
    clearViolations,
  };

  return (
    <BehaviorMonitoringContext.Provider value={value}>
      {children}
    </BehaviorMonitoringContext.Provider>
  );
};
