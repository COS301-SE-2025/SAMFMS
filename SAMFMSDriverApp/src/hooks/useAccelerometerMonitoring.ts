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

      // Skip violation detection if data quality is too low
      if (quality < 0.3) {
        return;
      }

      // Check if enough time has passed since last alert
      if (now - lastAlertTimeRef.current < settings.alertCooldown) {
        return;
      }

      let violationDetected = false;
      let violationType = '';

      if (acceleration > settings.accelerationThreshold) {
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
    [settings.accelerationThreshold, settings.brakingThreshold, settings.alertCooldown, onViolation]
  );

  // Process accelerometer data with new sensor fusion and filtering
  // Note: For phone in upright/portrait orientation:
  // X-axis = lateral (left/right), Y-axis = vertical (up/down), Z-axis = forward/backward
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
        // Basic processing without sensor fusion
        processed = {
          raw: accelerometerVector,
          compensated: accelerometerVector,
          filtered: accelerometerVector,
          drivingAcceleration: z, // Use Z-axis for upright phone orientation
          quality: 0.7, // Default quality
        };
      }

      // Apply multistage filtering if enabled
      let finalAcceleration = processed.drivingAcceleration;
      if (settings.enableMultistageFiltering && multistageFilterRef.current) {
        const filteredVector = multistageFilterRef.current.filter(processed.compensated);
        finalAcceleration = filteredVector.z; // Use Z-axis for upright phone orientation
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
          `📊 Acceleration: ${finalAcceleration.toFixed(2)} m/s² | Quality: ${(
            processed.quality * 100
          ).toFixed(0)}% | ` +
            `Calibrated: ${sensorFusionRef.current.isCalibrated() ? 'Yes' : 'No'} | ` +
            `Filtering: ${settings.enableMultistageFiltering ? 'On' : 'Off'}`
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

  // Start monitoring accelerometer with sensor fusion
  const startMonitoring = useCallback(() => {
    if (isMonitoring) {
      console.log('Accelerometer monitoring already active');
      return;
    }

    console.log('🎯 Starting enhanced accelerometer monitoring with sensor fusion and filtering');

    // Reset sensor fusion and filters
    sensorFusionRef.current = new SensorFusion();
    if (settings.enableMultistageFiltering) {
      multistageFilterRef.current = new MultistageFilter(
        settings.processNoise,
        settings.measurementNoise,
        settings.cutoffFrequency,
        10,
        settings.movingAverageWindow
      );
    }

    // Set update interval based on settings
    setUpdateIntervalForType(SensorTypes.accelerometer, settings.samplingRate);

    // Subscribe to accelerometer data
    accelerometerSubscriptionRef.current = accelerometer.subscribe(
      processAccelerometerData,
      error => {
        console.error('Accelerometer error:', error);
        setIsMonitoring(false);
      }
    );

    // Subscribe to gyroscope if sensor fusion is enabled
    if (settings.enableSensorFusion) {
      setUpdateIntervalForType(SensorTypes.gyroscope, settings.samplingRate);
      gyroscopeSubscriptionRef.current = gyroscope.subscribe(processGyroscopeData, error => {
        console.warn('Gyroscope error (non-critical):', error);
        // Don't stop monitoring if gyroscope fails, just log the error
      });
    }

    setIsMonitoring(true);

    // Reset violation counters when starting
    setViolations({
      accelerationCount: 0,
      brakingCount: 0,
      lastViolationTime: null,
    });

    // Clear previous flags
    setExcessiveAcceleration(false);
    setExcessiveBraking(false);
    setCurrentAcceleration(0);
    setIsCalibrated(false);
    setCalibrationProgress(0);
    setDataQuality(0);

    // Reset gyroscope data
    gyroscopeDataRef.current = null;
  }, [isMonitoring, settings, processAccelerometerData, processGyroscopeData]);

  // Stop monitoring accelerometer
  const stopMonitoring = useCallback(() => {
    if (!isMonitoring) {
      console.log('Accelerometer monitoring already inactive');
      return;
    }

    console.log('🛑 Stopping enhanced accelerometer monitoring');

    if (accelerometerSubscriptionRef.current) {
      accelerometerSubscriptionRef.current.unsubscribe();
      accelerometerSubscriptionRef.current = null;
    }

    if (gyroscopeSubscriptionRef.current) {
      gyroscopeSubscriptionRef.current.unsubscribe();
      gyroscopeSubscriptionRef.current = null;
    }

    setIsMonitoring(false);
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
  }, [isMonitoring, violations, settings]);

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
