import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Pause, Play, X, CheckCircle, Square } from 'lucide-react-native';
import { useTheme } from '../../contexts/ThemeContext';

interface TripControlsProps {
  isPaused: boolean;
  isNearDestination: boolean;
  canEndTrip: boolean;
  pausingTrip: boolean;
  cancelingTrip: boolean;
  endingTrip: boolean;
  onPauseResume: () => void;
  onCancelComplete: () => void;
  onEndTrip: () => void;
}

const TripControls: React.FC<TripControlsProps> = ({
  isPaused,
  isNearDestination,
  canEndTrip,
  pausingTrip,
  cancelingTrip,
  endingTrip,
  onPauseResume,
  onCancelComplete,
  onEndTrip,
}) => {
  const { theme } = useTheme();

  // Debug logging - removed to reduce console spam
  // console.log('🎮 TripControls rendered with:', {
  //   isNearDestination,
  //   isPaused,
  //   canEndTrip,
  // });

  return (
    <View style={[styles.controlsContainer, { backgroundColor: theme.background }]}>
      <View style={styles.controlButtonsRow}>
        {/* Pause/Resume Button */}
        {!isNearDestination && (
          <TouchableOpacity
            onPress={onPauseResume}
            disabled={pausingTrip}
            style={[
              styles.controlButton,
              {
                backgroundColor: pausingTrip
                  ? isPaused
                    ? theme.success + '60'
                    : theme.accent + '60'
                  : isPaused
                  ? theme.success
                  : theme.accent,
              },
            ]}
          >
            {pausingTrip ? (
              <View style={styles.controlButtonContent}>
                <View style={[styles.loadingSpinner, styles.loadingSpinnerWhite]} />
                <Text style={styles.controlButtonText}>
                  {isPaused ? 'Resuming...' : 'Pausing...'}
                </Text>
              </View>
            ) : (
              <View style={styles.controlButtonContent}>
                {isPaused ? <Play size={18} color="white" /> : <Pause size={18} color="white" />}
                <Text style={styles.controlButtonText}>{isPaused ? 'Resume' : 'Pause'}</Text>
              </View>
            )}
          </TouchableOpacity>
        )}

        {/* Cancel/Complete Trip Button */}
        <TouchableOpacity
          onPress={onCancelComplete}
          disabled={cancelingTrip || endingTrip}
          style={[
            styles.controlButton,
            {
              backgroundColor: isNearDestination
                ? endingTrip
                  ? theme.success + '60'
                  : theme.success
                : cancelingTrip
                ? theme.textSecondary + '60'
                : theme.textSecondary,
            },
          ]}
        >
          {cancelingTrip || endingTrip ? (
            <View style={styles.controlButtonContent}>
              <View style={[styles.loadingSpinner, styles.loadingSpinnerWhite]} />
              <Text style={styles.controlButtonText}>
                {isNearDestination ? 'Completing...' : 'Canceling...'}
              </Text>
            </View>
          ) : (
            <View style={styles.controlButtonContent}>
              {isNearDestination ? (
                <CheckCircle size={18} color="white" />
              ) : (
                <X size={18} color="white" />
              )}
              <Text style={styles.controlButtonText}>
                {isNearDestination ? 'Complete Trip' : 'Cancel'}
              </Text>
            </View>
          )}
        </TouchableOpacity>

        {/* End Trip Button */}
        {canEndTrip && (
          <TouchableOpacity
            onPress={onEndTrip}
            disabled={endingTrip}
            style={[
              styles.controlButton,
              { backgroundColor: endingTrip ? theme.danger + '60' : theme.danger },
            ]}
          >
            {endingTrip ? (
              <View style={styles.controlButtonContent}>
                <View style={[styles.loadingSpinner, styles.loadingSpinnerWhite]} />
                <Text style={styles.controlButtonText}>Ending...</Text>
              </View>
            ) : (
              <View style={styles.controlButtonContent}>
                <Square size={18} color="white" />
                <Text style={styles.controlButtonText}>End Trip</Text>
              </View>
            )}
          </TouchableOpacity>
        )}
      </View>
    </View>
  );
};

TripControls.displayName = 'TripControls';

const styles = StyleSheet.create({
  controlsContainer: {
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderTopWidth: 1,
    borderTopColor: '#E0E0E0',
  },
  controlButtonsRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 12,
  },
  controlButton: {
    flex: 1,
    borderRadius: 12,
    paddingVertical: 16,
    paddingHorizontal: 20,
    minHeight: 56,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  controlButtonContent: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  controlButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  loadingSpinner: {
    width: 16,
    height: 16,
    borderWidth: 2,
    borderRadius: 8,
    borderTopColor: 'transparent',
    // Animation would be handled by the parent component
  },
  loadingSpinnerWhite: {
    borderColor: 'white',
  },
});

export default React.memo(TripControls);
