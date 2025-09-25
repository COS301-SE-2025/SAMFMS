import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Navigation } from 'lucide-react-native';
import { useTheme } from '../../contexts/ThemeContext';

interface DirectionsCardProps {
  liveInstruction?: string;
  liveInstructionDistance?: number | null;
}

const DirectionsCard: React.FC<DirectionsCardProps> = ({
  liveInstruction,
  liveInstructionDistance,
}) => {
  const { theme } = useTheme();

  if (!liveInstruction) {
    return null;
  }

  return (
    <View style={styles.directionsContainer}>
      <View style={[styles.directionCard, { backgroundColor: theme.accent + '15' }]}>
        <View style={[styles.directionIcon, { backgroundColor: theme.accent }]}>
          <Navigation size={16} color="white" />
        </View>
        <Text style={[styles.directionText, { color: theme.text }]} numberOfLines={2}>
          {liveInstruction}
        </Text>
        {liveInstructionDistance && (
          <Text style={[styles.directionDistance, { color: theme.textSecondary }]}>
            {Math.round(liveInstructionDistance)}m
          </Text>
        )}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  directionsContainer: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
  },
  directionCard: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 12,
    marginBottom: 8,
  },
  directionIcon: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  directionText: {
    flex: 1,
    fontSize: 16,
    fontWeight: '600',
  },
  directionDistance: {
    fontSize: 14,
    fontWeight: '500',
    marginLeft: 8,
  },
});

export default DirectionsCard;
