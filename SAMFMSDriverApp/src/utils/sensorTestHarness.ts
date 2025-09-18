import { DatasetSession, ProcessedDatasetEntry } from './datasetLoader';
import { AccelerometerSettings } from './accelerometerSettings';
import { SensorFusion } from './sensorFusion';
import { MultistageFilter } from './multistageFilter';

export interface ViolationEvent {
  timestamp: number;
  type: 'acceleration' | 'braking';
  value: number;
  threshold: number;
  quality: number;
  isCalibrated: boolean;
}

export interface SessionTestResult {
  sessionName: string;
  behaviorType: 'safe' | 'risky';
  duration: number; // milliseconds
  totalSamples: number;

  // Calibration metrics
  calibrationTime: number; // milliseconds to calibrate
  calibrationSuccess: boolean;
  finalCalibrationProgress: number;

  // Violation metrics
  violations: ViolationEvent[];
  accelerationViolations: number;
  brakingViolations: number;
  totalViolations: number;
  violationRate: number; // violations per minute

  // Data quality metrics
  averageQuality: number;
  lowQualityPercentage: number; // percentage of time with quality < 0.6

  // Performance metrics
  processingTime: number; // milliseconds
  samplesProcessed: number;
  samplesSkipped: number; // due to low quality
}

export interface TestConfiguration {
  settings: AccelerometerSettings;
  name: string;
  description: string;
}

export class SensorTestHarness {
  private sensorFusion: SensorFusion;
  private multistageFilter: MultistageFilter | null = null;
  private currentSettings: AccelerometerSettings;

  constructor(settings: AccelerometerSettings) {
    this.currentSettings = settings;
    this.sensorFusion = new SensorFusion();

    if (settings.enableMultistageFiltering) {
      this.multistageFilter = new MultistageFilter(
        settings.processNoise,
        settings.measurementNoise,
        settings.cutoffFrequency,
        10, // 10Hz sampling
        settings.movingAverageWindow
      );
    }
  }

  /**
   * Simulate processing a dataset session with our accelerometer monitoring logic
   */
  public async runSessionTest(session: DatasetSession): Promise<SessionTestResult> {
    const startTime = Date.now();

    // Reset for new session
    this.sensorFusion = new SensorFusion();
    if (this.currentSettings.enableMultistageFiltering) {
      this.multistageFilter = new MultistageFilter(
        this.currentSettings.processNoise,
        this.currentSettings.measurementNoise,
        this.currentSettings.cutoffFrequency,
        10,
        this.currentSettings.movingAverageWindow
      );
    }

    const violations: ViolationEvent[] = [];
    let qualitySum = 0;
    let lowQualityCount = 0;
    let samplesProcessed = 0;
    let samplesSkipped = 0;
    let calibrationTime = 0;
    let lastAlertTime = 0;

    for (const entry of session.data) {
      const processed = this.processDataEntry(entry);
      samplesProcessed++;
      qualitySum += processed.quality;

      // Track calibration time
      if (!this.sensorFusion.isCalibrated() && calibrationTime === 0) {
        calibrationTime = entry.timestamp - session.data[0].timestamp;
      }

      // Check data quality threshold
      if (processed.quality < 0.6) {
        lowQualityCount++;
        samplesSkipped++;
        continue;
      }

      // Check for violations (similar to useAccelerometerMonitoring logic)
      const now = entry.timestamp;
      if (now - lastAlertTime < this.currentSettings.alertCooldown) {
        continue;
      }

      const acceleration = processed.drivingAcceleration;

      if (acceleration > this.currentSettings.accelerationThreshold) {
        violations.push({
          timestamp: entry.timestamp,
          type: 'acceleration',
          value: acceleration,
          threshold: this.currentSettings.accelerationThreshold,
          quality: processed.quality,
          isCalibrated: this.sensorFusion.isCalibrated(),
        });
        lastAlertTime = now;
      } else if (acceleration < this.currentSettings.brakingThreshold) {
        violations.push({
          timestamp: entry.timestamp,
          type: 'braking',
          value: acceleration,
          threshold: this.currentSettings.brakingThreshold,
          quality: processed.quality,
          isCalibrated: this.sensorFusion.isCalibrated(),
        });
        lastAlertTime = now;
      }
    }

    const processingTime = Date.now() - startTime;
    const accelerationViolations = violations.filter(v => v.type === 'acceleration').length;
    const brakingViolations = violations.filter(v => v.type === 'braking').length;
    const durationMinutes = session.duration / 60000;

    return {
      sessionName: session.name,
      behaviorType: session.type,
      duration: session.duration,
      totalSamples: session.totalSamples,

      calibrationTime,
      calibrationSuccess: this.sensorFusion.isCalibrated(),
      finalCalibrationProgress: this.sensorFusion.getCalibrationProgress(),

      violations,
      accelerationViolations,
      brakingViolations,
      totalViolations: violations.length,
      violationRate: durationMinutes > 0 ? violations.length / durationMinutes : 0,

      averageQuality: samplesProcessed > 0 ? qualitySum / samplesProcessed : 0,
      lowQualityPercentage: samplesProcessed > 0 ? (lowQualityCount / samplesProcessed) * 100 : 0,

      processingTime,
      samplesProcessed,
      samplesSkipped,
    };
  }

  /**
   * Process a single data entry (similar to processAccelerometerData in the hook)
   */
  private processDataEntry(entry: ProcessedDatasetEntry) {
    const accelerometerVector = entry.accelerometer;
    const gyroscopeVector = entry.gyroscope;

    let processed;

    if (this.currentSettings.enableSensorFusion) {
      // Use sensor fusion for better accuracy
      processed = this.sensorFusion.processFusedData(accelerometerVector, gyroscopeVector);

      // Add calibration samples during the first few seconds
      if (!this.sensorFusion.isCalibrated()) {
        this.sensorFusion.addCalibrationSample(accelerometerVector);
      }
    } else {
      // Basic processing without sensor fusion - use magnitude of acceleration
      const magnitude = Math.sqrt(
        accelerometerVector.x * accelerometerVector.x +
          accelerometerVector.y * accelerometerVector.y +
          accelerometerVector.z * accelerometerVector.z
      );
      const gravityMagnitude = 9.81;
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
    if (this.currentSettings.enableMultistageFiltering && this.multistageFilter) {
      const filteredVector = this.multistageFilter.filter(processed.compensated);
      finalAcceleration = this.sensorFusion.isCalibrated()
        ? processed.drivingAcceleration
        : Math.sqrt(
            filteredVector.x * filteredVector.x +
              filteredVector.y * filteredVector.y +
              filteredVector.z * filteredVector.z
          ) - 9.81;
    }

    return {
      ...processed,
      drivingAcceleration: finalAcceleration,
    };
  }

  /**
   * Run tests with multiple configurations
   */
  public async runConfigurationComparison(
    sessions: DatasetSession[],
    configurations: TestConfiguration[]
  ): Promise<Map<string, SessionTestResult[]>> {
    const results = new Map<string, SessionTestResult[]>();

    for (const config of configurations) {
      console.log(`Running tests with configuration: ${config.name}`);
      this.currentSettings = config.settings;

      const configResults: SessionTestResult[] = [];
      for (const session of sessions) {
        console.log(`  Testing session: ${session.name}`);
        const result = await this.runSessionTest(session);
        configResults.push(result);
      }

      results.set(config.name, configResults);
    }

    return results;
  }

  /**
   * Generate a summary comparison between safe and risky sessions
   */
  public generateBehaviorComparison(results: SessionTestResult[]) {
    const safeResults = results.filter(r => r.behaviorType === 'safe');
    const riskyResults = results.filter(r => r.behaviorType === 'risky');

    const calculateStats = (data: SessionTestResult[]) => {
      if (data.length === 0) return null;

      const violationRates = data.map(r => r.violationRate);
      const qualities = data.map(r => r.averageQuality);
      const calibrationSuccessRate = data.filter(r => r.calibrationSuccess).length / data.length;

      return {
        count: data.length,
        avgViolationRate: violationRates.reduce((a, b) => a + b, 0) / violationRates.length,
        maxViolationRate: Math.max(...violationRates),
        minViolationRate: Math.min(...violationRates),
        avgQuality: qualities.reduce((a, b) => a + b, 0) / qualities.length,
        calibrationSuccessRate,
        totalViolations: data.reduce((sum, r) => sum + r.totalViolations, 0),
      };
    };

    return {
      safe: calculateStats(safeResults),
      risky: calculateStats(riskyResults),
      summary: {
        totalSessions: results.length,
        safeSessions: safeResults.length,
        riskySessions: riskyResults.length,
      },
    };
  }
}
