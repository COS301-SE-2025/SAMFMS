import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { ArrowLeft } from 'lucide-react-native';
import { useTheme } from '../../contexts/ThemeContext';

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
}

const TripHeader: React.FC<TripHeaderProps> = ({
  shouldShowBackButton,
  onBackPress,
  activeTrip,
  currentSpeed,
  speedLimit,
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
      {shouldShowBackButton && (
        <TouchableOpacity onPress={onBackPress} style={styles.backButton}>
          <View style={[styles.backButtonCircle, { backgroundColor: theme.accent + '20' }]}>
            <ArrowLeft size={20} color={theme.accent} />
          </View>
        </TouchableOpacity>
      )}
      {!shouldShowBackButton && <View style={styles.headerRight} />}

      <View style={styles.headerTitleContainer}>
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
        <Text style={[styles.headerDistance, { color: theme.success }]}>
          {activeTrip.estimated_distance
            ? (activeTrip.estimated_distance / 1000).toFixed(1) + ' km'
            : 'Distance N/A'}
        </Text>
      </View>

      <View style={styles.headerRightContainer}>
        <View style={styles.speedContainer}>
          <Text style={[styles.speedValue, { color: theme.accent }]}>
            {currentSpeed.toFixed(0)}
          </Text>
          <Text style={[styles.speedLabel, { color: theme.textSecondary }]}>km/h</Text>
        </View>

        {/* Speed Limit Display */}
        {speedLimit && (
          <View
            style={[
              styles.speedLimitContainer,
              { backgroundColor: theme.warning + '20', borderColor: theme.warning },
            ]}
          >
            <Text style={[styles.speedLimitValue, { color: theme.warning }]}>{speedLimit}</Text>
            <Text style={[styles.speedLimitLabel, { color: theme.warning }]}>LIMIT</Text>
          </View>
        )}
      </View>
    </View>
  );
};

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
  backButton: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
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
    alignItems: 'center',
    paddingHorizontal: 16,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 4,
    textAlign: 'center',
  },
  headerPriority: {
    fontSize: 10,
    fontWeight: '600',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 12,
    marginBottom: 4,
    textAlign: 'center',
    overflow: 'hidden',
    minWidth: 60,
  },
  headerDistance: {
    fontSize: 12,
    fontWeight: '600',
    textAlign: 'center',
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
  speedValue: {
    fontSize: 20,
    fontWeight: '700',
    lineHeight: 24,
  },
  speedLabel: {
    fontSize: 10,
    fontWeight: '500',
    marginTop: -2,
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
  speedLimitValue: {
    fontSize: 16,
    fontWeight: '700',
    lineHeight: 18,
  },
  speedLimitLabel: {
    fontSize: 8,
    fontWeight: '600',
    marginTop: 1,
  },
});

export default TripHeader;
