import React, { useRef, useEffect } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useTheme } from '../../contexts/ThemeContext';

interface AccelerometerDisplayProps {
  currentAcceleration: number;
  excessiveAcceleration: boolean;
  excessiveBraking: boolean;
  violationCount: number;
  isCalibrated?: boolean;
  calibrationProgress?: number;
  dataQuality?: number;
}

const AccelerometerDisplay: React.FC<AccelerometerDisplayProps> = React.memo(
  ({
    currentAcceleration,
    excessiveAcceleration,
    excessiveBraking,
    violationCount,
    isCalibrated = false,
    calibrationProgress = 0,
    dataQuality = 0,
  }) => {
    const { theme } = useTheme();
    const accelerationTextRef = useRef<Text>(null);
    const lastUpdateRef = useRef<number>(0);

    // Use ref to update the display value directly without re-rendering
    useEffect(() => {
      const now = Date.now();
      // Throttle DOM updates to every 200ms to improve performance
      if (now - lastUpdateRef.current > 200) {
        if (accelerationTextRef.current) {
          // Update the text content directly via ref
          const formattedValue = currentAcceleration.toFixed(2);
          accelerationTextRef.current.setNativeProps({
            children: `${formattedValue} m/s²`,
          });
        }
        lastUpdateRef.current = now;
      }
    }, [currentAcceleration]);

    // Determine color based on violation status and data quality
    const getAccelerationColor = () => {
      if (excessiveAcceleration || excessiveBraking) {
        return '#ff6b6b'; // Red for active violation
      } else if (violationCount > 0) {
        return '#ffd43b'; // Yellow for past violations
      } else if (dataQuality > 0.8) {
        return theme.success; // Green for high quality
      } else if (dataQuality > 0.5) {
        return '#ffd43b'; // Yellow for medium quality
      } else {
        return theme.textSecondary; // Gray for low quality
      }
    };

    // Get calibration status text
    const getCalibrationStatus = () => {
      if (!isCalibrated && calibrationProgress > 0) {
        return `Calibrating... ${Math.round(calibrationProgress * 100)}%`;
      } else if (isCalibrated) {
        return `Quality: ${Math.round(dataQuality * 100)}%`;
      } else {
        return 'Not calibrated';
      }
    };

    return (
      <View style={styles.container}>
        <Text style={[styles.label, { color: theme.textSecondary }]}>Acceleration:</Text>
        <Text ref={accelerationTextRef} style={[styles.value, { color: getAccelerationColor() }]}>
          {currentAcceleration.toFixed(2)} m/s²
        </Text>
        {(calibrationProgress > 0 || isCalibrated || dataQuality > 0) && (
          <Text style={[styles.status, { color: theme.textSecondary }]}>
            {getCalibrationStatus()}
          </Text>
        )}
      </View>
    );
  }
);

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
  },
  label: {
    fontSize: 12,
    fontWeight: '500',
    marginRight: 6,
  },
  value: {
    fontSize: 12,
    fontWeight: '700',
  },
  status: {
    fontSize: 10,
    fontWeight: '400',
    marginLeft: 8,
    fontStyle: 'italic',
  },
});

AccelerometerDisplay.displayName = 'AccelerometerDisplay';

export default AccelerometerDisplay;
