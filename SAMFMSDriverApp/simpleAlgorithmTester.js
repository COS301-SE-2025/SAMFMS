/**
 * Simplified Algorithm Tester for Real Data
 * Processes real CSV data and calculates violations without React Native dependencies
 */
class SimpleAlgorithmTester {
  constructor(settings) {
    this.settings = {
      accelerationThreshold: 6.5,
      brakingThreshold: -6.5,
      qualityThreshold: 0.6,
      calibrationPeriod: 15000, // 15 seconds
      alertCooldown: 2000, // 2 seconds
      enableFiltering: true,
      ...settings,
    };

    this.gravityVector = { x: 0, y: 0, z: -9.81 };
    this.isCalibrated = false;
    this.calibrationSamples = [];
  }

  /**
   * Test algorithm on a dataset
   */
  async testDataset(dataset) {
    console.log(`  Testing ${dataset.name} (${dataset.type} driving)...`);

    this.reset();
    const violations = [];
    const qualityScores = [];
    let samplesProcessed = 0;
    let samplesSkipped = 0;
    let lastViolationTime = 0;
    let calibrationTime = 0;

    const startTime = dataset.data[0]?.timestamp || 0;

    for (const sample of dataset.data) {
      const relativeTime = sample.timestamp - startTime;

      // Calibration phase
      if (!this.isCalibrated && relativeTime < this.settings.calibrationPeriod) {
        this.addCalibrationSample(sample.accelerometer);
        if (this.calibrationSamples.length >= 150) {
          // 15 seconds at ~10Hz
          this.performCalibration();
          calibrationTime = relativeTime;
        }
        continue;
      }

      // Process sample
      const processed = this.processSample(sample);
      samplesProcessed++;
      qualityScores.push(processed.quality);

      // Skip low quality samples
      if (processed.quality < this.settings.qualityThreshold) {
        samplesSkipped++;
        continue;
      }

      // Check for violations with cooldown
      if (sample.timestamp - lastViolationTime >= this.settings.alertCooldown) {
        const violation = this.checkViolation(processed, sample.timestamp);
        if (violation) {
          violations.push(violation);
          lastViolationTime = sample.timestamp;
        }
      }
    }

    const durationMinutes = dataset.duration / 60000;
    const avgQuality =
      qualityScores.length > 0
        ? qualityScores.reduce((a, b) => a + b, 0) / qualityScores.length
        : 0;

    return {
      sessionName: dataset.name,
      behaviorType: dataset.type,
      duration: dataset.duration,
      totalSamples: dataset.data.length,

      // Calibration metrics
      calibrationTime,
      calibrationSuccess: this.isCalibrated,

      // Violation metrics
      violations,
      totalViolations: violations.length,
      violationRate: durationMinutes > 0 ? violations.length / durationMinutes : 0,

      // Quality metrics
      averageQuality: avgQuality,
      lowQualityPercentage: samplesProcessed > 0 ? (samplesSkipped / samplesProcessed) * 100 : 0,

      // Performance metrics
      samplesProcessed,
      samplesSkipped,
    };
  }

  /**
   * Reset algorithm state
   */
  reset() {
    this.isCalibrated = false;
    this.calibrationSamples = [];
    this.gravityVector = { x: 0, y: 0, z: -9.81 };
  }

  /**
   * Add calibration sample
   */
  addCalibrationSample(accelerometer) {
    this.calibrationSamples.push(accelerometer);
  }

  /**
   * Perform gravity calibration
   */
  performCalibration() {
    if (this.calibrationSamples.length < 50) return;

    // Calculate average acceleration during stationary period
    const avgX =
      this.calibrationSamples.reduce((sum, s) => sum + s.x, 0) / this.calibrationSamples.length;
    const avgY =
      this.calibrationSamples.reduce((sum, s) => sum + s.y, 0) / this.calibrationSamples.length;
    const avgZ =
      this.calibrationSamples.reduce((sum, s) => sum + s.z, 0) / this.calibrationSamples.length;

    this.gravityVector = { x: avgX, y: avgY, z: avgZ };
    this.isCalibrated = true;
  }

  /**
   * Process a single sensor sample
   */
  processSample(sample) {
    const accel = sample.accelerometer;
    const gyro = sample.gyroscope;

    // Remove gravity component
    const linearAccel = {
      x: accel.x - this.gravityVector.x,
      y: accel.y - this.gravityVector.y,
      z: accel.z - this.gravityVector.z,
    };

    // Calculate driving acceleration (improved algorithm)
    let drivingAcceleration;

    if (this.isCalibrated && this.settings.enableFiltering) {
      // Use dominant horizontal axis (improved)
      const horizontalMag = Math.sqrt(
        linearAccel.x * linearAccel.x + linearAccel.y * linearAccel.y
      );
      const verticalMag = Math.abs(linearAccel.z);

      if (horizontalMag > verticalMag) {
        drivingAcceleration = Math.sqrt(
          linearAccel.x * linearAccel.x + linearAccel.y * linearAccel.y
        );
        if (linearAccel.x < 0) drivingAcceleration = -drivingAcceleration; // Braking
      } else {
        drivingAcceleration = linearAccel.z;
      }
    } else {
      // Fallback to magnitude-based (baseline)
      const magnitude = Math.sqrt(accel.x * accel.x + accel.y * accel.y + accel.z * accel.z);
      drivingAcceleration = magnitude - 9.81;
    }

    // Calculate quality score
    const gyroMagnitude = Math.sqrt(gyro.x * gyro.x + gyro.y * gyro.y + gyro.z * gyro.z);
    const quality = this.calculateQuality(accel, gyro, gyroMagnitude);

    return {
      drivingAcceleration,
      quality,
      linearAccel,
      timestamp: sample.timestamp,
    };
  }

  /**
   * Calculate data quality score
   */
  calculateQuality(accel, gyro, gyroMagnitude) {
    // Improved quality assessment
    const accelMagnitude = Math.sqrt(accel.x * accel.x + accel.y * accel.y + accel.z * accel.z);

    // Check for reasonable accelerometer values (should be around 9.8 m/s² at rest)
    const gravityDeviation = Math.abs(accelMagnitude - 9.81) / 9.81;
    let qualityScore = Math.max(0, 1 - gravityDeviation);

    // Penalize excessive gyroscope noise
    if (gyroMagnitude > 2.0) {
      // 2 rad/s threshold
      qualityScore *= 0.7;
    }

    // Boost quality if calibrated
    if (this.isCalibrated) {
      qualityScore = Math.min(1.0, qualityScore * 1.2);
    }

    return qualityScore;
  }

  /**
   * Check for driving violations
   */
  checkViolation(processed, timestamp) {
    const acceleration = processed.drivingAcceleration;

    if (acceleration > this.settings.accelerationThreshold) {
      return {
        timestamp,
        type: 'acceleration',
        value: acceleration,
        threshold: this.settings.accelerationThreshold,
        quality: processed.quality,
      };
    } else if (acceleration < this.settings.brakingThreshold) {
      return {
        timestamp,
        type: 'braking',
        value: acceleration,
        threshold: this.settings.brakingThreshold,
        quality: processed.quality,
      };
    }

    return null;
  }

  /**
   * Calculate validation metrics for a set of results
   */
  static calculateValidationMetrics(results) {
    const safeResults = results.filter(r => r.behaviorType === 'safe');
    const riskyResults = results.filter(r => r.behaviorType === 'risky');

    // Classification threshold: 5 violations per minute
    const VIOLATION_THRESHOLD = 5;

    const truePositives = riskyResults.filter(r => r.violationRate >= VIOLATION_THRESHOLD).length;
    const falsePositives = safeResults.filter(r => r.violationRate >= VIOLATION_THRESHOLD).length;
    const trueNegatives = safeResults.filter(r => r.violationRate < VIOLATION_THRESHOLD).length;
    const falseNegatives = riskyResults.filter(r => r.violationRate < VIOLATION_THRESHOLD).length;

    const total = results.length;
    const accuracy = total > 0 ? (truePositives + trueNegatives) / total : 0;
    const precision =
      truePositives + falsePositives > 0 ? truePositives / (truePositives + falsePositives) : 0;
    const recall =
      truePositives + falseNegatives > 0 ? truePositives / (truePositives + falseNegatives) : 0;
    const falsePositiveRate =
      falsePositives + trueNegatives > 0 ? falsePositives / (falsePositives + trueNegatives) : 0;

    // Calculate averages
    const avgDataQuality =
      results.length > 0
        ? results.reduce((sum, r) => sum + r.averageQuality, 0) / results.length
        : 0;
    const calibrationSuccessRate =
      results.length > 0 ? results.filter(r => r.calibrationSuccess).length / results.length : 0;

    // Violation rates by category
    const avgViolationRateSafe =
      safeResults.length > 0
        ? safeResults.reduce((sum, r) => sum + r.violationRate, 0) / safeResults.length
        : 0;
    const avgViolationRateRisky =
      riskyResults.length > 0
        ? riskyResults.reduce((sum, r) => sum + r.violationRate, 0) / riskyResults.length
        : 0;

    return {
      accuracy,
      precision,
      recall,
      falsePositiveRate,
      avgDataQuality,
      calibrationSuccessRate,
      violationRateDifference: avgViolationRateRisky - avgViolationRateSafe,
      truePositives,
      falsePositives,
      trueNegatives,
      falseNegatives,
      totalSessions: total,
      safeSessions: safeResults.length,
      riskySessions: riskyResults.length,
      avgViolationRateSafe,
      avgViolationRateRisky,
    };
  }
}

module.exports = { SimpleAlgorithmTester };
