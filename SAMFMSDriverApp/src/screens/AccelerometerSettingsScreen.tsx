import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, ScrollView, StyleSheet, Alert, TouchableOpacity, Switch } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { ArrowLeft, RotateCcw } from 'lucide-react-native';
import { useTheme } from '../contexts/ThemeContext';
import {
  AccelerometerSettingsManager,
  AccelerometerSettings,
  DEFAULT_ACCELEROMETER_SETTINGS,
} from '../utils/accelerometerSettings';

interface AccelerometerSettingsScreenProps {
  navigation: any;
}

interface SliderSettingProps {
  title: string;
  subtitle: string;
  value: number;
  minValue: number;
  maxValue: number;
  step: number;
  unit: string;
  onValueChange: (value: number) => void;
  theme: any;
}

const SliderSetting: React.FC<SliderSettingProps> = ({
  title,
  subtitle,
  value,
  minValue,
  maxValue,
  step,
  unit,
  onValueChange,
  theme,
}) => {
  const [localValue, setLocalValue] = useState(value);

  const increment = () => {
    const newValue = Math.min(maxValue, localValue + step);
    setLocalValue(newValue);
    onValueChange(newValue);
  };

  const decrement = () => {
    const newValue = Math.max(minValue, localValue - step);
    setLocalValue(newValue);
    onValueChange(newValue);
  };

  return (
    <View style={[styles.settingItem, { borderBottomColor: theme.border }]}>
      <View style={styles.settingContent}>
        <Text style={[styles.settingTitle, { color: theme.text }]}>{title}</Text>
        <Text style={[styles.settingSubtitle, { color: theme.textSecondary }]}>{subtitle}</Text>
      </View>
      <View style={styles.sliderControls}>
        <TouchableOpacity
          style={[styles.sliderButton, { backgroundColor: theme.accent + '20' }]}
          onPress={decrement}
        >
          <Text style={[styles.sliderButtonText, { color: theme.accent }]}>−</Text>
        </TouchableOpacity>
        <Text style={[styles.sliderValue, { color: theme.text }]}>
          {localValue.toFixed(step < 1 ? 1 : 0)} {unit}
        </Text>
        <TouchableOpacity
          style={[styles.sliderButton, { backgroundColor: theme.accent + '20' }]}
          onPress={increment}
        >
          <Text style={[styles.sliderButtonText, { color: theme.accent }]}>+</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

interface ToggleSettingProps {
  title: string;
  subtitle: string;
  value: boolean;
  onValueChange: (value: boolean) => void;
  theme: any;
}

const ToggleSetting: React.FC<ToggleSettingProps> = ({
  title,
  subtitle,
  value,
  onValueChange,
  theme,
}) => (
  <View style={[styles.settingItem, { borderBottomColor: theme.border }]}>
    <View style={styles.settingContent}>
      <Text style={[styles.settingTitle, { color: theme.text }]}>{title}</Text>
      <Text style={[styles.settingSubtitle, { color: theme.textSecondary }]}>{subtitle}</Text>
    </View>
    <Switch
      value={value}
      onValueChange={onValueChange}
      trackColor={{ false: '#94a3b8', true: theme.accent }}
      thumbColor={value ? '#ffffff' : '#f4f4f5'}
    />
  </View>
);

export default function AccelerometerSettingsScreen({
  navigation,
}: AccelerometerSettingsScreenProps) {
  const { theme } = useTheme();
  const [settings, setSettings] = useState<AccelerometerSettings>(DEFAULT_ACCELEROMETER_SETTINGS);
  const [_hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  const settingsManager = AccelerometerSettingsManager.getInstance();

  const loadSettings = useCallback(async () => {
    try {
      const loadedSettings = await settingsManager.loadSettings();
      setSettings(loadedSettings);
    } catch (error) {
      Alert.alert('Error', 'Failed to load settings');
    }
  }, [settingsManager]);

  useEffect(() => {
    loadSettings();
  }, [loadSettings]);

  const updateSetting = <K extends keyof AccelerometerSettings>(
    key: K,
    value: AccelerometerSettings[K]
  ) => {
    const newSettings = { ...settings, [key]: value };
    setSettings(newSettings);
    setHasUnsavedChanges(true);

    // Auto-save settings
    saveSettings({ [key]: value });
  };

  const saveSettings = async (settingsToSave: Partial<AccelerometerSettings>) => {
    try {
      const validationErrors = settingsManager.validateSettings(settingsToSave);
      if (validationErrors.length > 0) {
        Alert.alert('Invalid Settings', validationErrors.join('\n'));
        return;
      }

      await settingsManager.saveSettings(settingsToSave);
      setHasUnsavedChanges(false);
    } catch (error) {
      Alert.alert('Error', 'Failed to save settings');
    }
  };

  const resetToDefaults = () => {
    Alert.alert(
      'Reset Settings',
      'Are you sure you want to reset all accelerometer settings to default values?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Reset',
          style: 'destructive',
          onPress: async () => {
            try {
              await settingsManager.resetToDefaults();
              await loadSettings();
              setHasUnsavedChanges(false);
            } catch (error) {
              Alert.alert('Error', 'Failed to reset settings');
            }
          },
        },
      ]
    );
  };

  const applyPreset = (presetName: string) => {
    const presets = settingsManager.getPresets();
    const preset = presets[presetName];
    if (preset) {
      setSettings({ ...settings, ...preset });
      setHasUnsavedChanges(true);
      saveSettings(preset);
    }
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
      {/* Header */}
      <View
        style={[
          styles.header,
          { backgroundColor: theme.cardBackground, borderBottomColor: theme.border },
        ]}
      >
        <TouchableOpacity style={styles.backButton} onPress={() => navigation.goBack()}>
          <ArrowLeft size={24} color={theme.text} />
        </TouchableOpacity>
        <Text style={[styles.headerTitle, { color: theme.text }]}>Accelerometer Settings</Text>
        <TouchableOpacity style={styles.resetButton} onPress={resetToDefaults}>
          <RotateCcw size={20} color={theme.accent} />
        </TouchableOpacity>
      </View>

      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        {/* Quick Presets */}
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.textSecondary }]}>QUICK PRESETS</Text>
          <View style={[styles.card, { backgroundColor: theme.cardBackground }]}>
            <View style={styles.presetButtons}>
              {Object.keys(settingsManager.getPresets()).map(presetName => (
                <TouchableOpacity
                  key={presetName}
                  style={[
                    styles.presetButton,
                    { backgroundColor: theme.accent + '20', borderColor: theme.accent },
                  ]}
                  onPress={() => applyPreset(presetName)}
                >
                  <Text style={[styles.presetButtonText, { color: theme.accent }]}>
                    {presetName.charAt(0).toUpperCase() + presetName.slice(1)}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        </View>

        {/* Detection Thresholds */}
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.textSecondary }]}>
            DETECTION THRESHOLDS
          </Text>
          <View style={[styles.card, { backgroundColor: theme.cardBackground }]}>
            <SliderSetting
              title="Acceleration Threshold"
              subtitle="Sensitivity for excessive acceleration detection"
              value={settings.accelerationThreshold}
              minValue={1}
              maxValue={10}
              step={0.5}
              unit="m/s²"
              onValueChange={value => updateSetting('accelerationThreshold', value)}
              theme={theme}
            />
            <SliderSetting
              title="Braking Threshold"
              subtitle="Sensitivity for excessive braking detection"
              value={Math.abs(settings.brakingThreshold)}
              minValue={1}
              maxValue={10}
              step={0.5}
              unit="m/s²"
              onValueChange={value => updateSetting('brakingThreshold', -value)}
              theme={theme}
            />
          </View>
        </View>

        {/* Sensor Settings */}
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.textSecondary }]}>SENSOR SETTINGS</Text>
          <View style={[styles.card, { backgroundColor: theme.cardBackground }]}>
            <SliderSetting
              title="Sampling Rate"
              subtitle="How often to read sensor data"
              value={settings.samplingRate}
              minValue={50}
              maxValue={500}
              step={50}
              unit="ms"
              onValueChange={value => updateSetting('samplingRate', value)}
              theme={theme}
            />
            <SliderSetting
              title="Alert Cooldown"
              subtitle="Time between violation alerts"
              value={settings.alertCooldown / 1000}
              minValue={1}
              maxValue={30}
              step={1}
              unit="sec"
              onValueChange={value => updateSetting('alertCooldown', value * 1000)}
              theme={theme}
            />
          </View>
        </View>

        {/* Advanced Features */}
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.textSecondary }]}>
            ADVANCED FEATURES
          </Text>
          <View style={[styles.card, { backgroundColor: theme.cardBackground }]}>
            <ToggleSetting
              title="Sensor Fusion"
              subtitle="Use multiple sensors for better accuracy"
              value={settings.enableSensorFusion}
              onValueChange={value => updateSetting('enableSensorFusion', value)}
              theme={theme}
            />
            <ToggleSetting
              title="Multistage Filtering"
              subtitle="Advanced signal processing for noise reduction"
              value={settings.enableMultistageFiltering}
              onValueChange={value => updateSetting('enableMultistageFiltering', value)}
              theme={theme}
            />
          </View>
        </View>

        {/* Filter Parameters (only show if multistage filtering is enabled) */}
        {settings.enableMultistageFiltering && (
          <View style={styles.section}>
            <Text style={[styles.sectionTitle, { color: theme.textSecondary }]}>
              FILTER PARAMETERS
            </Text>
            <View style={[styles.card, { backgroundColor: theme.cardBackground }]}>
              <SliderSetting
                title="Cutoff Frequency"
                subtitle="Low-pass filter frequency"
                value={settings.cutoffFrequency}
                minValue={0.5}
                maxValue={5}
                step={0.1}
                unit="Hz"
                onValueChange={value => updateSetting('cutoffFrequency', value)}
                theme={theme}
              />
              <SliderSetting
                title="Moving Average Window"
                subtitle="Number of samples for smoothing"
                value={settings.movingAverageWindow}
                minValue={3}
                maxValue={15}
                step={1}
                unit="samples"
                onValueChange={value => updateSetting('movingAverageWindow', value)}
                theme={theme}
              />
            </View>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
  },
  backButton: {
    marginRight: 16,
  },
  headerTitle: {
    flex: 1,
    fontSize: 18,
    fontWeight: '600',
  },
  resetButton: {
    padding: 8,
  },
  scrollView: {
    flex: 1,
  },
  section: {
    marginTop: 24,
  },
  sectionTitle: {
    paddingHorizontal: 16,
    paddingBottom: 8,
    fontSize: 12,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  card: {
    marginHorizontal: 16,
    borderRadius: 12,
    overflow: 'hidden',
  },
  settingItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
  },
  settingContent: {
    flex: 1,
    marginRight: 16,
  },
  settingTitle: {
    fontSize: 16,
    fontWeight: '500',
  },
  settingSubtitle: {
    fontSize: 14,
    marginTop: 2,
  },
  sliderControls: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  sliderButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sliderButtonText: {
    fontSize: 18,
    fontWeight: '600',
  },
  sliderValue: {
    marginHorizontal: 12,
    fontSize: 14,
    fontWeight: '500',
    minWidth: 60,
    textAlign: 'center',
  },
  presetButtons: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    padding: 16,
    gap: 8,
  },
  presetButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1,
  },
  presetButtonText: {
    fontSize: 14,
    fontWeight: '500',
  },
});
