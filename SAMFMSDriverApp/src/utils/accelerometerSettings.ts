import AsyncStorage from '@react-native-async-storage/async-storage';

export interface AccelerometerSettings {
  accelerationThreshold: number;
  brakingThreshold: number;
  samplingRate: number;
  smoothingFactor: number;
  alertCooldown: number;
  enableSensorFusion: boolean;
  enableMultistageFiltering: boolean;
  processNoise: number;
  measurementNoise: number;
  cutoffFrequency: number;
  movingAverageWindow: number;
}

export const DEFAULT_ACCELEROMETER_SETTINGS: AccelerometerSettings = {
  accelerationThreshold: 4.5, // m/s²
  brakingThreshold: -4.5, // m/s²
  samplingRate: 100, // milliseconds
  smoothingFactor: 0.8, // 0-1
  alertCooldown: 10000, // milliseconds
  enableSensorFusion: true,
  enableMultistageFiltering: true,
  processNoise: 0.01, // Kalman filter parameter
  measurementNoise: 0.1, // Kalman filter parameter
  cutoffFrequency: 2.0, // Hz - Butterworth filter
  movingAverageWindow: 5, // samples
};

const STORAGE_KEY = 'SAMFMS_ACCELEROMETER_SETTINGS';

export class AccelerometerSettingsManager {
  private static instance: AccelerometerSettingsManager;
  private settings: AccelerometerSettings = { ...DEFAULT_ACCELEROMETER_SETTINGS };
  private listeners: Array<(settings: AccelerometerSettings) => void> = [];

  public static getInstance(): AccelerometerSettingsManager {
    if (!AccelerometerSettingsManager.instance) {
      AccelerometerSettingsManager.instance = new AccelerometerSettingsManager();
    }
    return AccelerometerSettingsManager.instance;
  }

  /**
   * Load settings from storage
   */
  public async loadSettings(): Promise<AccelerometerSettings> {
    try {
      const storedSettings = await AsyncStorage.getItem(STORAGE_KEY);
      if (storedSettings) {
        const parsed = JSON.parse(storedSettings);
        // Merge with defaults to ensure all properties exist
        this.settings = { ...DEFAULT_ACCELEROMETER_SETTINGS, ...parsed };
      }
    } catch (error) {
      console.warn('Failed to load accelerometer settings:', error);
      this.settings = { ...DEFAULT_ACCELEROMETER_SETTINGS };
    }
    return this.settings;
  }

  /**
   * Save settings to storage
   */
  public async saveSettings(newSettings: Partial<AccelerometerSettings>): Promise<void> {
    try {
      this.settings = { ...this.settings, ...newSettings };
      await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(this.settings));
      this.notifyListeners();
    } catch (error) {
      console.error('Failed to save accelerometer settings:', error);
      throw error;
    }
  }

  /**
   * Get current settings
   */
  public getSettings(): AccelerometerSettings {
    return { ...this.settings };
  }

  /**
   * Reset to default settings
   */
  public async resetToDefaults(): Promise<void> {
    await this.saveSettings(DEFAULT_ACCELEROMETER_SETTINGS);
  }

  /**
   * Subscribe to settings changes
   */
  public subscribe(listener: (settings: AccelerometerSettings) => void): () => void {
    this.listeners.push(listener);
    return () => {
      const index = this.listeners.indexOf(listener);
      if (index > -1) {
        this.listeners.splice(index, 1);
      }
    };
  }

  /**
   * Notify all listeners of settings changes
   */
  private notifyListeners(): void {
    this.listeners.forEach(listener => listener(this.settings));
  }

  /**
   * Validate settings values
   */
  public validateSettings(settings: Partial<AccelerometerSettings>): string[] {
    const errors: string[] = [];

    if (settings.accelerationThreshold !== undefined) {
      if (settings.accelerationThreshold < 1 || settings.accelerationThreshold > 20) {
        errors.push('Acceleration threshold must be between 1 and 20 m/s²');
      }
    }

    if (settings.brakingThreshold !== undefined) {
      if (settings.brakingThreshold > -1 || settings.brakingThreshold < -20) {
        errors.push('Braking threshold must be between -20 and -1 m/s²');
      }
    }

    if (settings.samplingRate !== undefined) {
      if (settings.samplingRate < 50 || settings.samplingRate > 1000) {
        errors.push('Sampling rate must be between 50 and 1000 milliseconds');
      }
    }

    if (settings.smoothingFactor !== undefined) {
      if (settings.smoothingFactor < 0 || settings.smoothingFactor > 1) {
        errors.push('Smoothing factor must be between 0 and 1');
      }
    }

    if (settings.alertCooldown !== undefined) {
      if (settings.alertCooldown < 1000 || settings.alertCooldown > 60000) {
        errors.push('Alert cooldown must be between 1 and 60 seconds');
      }
    }

    if (settings.processNoise !== undefined) {
      if (settings.processNoise < 0.001 || settings.processNoise > 1) {
        errors.push('Process noise must be between 0.001 and 1');
      }
    }

    if (settings.measurementNoise !== undefined) {
      if (settings.measurementNoise < 0.01 || settings.measurementNoise > 10) {
        errors.push('Measurement noise must be between 0.01 and 10');
      }
    }

    if (settings.cutoffFrequency !== undefined) {
      if (settings.cutoffFrequency < 0.5 || settings.cutoffFrequency > 5) {
        errors.push('Cutoff frequency must be between 0.5 and 5 Hz');
      }
    }

    if (settings.movingAverageWindow !== undefined) {
      if (settings.movingAverageWindow < 3 || settings.movingAverageWindow > 20) {
        errors.push('Moving average window must be between 3 and 20 samples');
      }
    }

    return errors;
  }

  /**
   * Get preset configurations
   */
  public getPresets(): { [key: string]: Partial<AccelerometerSettings> } {
    return {
      sensitive: {
        accelerationThreshold: 3.0,
        brakingThreshold: -3.0,
        cutoffFrequency: 1.5,
        movingAverageWindow: 3,
      },
      normal: {
        ...DEFAULT_ACCELEROMETER_SETTINGS,
      },
      relaxed: {
        accelerationThreshold: 6.0,
        brakingThreshold: -6.0,
        cutoffFrequency: 2.5,
        movingAverageWindow: 7,
      },
      performance: {
        samplingRate: 50,
        enableSensorFusion: true,
        enableMultistageFiltering: true,
        processNoise: 0.005,
        measurementNoise: 0.05,
      },
    };
  }
}
