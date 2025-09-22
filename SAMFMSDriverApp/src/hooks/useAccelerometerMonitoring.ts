import { useState, useEffect, useRef, useCallback } from 'react';
import {
  accelerometer,
  gyroscope,
  SensorData,
  setUpdateIntervalForType,
  SensorTypes,
} from 'react-native-sensors';
import { Vibration } from 'react-native';
import { SensorFusion, Vector3D, ProcessedAcceleration } from '../utils/sensorFusion';
import { MultistageFilter } from '../utils/multistageFilter';
import {
  AccelerometerSettingsManager,
  AccelerometerSettings,
  DEFAULT_ACCELEROMETER_SETTINGS,
} from '../utils/accelerometerSettings';

interface AccelerometerHookReturn {
  isMonitoring: boolean;
  startMonitoring: () => void;
  stopMonitoring: () => void;
  excessiveAcceleration: boolean;
  excessiveBraking: boolean;
  currentAcceleration: number;
  violations: {
    accelerationCount: number;
    brakingCount: number;
    lastViolationTime: Date | null;
  };
  isCalibrated: boolean;
  calibrationProgress: number;
  dataQuality: number;
}

interface ViolationCallbackParams {
  type: 'acceleration' | 'braking';
  value: number;
  threshold: number;
  timestamp: Date;
}

export const useAccelerometerMonitoring = (
  onViolation?: (params: ViolationCallbackParams) => void
): AccelerometerHookReturn => {
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [excessiveAcceleration, setExcessiveAcceleration] = useState(false);
  const [excessiveBraking, setExcessiveBraking] = useState(false);
  const [currentAcceleration, setCurrentAcceleration] = useState(0);
  const [violations, setViolations] = useState({
    accelerationCount: 0,
    brakingCount: 0,
    lastViolationTime: null as Date | null,
  });
  const [isCalibrated, setIsCalibrated] = useState(false);
  const [calibrationProgress, setCalibrationProgress] = useState(0);
  const [dataQuality, setDataQuality] = useState(0);
  const [settings, setSettings] = useState<AccelerometerSettings>(DEFAULT_ACCELEROMETER_SETTINGS);

  const accelerometerSubscriptionRef = useRef<any>(null);
  const gyroscopeSubscriptionRef = useRef<any>(null);
  const lastAlertTimeRef = useRef<number>(0);
  const lastUIUpdateTimeRef = useRef<number>(0);
  const lastUIValueRef = useRef<number>(0);
  const sensorFusionRef = useRef<SensorFusion>(new SensorFusion());
  const multistageFilterRef = useRef<MultistageFilter | null>(null);
  const gyroscopeDataRef = useRef<Vector3D | null>(null);

  const settingsManager = AccelerometerSettingsManager.getInstance();

  // Load settings on mount
  useEffect(() => {
    const loadSettings = async () => {
      const loadedSettings = await settingsManager.loadSettings();
      setSettings(loadedSettings);

      // Initialize multistage filter with loaded settings
      if (loadedSettings.enableMultistageFiltering) {
        multistageFilterRef.current = new MultistageFilter(
          loadedSettings.processNoise,
          loadedSettings.measurementNoise,
          loadedSettings.cutoffFrequency,
          10, // 10Hz sampling frequency
          loadedSettings.movingAverageWindow
        );
      }
    };

    loadSettings();

    // Subscribe to settings changes
    const unsubscribe = settingsManager.subscribe(newSettings => {
      setSettings(newSettings);

      // Update multistage filter parameters
      if (newSettings.enableMultistageFiltering && multistageFilterRef.current) {
        multistageFilterRef.current.updateParameters(
          newSettings.processNoise,
          newSettings.measurementNoise,
          newSettings.cutoffFrequency,
          newSettings.movingAverageWindow
        );
      } else if (newSettings.enableMultistageFiltering && !multistageFilterRef.current) {
        multistageFilterRef.current = new MultistageFilter(
          newSettings.processNoise,
          newSettings.measurementNoise,
          newSettings.cutoffFrequency,
          10,
          newSettings.movingAverageWindow
        );
      } else if (!newSettings.enableMultistageFiltering) {
        multistageFilterRef.current = null;
      }
    });

    return unsubscribe;
  }, [settingsManager]);

  // Check for violations and trigger alerts
  const checkViolations = useCallback(
    (acceleration: number, quality: number) => {
      const now = Date.now();

      // Enhanced debug logging for violation detection
      const shouldLogDebug = Math.abs(acceleration) > 1.0; // Log when there's any significant acceleration

      // Check calibration status directly from sensor fusion for real-time accuracy
      const isCurrentlyCalibrated = settings.enableSensorFusion
        ? sensorFusionRef.current.isCalibrated()
        : true; // Skip calibration requirement if sensor fusion is disabled

      const currentProgress = settings.enableSensorFusion
        ? sensorFusionRef.current.getCalibrationProgress()
        : 1.0;

      if (shouldLogDebug) {
        console.log(
          `🔍 VIOLATION CHECK: acc=${acceleration.toFixed(3)}, quality=${(quality * 100).toFixed(
            1
          )}%, calibrated=${isCurrentlyCalibrated} (state: ${isCalibrated}), accel_threshold=${
            settings.accelerationThreshold
          }, brake_threshold=${settings.brakingThreshold}`
        );
      }

      // Skip violation detection if data quality is too low
      // Temporarily reduced threshold from 0.6 to 0.3 for better testing
      if (quality < 0.3) {
        if (shouldLogDebug) {
          console.log(`❌ SKIP: Quality too low (${(quality * 100).toFixed(1)}% < 30%)`);
        }
        return;
      }

      // Skip violation detection during calibration phase
      // Allow the system to learn normal driving patterns without false alerts
      if (!isCurrentlyCalibrated) {
        if (shouldLogDebug) {
          console.log(
            `❌ SKIP: System not calibrated yet (progress: ${Math.round(currentProgress * 100)}%)`
          );
        }
        return;
      }

      // Check if enough time has passed since last alert
      const timeSinceLastAlert = now - lastAlertTimeRef.current;
      if (timeSinceLastAlert < settings.alertCooldown) {
        if (shouldLogDebug) {
          const remainingCooldown = Math.ceil((settings.alertCooldown - timeSinceLastAlert) / 1000);
          console.log(
            `❌ SKIP: Cooldown active - ${remainingCooldown}s remaining (${(
              timeSinceLastAlert / 1000
            ).toFixed(1)}s/${settings.alertCooldown / 1000}s)`
          );
        }
        return;
      }

      let violationDetected = false;
      let violationType = '';

      if (acceleration > settings.accelerationThreshold) {
        console.log(
          `🚨 ACCELERATION VIOLATION DETECTED! ${acceleration.toFixed(3)} > ${
            settings.accelerationThreshold
          }`
        );
        setExcessiveAcceleration(true);
        violationDetected = true;
        violationType = 'acceleration';

        const violationTime = new Date();
        setViolations(prev => ({
          ...prev,
          accelerationCount: prev.accelerationCount + 1,
          lastViolationTime: violationTime,
        }));

        // Trigger violation callback if provided
        if (onViolation) {
          onViolation({
            type: 'acceleration',
            value: acceleration,
            threshold: settings.accelerationThreshold,
            timestamp: violationTime,
          });
        }

        console.warn(
          `🚨 EXCESSIVE ACCELERATION DETECTED: ${acceleration.toFixed(2)} m/s² (Quality: ${(
            quality * 100
          ).toFixed(0)}%)`
        );
      } else if (acceleration < settings.brakingThreshold) {
        console.log(
          `🚨 BRAKING VIOLATION DETECTED! ${acceleration.toFixed(3)} < ${settings.brakingThreshold}`
        );
        setExcessiveBraking(true);
        violationDetected = true;
        violationType = 'braking';
        const violationTime = new Date();
        setViolations(prev => ({
          ...prev,
          brakingCount: prev.brakingCount + 1,
          lastViolationTime: violationTime,
        }));

        // Trigger violation callback if provided
        if (onViolation) {
          onViolation({
            type: 'braking',
            value: acceleration,
            threshold: settings.brakingThreshold,
            timestamp: violationTime,
          });
        }

        console.warn(
          `🚨 EXCESSIVE BRAKING DETECTED: ${acceleration.toFixed(2)} m/s² (Quality: ${(
            quality * 100
          ).toFixed(0)}%)`
        );
      }

      if (violationDetected) {
        // Provide haptic feedback
        try {
          Vibration.vibrate([0, 200, 100, 200]); // Pattern: wait, vibrate, wait, vibrate
        } catch (error) {
          console.warn('Vibration not available:', error);
        }

        lastAlertTimeRef.current = now;

        // Log cooldown period start
        console.log(
          `⏱️ Violation cooldown started - Next violation can be detected in ${
            settings.alertCooldown / 1000
          } seconds`
        );

        // Clear the violation flag after a short time
        setTimeout(() => {
          if (violationType === 'acceleration') {
            setExcessiveAcceleration(false);
          } else if (violationType === 'braking') {
            setExcessiveBraking(false);
          }
        }, 2000); // Clear after 2 seconds
      }
    },
    [
      settings.accelerationThreshold,
      settings.brakingThreshold,
      settings.alertCooldown,
      settings.enableSensorFusion,
      onViolation,
      isCalibrated,
    ]
  );

  // Process accelerometer data with new sensor fusion and filtering
  // Note: Dynamic orientation detection determines the appropriate driving axis
  // No assumptions made about device orientation
  const processAccelerometerData = useCallback(
    (data: SensorData) => {
      const { x, y, z } = data;
      const accelerometerVector: Vector3D = { x, y, z };

      // Get gyroscope data if available
      const gyroscopeVector = gyroscopeDataRef.current;

      let processed: ProcessedAcceleration;

      if (settings.enableSensorFusion) {
        // Use sensor fusion for better accuracy
        processed = sensorFusionRef.current.processFusedData(
          accelerometerVector,
          gyroscopeVector || undefined
        );

        // Update calibration status
        const newCalibrationProgress = sensorFusionRef.current.getCalibrationProgress();
        setCalibrationProgress(newCalibrationProgress);
        setIsCalibrated(sensorFusionRef.current.isCalibrated());

        // Add calibration samples during the first few seconds
        if (!sensorFusionRef.current.isCalibrated()) {
          sensorFusionRef.current.addCalibrationSample(accelerometerVector);
        }
      } else {
        // Basic processing without sensor fusion - use magnitude of acceleration
        // to avoid axis assumptions when sensor fusion is disabled
        const magnitude = Math.sqrt(x * x + y * y + z * z);
        const gravityMagnitude = 9.81;
        // Estimate driving acceleration as deviation from gravity
        const drivingMagnitude = Math.abs(magnitude - gravityMagnitude);

        processed = {
          raw: accelerometerVector,
          compensated: accelerometerVector,
          filtered: accelerometerVector,
          drivingAcceleration: drivingMagnitude,
          quality: 0.5, // Lower quality without sensor fusion
        };
      }

      // Apply multistage filtering if enabled
      let finalAcceleration = processed.drivingAcceleration;
      if (settings.enableMultistageFiltering && multistageFilterRef.current) {
        const filteredVector = multistageFilterRef.current.filter(processed.compensated);
        // Use the driving acceleration from sensor fusion instead of assuming axis
        finalAcceleration = sensorFusionRef.current.isCalibrated()
          ? processed.drivingAcceleration
          : Math.sqrt(
              filteredVector.x * filteredVector.x +
                filteredVector.y * filteredVector.y +
                filteredVector.z * filteredVector.z
            ) - 9.81;
      } // Update data quality
      setDataQuality(processed.quality);

      // Update current acceleration display (throttled to reduce re-renders)
      const now = Date.now();
      const shouldUpdateUI =
        now - lastUIUpdateTimeRef.current > 1000 && // Update every 1 second
        Math.abs(finalAcceleration - lastUIValueRef.current) > 0.3; // Significant change threshold

      if (shouldUpdateUI) {
        setCurrentAcceleration(finalAcceleration);
        lastUIUpdateTimeRef.current = now;
        lastUIValueRef.current = finalAcceleration;
      }

      // Check for violations
      checkViolations(finalAcceleration, processed.quality);

      // Debug logging for high acceleration events
      if (Math.abs(finalAcceleration) > 2.0) {
        console.log(
          `📊 Acceleration: ${finalAcceleration.toFixed(3)} m/s² (SIGNED) | Quality: ${(
            processed.quality * 100
          ).toFixed(0)}% | ` +
            `Calibrated: ${sensorFusionRef.current.isCalibrated() ? 'Yes' : 'No'} | ` +
            `Filtering: ${settings.enableMultistageFiltering ? 'On' : 'Off'} | ` +
            `Raw: [${accelerometerVector.x.toFixed(2)}, ${accelerometerVector.y.toFixed(
              2
            )}, ${accelerometerVector.z.toFixed(2)}]`
        );
      }
    },
    [settings.enableSensorFusion, settings.enableMultistageFiltering, checkViolations]
  );

  // Process gyroscope data
  const processGyroscopeData = useCallback((data: SensorData) => {
    const { x, y, z } = data;
    gyroscopeDataRef.current = { x, y, z };
  }, []);

  // Use refs to store the latest versions of the processing functions
  // This prevents them from being recreated on every render and causing startMonitoring to restart
  const processAccelerometerDataRef = useRef(processAccelerometerData);
  const processGyroscopeDataRef = useRef(processGyroscopeData);

  // Update refs when functions change
  useEffect(() => {
    processAccelerometerDataRef.current = processAccelerometerData;
    processGyroscopeDataRef.current = processGyroscopeData;
  }, [processAccelerometerData, processGyroscopeData]);

  // Start monitoring accelerometer with sensor fusion
  const startMonitoring = useCallback(() => {
    if (isMonitoring) {
      console.log('Accelerometer monitoring already active');
      return;
    }

    // Clean up any existing subscriptions before starting new ones
    if (accelerometerSubscriptionRef.current) {
      accelerometerSubscriptionRef.current.unsubscribe();
      accelerometerSubscriptionRef.current = null;
    }
    if (gyroscopeSubscriptionRef.current) {
      gyroscopeSubscriptionRef.current.unsubscribe();
      gyroscopeSubscriptionRef.current = null;
    }

    console.log('🎯 Starting enhanced accelerometer monitoring with sensor fusion and filtering');

    // Only reset sensor fusion if it doesn't exist or if we're forcing a restart
    // This prevents constant recalibration during normal operation
    if (!sensorFusionRef.current || !sensorFusionRef.current.isCalibrated()) {
      console.log('🔄 Initializing new sensor fusion instance (was not calibrated)');
      sensorFusionRef.current = new SensorFusion();
      // Start calibration process
      sensorFusionRef.current.startCalibration();

      // Reset calibration status since we're starting fresh
      setIsCalibrated(false);
      setCalibrationProgress(0);
    } else {
      console.log('✅ Reusing existing calibrated sensor fusion instance');
    }

    // Initialize multistage filter if needed
    if (settings.enableMultistageFiltering && !multistageFilterRef.current) {
      multistageFilterRef.current = new MultistageFilter(
        settings.processNoise,
        settings.measurementNoise,
        settings.cutoffFrequency,
        10,
        settings.movingAverageWindow
      );
    }

    // Reset monitoring state (but preserve calibration if it exists)
    setExcessiveAcceleration(false);
    setExcessiveBraking(false);
    setCurrentAcceleration(0);
    setDataQuality(0);

    // Update calibration display from current sensor fusion state
    if (sensorFusionRef.current) {
      setCalibrationProgress(sensorFusionRef.current.getCalibrationProgress());
      setIsCalibrated(sensorFusionRef.current.isCalibrated());
    }

    // Set update interval based on settings
    setUpdateIntervalForType(SensorTypes.accelerometer, settings.samplingRate);

    // Subscribe to accelerometer data using ref to avoid dependency issues
    accelerometerSubscriptionRef.current = accelerometer.subscribe(
      data => processAccelerometerDataRef.current(data),
      error => {
        console.error('Accelerometer error:', error);
        setIsMonitoring(false);
      }
    );

    // Subscribe to gyroscope if sensor fusion is enabled using ref
    if (settings.enableSensorFusion) {
      setUpdateIntervalForType(SensorTypes.gyroscope, settings.samplingRate);
      gyroscopeSubscriptionRef.current = gyroscope.subscribe(
        data => processGyroscopeDataRef.current(data),
        error => {
          console.warn('Gyroscope error (non-critical):', error);
          // Don't stop monitoring if gyroscope fails, just log the error
        }
      );
    }

    // Set monitoring state AFTER successful subscription setup
    setIsMonitoring(true);

    // Reset violation counters when starting
    setViolations({
      accelerationCount: 0,
      brakingCount: 0,
      lastViolationTime: null,
    });

    // Reset gyroscope data
    gyroscopeDataRef.current = null;
  }, [
    isMonitoring,
    settings.enableSensorFusion,
    settings.enableMultistageFiltering,
    settings.processNoise,
    settings.measurementNoise,
    settings.cutoffFrequency,
    settings.movingAverageWindow,
    settings.samplingRate,
  ]); // More specific dependencies without function references

  // Stop monitoring accelerometer
  const stopMonitoring = useCallback(() => {
    console.log('🛑 Stopping enhanced accelerometer monitoring');

    // Set monitoring to false BEFORE cleanup to prevent race conditions
    setIsMonitoring(false);

    if (accelerometerSubscriptionRef.current) {
      accelerometerSubscriptionRef.current.unsubscribe();
      accelerometerSubscriptionRef.current = null;
    }

    if (gyroscopeSubscriptionRef.current) {
      gyroscopeSubscriptionRef.current.unsubscribe();
      gyroscopeSubscriptionRef.current = null;
    }

    setExcessiveAcceleration(false);
    setExcessiveBraking(false);
    setCurrentAcceleration(0);
    setIsCalibrated(false);
    setCalibrationProgress(0);
    setDataQuality(0);

    // Log final violation summary with enhanced metrics
    if (violations.accelerationCount > 0 || violations.brakingCount > 0) {
      console.log(
        `📊 Enhanced Trip Summary:
        - Acceleration violations: ${violations.accelerationCount}
        - Braking violations: ${violations.brakingCount}
        - Sensor fusion: ${settings.enableSensorFusion ? 'Enabled' : 'Disabled'}
        - Multistage filtering: ${settings.enableMultistageFiltering ? 'Enabled' : 'Disabled'}
        - Final calibration status: ${
          sensorFusionRef.current.isCalibrated() ? 'Calibrated' : 'Not calibrated'
        }`
      );
    }
  }, [violations, settings]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (accelerometerSubscriptionRef.current) {
        accelerometerSubscriptionRef.current.unsubscribe();
      }
      if (gyroscopeSubscriptionRef.current) {
        gyroscopeSubscriptionRef.current.unsubscribe();
      }
    };
  }, []);

  return {
    isMonitoring,
    startMonitoring,
    stopMonitoring,
    excessiveAcceleration,
    excessiveBraking,
    currentAcceleration,
    violations,
    isCalibrated,
    calibrationProgress,
    dataQuality,
  };
};
