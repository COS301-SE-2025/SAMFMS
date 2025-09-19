import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { ArrowLeft } from 'lucide-react-native';
import { useTheme } from '../../contexts/ThemeContext';
import AccelerometerDisplay from './AccelerometerDisplay';

interface TripHeaderProps {
  shouldShowBackButton: boolean;
  onBackPress: () => void;
  activeTrip: {
    name?: string;
    priority?: string;
    estimated_distance?: number;
  };
  currentSpeed: number;
  speedLimit?: number | null;
  accelerometerData?: {
    excessiveAcceleration: boolean;
    excessiveBraking: boolean;
    currentAcceleration: number;
    violations: {
      accelerationCount: number;
      brakingCount: number;
    };
    isCalibrated?: boolean;
    calibrationProgress?: number;
    dataQuality?: number;
  };
}

const TripHeader: React.FC<TripHeaderProps> = ({
  shouldShowBackButton,
  onBackPress,
  activeTrip,
  currentSpeed,
  speedLimit,
  accelerometerData,
}) => {
  const { theme } = useTheme();

  return (
    <View
      style={[
        styles.header,
        {
          backgroundColor: theme.cardBackground,
          borderBottomColor: theme.border,
        },
      ]}
    >
      {/* Component content remains the same */}
      {/* Left side: Back button (if shown) and trip info */}
      <View style={styles.headerLeftContainer}>
        {shouldShowBackButton && (
          <TouchableOpacity onPress={onBackPress} style={styles.backButton}>
            <View style={[styles.backButtonCircle, { backgroundColor: theme.accent + '20' }]}>
              <ArrowLeft size={20} color={theme.accent} />
            </View>
          </TouchableOpacity>
        )}

        <View style={styles.headerTitleContainer}>
          <View style={styles.tripNamePriorityContainer}>
            <Text style={[styles.headerTitle, { color: theme.text }]}>
              {activeTrip.name || 'Active Trip'}
            </Text>
            {activeTrip.priority && (
              <Text
                style={[
                  styles.headerPriority,
                  {
                    color: theme.background,
                    backgroundColor:
                      activeTrip.priority.toLowerCase() === 'low'
                        ? theme.success
                        : activeTrip.priority.toLowerCase() === 'normal'
                        ? theme.info
                        : activeTrip.priority.toLowerCase() === 'high'
                        ? theme.warning
                        : activeTrip.priority.toLowerCase() === 'urgent'
                        ? theme.danger
                        : theme.info,
                  },
                ]}
              >
                {activeTrip.priority.charAt(0).toUpperCase() + activeTrip.priority.slice(1)}
              </Text>
            )}
          </View>

          {/* Violation Counters */}
          {accelerometerData && accelerometerData.isCalibrated && (
            <View style={styles.violationCounters}>
              <View style={styles.violationCounter}>
                <Text style={[styles.violationLabel, { color: theme.danger }]}>ACC:</Text>
                <Text style={[styles.violationCountValue, { color: theme.danger }]}>
                  {accelerometerData.violations.accelerationCount}
                </Text>
              </View>
              <View style={styles.violationCounter}>
                <Text style={[styles.violationLabel, { color: theme.warning }]}>BRK:</Text>
                <Text style={[styles.violationCountValue, { color: theme.warning }]}>
                  {accelerometerData.violations.brakingCount}
                </Text>
              </View>
            </View>
          )}

          {/* Live Accelerometer Reading */}
          {accelerometerData && (
            <AccelerometerDisplay
              currentAcceleration={accelerometerData.currentAcceleration}
              excessiveAcceleration={accelerometerData.excessiveAcceleration}
              excessiveBraking={accelerometerData.excessiveBraking}
              violationCount={
                accelerometerData.violations.accelerationCount +
                accelerometerData.violations.brakingCount
              }
              isCalibrated={accelerometerData.isCalibrated}
              calibrationProgress={accelerometerData.calibrationProgress}
              dataQuality={accelerometerData.dataQuality}
            />
          )}

          {/* <Text style={[styles.headerDistance, { color: theme.success }]}>
            {activeTrip.estimated_distance
              ? (activeTrip.estimated_distance / 1000).toFixed(1) + ' km'
              : 'Distance N/A'}
          </Text> */}
        </View>
      </View>

      {/* Right side: Speed displays and accelerometer status */}
      <View style={styles.headerRightContainer}>
        <View
          style={[
            styles.speedContainer,
            styles.currentSpeedCircle,
            speedLimit && currentSpeed > speedLimit ? styles.currentSpeedCircleOverLimit : null,
          ]}
        >
          <Text style={styles.speedValueWhite}>{currentSpeed.toFixed(0)}</Text>
          <Text style={styles.speedLabelWhite}>km/h</Text>
        </View>

        {/* Speed Limit Display */}
        {speedLimit && (
          <View style={[styles.speedLimitContainer, styles.speedLimitCircle]}>
            <Text style={styles.speedLimitValue}>{speedLimit}</Text>
            <Text style={styles.speedLimitLabel}>LIMIT</Text>
          </View>
        )}

        {/* Accelerometer Status */}
        {accelerometerData &&
          (() => {
            const accelerationBgColor = accelerometerData.excessiveAcceleration
              ? '#ff6b6b'
              : accelerometerData.violations.accelerationCount > 0
              ? '#ffd43b'
              : '#51cf66';

            const brakingBgColor = accelerometerData.excessiveBraking
              ? '#ff6b6b'
              : accelerometerData.violations.brakingCount > 0
              ? '#ffd43b'
              : '#51cf66';

            return (
              <View style={styles.accelerometerContainer}>
                {/* Acceleration Violations */}
                <View style={[styles.violationIndicator, { backgroundColor: accelerationBgColor }]}>
                  <Text style={styles.violationText}>ACC</Text>
                  <Text style={styles.violationCount}>
                    {accelerometerData.violations.accelerationCount}
                  </Text>
                </View>

                {/* Braking Violations */}
                <View style={[styles.violationIndicator, { backgroundColor: brakingBgColor }]}>
                  <Text style={styles.violationText}>BRK</Text>
                  <Text style={styles.violationCount}>
                    {accelerometerData.violations.brakingCount}
                  </Text>
                </View>
              </View>
            );
          })()}
      </View>
    </View>
  );
};

TripHeader.displayName = 'TripHeader';

const styles = StyleSheet.create({
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 6,
    elevation: 3,
  },
  headerLeftContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  backButton: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  backButtonCircle: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTitleContainer: {
    flex: 1,
    alignItems: 'flex-start',
  },
  tripNamePriorityContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    marginRight: 8,
  },
  headerPriority: {
    fontSize: 10,
    fontWeight: '600',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 12,
    textAlign: 'center',
    overflow: 'hidden',
    minWidth: 60,
  },
  headerDistance: {
    fontSize: 12,
    fontWeight: '600',
  },
  headerRight: {
    width: 40,
  },
  headerRightContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    gap: 8,
  },
  speedContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 8,
  },
  currentSpeedCircle: {
    borderColor: '#FFFFFF',
    borderWidth: 3,
    borderRadius: 30,
    width: 60,
    height: 60,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 4,
  },
  currentSpeedCircleOverLimit: {
    backgroundColor: '#DC2626',
  },
  speedValue: {
    fontSize: 20,
    fontWeight: '700',
    lineHeight: 24,
  },
  speedValueWhite: {
    fontSize: 20,
    fontWeight: '700',
    lineHeight: 24,
    color: '#FFFFFF',
  },
  speedLabel: {
    fontSize: 10,
    fontWeight: '500',
    marginTop: -2,
  },
  speedLabelWhite: {
    fontSize: 10,
    fontWeight: '500',
    marginTop: -2,
    color: '#FFFFFF',
  },
  speedLimitContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderRadius: 8,
    paddingHorizontal: 6,
    paddingVertical: 4,
    minWidth: 50,
  },
  speedLimitCircle: {
    backgroundColor: '#FFFFFF',
    borderColor: '#DC2626',
    borderRadius: 30,
    width: 60,
    height: 60,
    borderWidth: 3,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 4,
  },
  speedLimitValue: {
    fontSize: 16,
    fontWeight: '700',
    lineHeight: 18,
    color: '#000000',
  },
  speedLimitLabel: {
    fontSize: 8,
    fontWeight: '600',
    marginTop: 1,
    color: '#000000',
  },
  accelerometerContainer: {
    flexDirection: 'column',
    marginLeft: 8,
  },
  accelerometerDisplay: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
  },
  accelerometerLabel: {
    fontSize: 12,
    fontWeight: '500',
    marginRight: 6,
  },
  accelerometerValue: {
    fontSize: 12,
    fontWeight: '700',
  },
  violationIndicator: {
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 15,
    width: 40,
    height: 30,
    marginVertical: 2,
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2,
    shadowRadius: 2,
    elevation: 2,
  },
  violationText: {
    fontSize: 8,
    fontWeight: '600',
    color: '#FFFFFF',
    lineHeight: 10,
  },
  violationCount: {
    fontSize: 10,
    fontWeight: '700',
    color: '#FFFFFF',
    lineHeight: 12,
  },
  violationCounters: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
    gap: 12,
  },
  violationCounter: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    backgroundColor: 'rgba(0,0,0,0.1)',
  },
  violationLabel: {
    fontSize: 10,
    fontWeight: '600',
    marginRight: 4,
  },
  violationCountValue: {
    fontSize: 10,
    fontWeight: '700',
    minWidth: 16,
    textAlign: 'center',
  },
});

TripHeader.displayName = 'TripHeader';

export default React.memo(TripHeader, (prevProps, nextProps) => {
  // Custom comparison to prevent unnecessary rerenders
  return (
    prevProps.shouldShowBackButton === nextProps.shouldShowBackButton &&
    prevProps.activeTrip?.name === nextProps.activeTrip?.name &&
    prevProps.activeTrip?.priority === nextProps.activeTrip?.priority &&
    Math.round(prevProps.currentSpeed) === Math.round(nextProps.currentSpeed) &&
    prevProps.speedLimit === nextProps.speedLimit &&
    // Only rerender if accelerometer values have significant changes
    Math.round(prevProps.accelerometerData?.currentAcceleration || 0) ===
      Math.round(nextProps.accelerometerData?.currentAcceleration || 0) &&
    prevProps.accelerometerData?.excessiveAcceleration ===
      nextProps.accelerometerData?.excessiveAcceleration &&
    prevProps.accelerometerData?.excessiveBraking ===
      nextProps.accelerometerData?.excessiveBraking &&
    prevProps.accelerometerData?.violations?.accelerationCount ===
      nextProps.accelerometerData?.violations?.accelerationCount &&
    prevProps.accelerometerData?.violations?.brakingCount ===
      nextProps.accelerometerData?.violations?.brakingCount
  );
});
