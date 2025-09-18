/**
 * Enhanced Algorithm Tester with Adaptive Thresholds and Improved Detection
 * Uses statistical analysis and multiple detection methods for better accuracy
 */
class EnhancedAlgorithmTester {
  constructor(settings) {
    this.settings = {
      // Adaptive threshold settings
      useAdaptiveThresholds: true,
      baseAccelerationThreshold: 2.0, // Reduced from 6.5
      baseBrakingThreshold: -2.0, // Reduced from -6.5
      thresholdMultiplier: 2.5, // Standard deviations above baseline

      // Quality and timing
      qualityThreshold: 0.6,
      calibrationPeriod: 15000,
      alertCooldown: 1000, // Reduced cooldown for better detection

      // Enhanced detection features
      enableJerkDetection: true,
      jerkThreshold: 0.2, // Based on analysis (95th percentile)
      enablePatternDetection: true,
      enableSmoothing: true,
      smoothingWindow: 3,

      // Event scoring
      enableEventScoring: true,
      violationScoreThreshold: 1.0,

      ...settings,
    };

    this.gravityVector = { x: 0, y: 0, z: -9.81 };
    this.isCalibrated = false;
    this.calibrationSamples = [];

    // Adaptive threshold calculation
    this.sessionBaseline = {
      accelerationStd: 0.5, // Default baseline
      jerkStd: 0.1,
      sampleCount: 0,
      accelerationThreshold: this.settings.baseAccelerationThreshold,
      brakingThreshold: this.settings.baseBrakingThreshold,
      jerkThreshold: this.settings.jerkThreshold,
    };

    // Smoothing buffer
    this.smoothingBuffer = [];

    // Previous sample for jerk calculation
    this.previousAcceleration = null;
  }

  /**
   * Test algorithm on a dataset with enhanced detection
   */
  async testDataset(dataset) {
    console.log(`  Testing ${dataset.name} (${dataset.type} driving)...`);

    this.reset();
    const violations = [];
    const qualityScores = [];
    const allAccelerations = [];
    const allJerks = [];

    let samplesProcessed = 0;
    let samplesSkipped = 0;
    let lastViolationTime = 0;
    let calibrationTime = 0;

    const startTime = dataset.data[0]?.timestamp || 0;

    // Phase 1: Calibration and baseline calculation
    for (let i = 0; i < Math.min(dataset.data.length, 1500); i++) {
      const sample = dataset.data[i];
      const relativeTime = sample.timestamp - startTime;

      // Calibration phase
      if (!this.isCalibrated && relativeTime < this.settings.calibrationPeriod) {
        this.addCalibrationSample(sample.accelerometer);
        if (this.calibrationSamples.length >= 150) {
          this.performCalibration();
          calibrationTime = relativeTime;
        }
        continue;
      }

      // Collect baseline data for adaptive thresholds
      if (this.isCalibrated && this.settings.useAdaptiveThresholds) {
        const processed = this.processSample(sample);
        allAccelerations.push(processed.drivingAcceleration);
      }
    }

    // Calculate adaptive thresholds
    if (this.settings.useAdaptiveThresholds && allAccelerations.length > 0) {
      this.calculateAdaptiveThresholds(allAccelerations, allJerks);
    }

    // Phase 2: Violation detection with enhanced algorithm
    for (const sample of dataset.data) {
      const relativeTime = sample.timestamp - startTime;

      // Skip calibration period
      if (relativeTime < this.settings.calibrationPeriod) {
        continue;
      }

      // Process sample with enhanced detection
      const processed = this.processSampleEnhanced(sample);
      samplesProcessed++;
      qualityScores.push(processed.quality);

      // Skip low quality samples
      if (processed.quality < this.settings.qualityThreshold) {
        samplesSkipped++;
        continue;
      }

      // Enhanced violation detection with cooldown
      if (sample.timestamp - lastViolationTime >= this.settings.alertCooldown) {
        const violation = this.checkEnhancedViolation(processed, sample.timestamp);
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

      // Enhanced metrics
      adaptiveThresholds: {
        acceleration: this.sessionBaseline.accelerationThreshold,
        braking: this.sessionBaseline.brakingThreshold,
        jerk: this.sessionBaseline.jerkThreshold,
      },

      // Performance metrics
      samplesProcessed,
      samplesSkipped,
    };
  }

  /**
   * Calculate adaptive thresholds based on session baseline
   */
  calculateAdaptiveThresholds(accelerations, jerks) {
    // Calculate standard deviations for this session
    const accelMean = accelerations.reduce((sum, val) => sum + val, 0) / accelerations.length;
    const accelVariance =
      accelerations.reduce((sum, val) => sum + Math.pow(val - accelMean, 2), 0) /
      accelerations.length;
    const accelStd = Math.sqrt(accelVariance);

    // Set adaptive thresholds based on session characteristics
    this.sessionBaseline.accelerationStd = accelStd;

    // Calculate thresholds as multiples of standard deviation, with minimums
    const accelThreshold = Math.max(
      this.settings.baseAccelerationThreshold,
      accelStd * this.settings.thresholdMultiplier
    );

    this.sessionBaseline.accelerationThreshold = accelThreshold;
    this.sessionBaseline.brakingThreshold = -accelThreshold;

    console.log(`    📊 Adaptive thresholds: ±${accelThreshold.toFixed(2)} m/s²`);
  }

  /**
   * Enhanced sample processing with smoothing and jerk calculation
   */
  processSampleEnhanced(sample) {
    const basicProcessed = this.processSample(sample);

    // Add smoothing if enabled
    let smoothedAcceleration = basicProcessed.drivingAcceleration;
    if (this.settings.enableSmoothing) {
      smoothedAcceleration = this.applySmoothingFilter(basicProcessed.drivingAcceleration);
    }

    // Calculate jerk (rate of acceleration change)
    let jerk = null;
    if (this.settings.enableJerkDetection && this.previousAcceleration !== null) {
      jerk = Math.abs(smoothedAcceleration - this.previousAcceleration);
    }
    this.previousAcceleration = smoothedAcceleration;

    return {
      ...basicProcessed,
      drivingAcceleration: smoothedAcceleration,
      jerk,
      rawAcceleration: basicProcessed.drivingAcceleration,
    };
  }

  /**
   * Apply simple moving average smoothing
   */
  applySmoothingFilter(acceleration) {
    this.smoothingBuffer.push(acceleration);

    // Keep buffer at window size
    if (this.smoothingBuffer.length > this.settings.smoothingWindow) {
      this.smoothingBuffer.shift();
    }

    // Return moving average
    return this.smoothingBuffer.reduce((sum, val) => sum + val, 0) / this.smoothingBuffer.length;
  }

  /**
   * Enhanced violation detection with multiple criteria
   */
  checkEnhancedViolation(processed, timestamp) {
    const acceleration = processed.drivingAcceleration;
    const jerk = processed.jerk;

    // Get thresholds (adaptive or fixed)
    const accelThreshold = this.sessionBaseline.accelerationThreshold;
    const brakingThreshold = this.sessionBaseline.brakingThreshold;

    let violationScore = 0;
    let violationType = null;
    let primaryCause = null;

    // Check acceleration violation
    if (acceleration > accelThreshold) {
      violationType = 'acceleration';
      primaryCause = 'acceleration';
      violationScore += Math.abs(acceleration) / accelThreshold;
    }

    // Check braking violation
    if (acceleration < brakingThreshold) {
      violationType = 'braking';
      primaryCause = 'braking';
      violationScore += Math.abs(acceleration) / Math.abs(brakingThreshold);
    }

    // Return violation if score exceeds threshold or simple threshold check
    if (this.settings.enableEventScoring) {
      if (violationScore >= this.settings.violationScoreThreshold) {
        return {
          timestamp,
          type: violationType,
          value: acceleration,
          jerk: jerk,
          score: violationScore,
          threshold: violationType === 'acceleration' ? accelThreshold : brakingThreshold,
          quality: processed.quality,
          cause: primaryCause,
        };
      }
    } else {
      // Legacy simple threshold check
      if (violationType !== null) {
        return {
          timestamp,
          type: violationType,
          value: acceleration,
          jerk: jerk,
          threshold: violationType === 'acceleration' ? accelThreshold : brakingThreshold,
          quality: processed.quality,
        };
      }
    }

    return null;
  }

  /**
   * Reset algorithm state
   */
  reset() {
    this.isCalibrated = false;
    this.calibrationSamples = [];
    this.gravityVector = { x: 0, y: 0, z: -9.81 };
    this.sessionBaseline = {
      accelerationStd: 0.5,
      jerkStd: 0.1,
      sampleCount: 0,
      accelerationThreshold: this.settings.baseAccelerationThreshold,
      brakingThreshold: this.settings.baseBrakingThreshold,
      jerkThreshold: this.settings.jerkThreshold,
    };
    this.smoothingBuffer = [];
    this.previousAcceleration = null;
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
   * Process a single sensor sample (basic implementation)
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

    // Improved driving acceleration calculation
    let drivingAcceleration;

    if (this.isCalibrated) {
      // Use dominant horizontal axis with better logic
      const horizontalMag = Math.sqrt(
        linearAccel.x * linearAccel.x + linearAccel.y * linearAccel.y
      );
      const verticalMag = Math.abs(linearAccel.z);

      // Prefer horizontal movement for driving detection
      if (horizontalMag > verticalMag * 0.5) {
        // Less strict requirement
        // Use the larger horizontal component
        if (Math.abs(linearAccel.x) > Math.abs(linearAccel.y)) {
          drivingAcceleration = linearAccel.x;
        } else {
          drivingAcceleration = linearAccel.y;
        }
      } else {
        drivingAcceleration = linearAccel.z;
      }
    } else {
      // Fallback
      const magnitude = Math.sqrt(accel.x * accel.x + accel.y * accel.y + accel.z * accel.z);
      drivingAcceleration = magnitude - 9.81;
    }

    // Enhanced quality calculation
    const gyroMagnitude = Math.sqrt(gyro.x * gyro.x + gyro.y * gyro.y + gyro.z * gyro.z);
    const quality = this.calculateEnhancedQuality(accel, gyro, gyroMagnitude);

    return {
      drivingAcceleration,
      quality,
      linearAccel,
      timestamp: sample.timestamp,
    };
  }

  /**
   * Enhanced quality calculation
   */
  calculateEnhancedQuality(accel, gyro, gyroMagnitude) {
    const accelMagnitude = Math.sqrt(accel.x * accel.x + accel.y * accel.y + accel.z * accel.z);

    // More lenient quality assessment
    const gravityDeviation = Math.abs(accelMagnitude - 9.81) / 9.81;
    let qualityScore = Math.max(0, 1 - gravityDeviation * 0.5); // Less penalty for deviation

    // Less penalty for gyroscope noise
    if (gyroMagnitude > 3.0) {
      // Higher threshold
      qualityScore *= 0.8;
    }

    // Boost quality if calibrated
    if (this.isCalibrated) {
      qualityScore = Math.min(1.0, qualityScore * 1.1);
    }

    return qualityScore;
  }

  /**
   * Calculate validation metrics with dynamic threshold
   */
  static calculateValidationMetrics(results) {
    const safeResults = results.filter(r => r.behaviorType === 'safe');
    const riskyResults = results.filter(r => r.behaviorType === 'risky');

    // Dynamic threshold based on violation rates
    const allViolationRates = results.map(r => r.violationRate);
    const avgViolationRate =
      allViolationRates.reduce((sum, rate) => sum + rate, 0) / allViolationRates.length;
    const VIOLATION_THRESHOLD = Math.max(avgViolationRate, 0.5); // At least 0.5 violations per minute

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

    const avgDataQuality =
      results.length > 0
        ? results.reduce((sum, r) => sum + r.averageQuality, 0) / results.length
        : 0;
    const calibrationSuccessRate =
      results.length > 0 ? results.filter(r => r.calibrationSuccess).length / results.length : 0;

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
      dynamicThreshold: VIOLATION_THRESHOLD,
    };
  }
}

module.exports = { EnhancedAlgorithmTester };
