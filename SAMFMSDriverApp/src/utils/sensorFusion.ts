export interface Vector3D {
  x: number;
  y: number;
  z: number;
}

export interface SensorFusionData {
  accelerometer: Vector3D;
  gyroscope?: Vector3D;
  magnetometer?: Vector3D;
  timestamp: number;
}

export interface CalibrationData {
  gravityVector: Vector3D;
  deviceBias: Vector3D;
  orientationMatrix: number[][];
  isCalibrated: boolean;
  deviceOrientation: DeviceOrientation;
  drivingAxis: 'x' | 'y' | 'z';
}

export interface DeviceOrientation {
  primary: 'x' | 'y' | 'z'; // Axis with strongest gravity component
  secondary: 'x' | 'y' | 'z'; // Second strongest
  tertiary: 'x' | 'y' | 'z'; // Weakest (likely the driving axis)
  confidence: number; // 0-1 confidence in orientation detection
  description: string; // Human readable description
}

export interface ProcessedAcceleration {
  raw: Vector3D;
  compensated: Vector3D;
  filtered: Vector3D;
  drivingAcceleration: number;
  quality: number; // 0-1 score indicating data quality
}

export class SensorFusion {
  private calibrationData: CalibrationData | null = null;
  private calibrationSamples: Vector3D[] = [];
  private readonly CALIBRATION_SAMPLES = 150; // 15 seconds at 10Hz for more robust calibration
  private readonly MIN_CALIBRATION_SAMPLES = 100; // Minimum samples for basic calibration
  private readonly GRAVITY_MAGNITUDE = 9.81;
  private calibrationStartTime: number = 0;
  private readonly CALIBRATION_TIMEOUT = 30000; // 30 seconds max calibration time

  /**
   * Start calibration process - device should be stationary
   */
  public startCalibration(): void {
    this.calibrationSamples = [];
    this.calibrationData = null;
    this.calibrationStartTime = Date.now();
    console.log('🔧 Starting accelerometer calibration process...');
  }

  /**
   * Add calibration sample during stationary period
   */
  public addCalibrationSample(accelerometerData: Vector3D): boolean {
    if (this.calibrationSamples.length >= this.CALIBRATION_SAMPLES) {
      return false;
    }

    this.calibrationSamples.push({ ...accelerometerData });

    // Check for timeout-based calibration completion
    const timeElapsed = Date.now() - this.calibrationStartTime;
    const hasMinimumSamples = this.calibrationSamples.length >= this.MIN_CALIBRATION_SAMPLES;
    const isTimedOut = timeElapsed >= this.CALIBRATION_TIMEOUT;

    // Force calibration completion after timeout with minimum samples
    if (isTimedOut && hasMinimumSamples) {
      console.warn('🕐 Calibration timeout reached, forcing completion with available samples');
      this.completeCalibration();
      return true;
    }

    // Only complete calibration when we have enough samples AND device is stable
    if (this.calibrationSamples.length >= this.CALIBRATION_SAMPLES) {
      if (this.isDeviceStable()) {
        this.completeCalibration();
        return true;
      } else {
        // Reset if device wasn't stable during full calibration period
        console.warn('Device not stable during calibration, restarting calibration');
        this.calibrationSamples = [];
        this.calibrationStartTime = Date.now();
        return false;
      }
    }

    // For partial calibration, require both minimum samples and stability
    if (this.calibrationSamples.length >= this.MIN_CALIBRATION_SAMPLES) {
      // Check stability every 20 samples after minimum threshold
      if ((this.calibrationSamples.length - this.MIN_CALIBRATION_SAMPLES) % 20 === 0) {
        if (this.isDeviceStable()) {
          this.completeCalibration();
          return true;
        }
      }
    }

    // Log progress periodically
    if (this.calibrationSamples.length % 50 === 0) {
      console.log(
        `🔧 Calibration progress: ${this.calibrationSamples.length}/${
          this.CALIBRATION_SAMPLES
        } samples (${(timeElapsed / 1000).toFixed(1)}s)`
      );
    }

    return false;
  }

  /**
   * Check if calibration is complete
   */
  public isCalibrated(): boolean {
    return this.calibrationData?.isCalibrated ?? false;
  }

  /**
   * Get calibration progress (0-1)
   */
  public getCalibrationProgress(): number {
    return Math.min(this.calibrationSamples.length / this.CALIBRATION_SAMPLES, 1);
  }

  /**
   * Process sensor fusion data with gravity compensation
   */
  public processFusedData(
    accelerometerData: Vector3D,
    gyroscopeData?: Vector3D,
    _magnetometerData?: Vector3D
  ): ProcessedAcceleration {
    const raw = { ...accelerometerData };

    // Apply gravity compensation if calibrated
    const compensated = this.isCalibrated() ? this.compensateGravity(raw) : raw;

    // Calculate data quality score
    const quality = this.calculateDataQuality(raw, gyroscopeData);

    // For now, filtered is same as compensated (will be enhanced with multistage filtering)
    const filtered = { ...compensated };

    // Calculate driving-specific acceleration (Z-axis for upright phone)
    const drivingAcceleration = this.calculateDrivingAcceleration(filtered);

    return {
      raw,
      compensated,
      filtered,
      drivingAcceleration,
      quality,
    };
  }

  /**
   * Check if device appears stable based on recent calibration samples
   * Relaxed for in-vehicle calibration during driving
   */
  private isDeviceStable(): boolean {
    if (this.calibrationSamples.length < 30) {
      return false;
    }

    // Check variance in the last 30 samples for better stability assessment
    const recentSamples = this.calibrationSamples.slice(-30);

    // Calculate mean
    const mean = {
      x: recentSamples.reduce((sum, sample) => sum + sample.x, 0) / recentSamples.length,
      y: recentSamples.reduce((sum, sample) => sum + sample.y, 0) / recentSamples.length,
      z: recentSamples.reduce((sum, sample) => sum + sample.z, 0) / recentSamples.length,
    };

    // Calculate variance
    const variance = {
      x:
        recentSamples.reduce((sum, sample) => sum + Math.pow(sample.x - mean.x, 2), 0) /
        recentSamples.length,
      y:
        recentSamples.reduce((sum, sample) => sum + Math.pow(sample.y - mean.y, 2), 0) /
        recentSamples.length,
      z:
        recentSamples.reduce((sum, sample) => sum + Math.pow(sample.z - mean.z, 2), 0) /
        recentSamples.length,
    };

    // More relaxed stability threshold for in-vehicle calibration
    const stabilityThreshold = 0.3; // Increased from 0.05 to 0.3 m/s² for moving vehicle

    // Also check that the magnitude is in a reasonable range (relaxed gravity check)
    const magnitude = Math.sqrt(mean.x * mean.x + mean.y * mean.y + mean.z * mean.z);
    const gravityCheck = Math.abs(magnitude - this.GRAVITY_MAGNITUDE) < 3.0; // Within 3 m/s² of gravity (relaxed from 1.0)

    const isStable =
      variance.x < stabilityThreshold &&
      variance.y < stabilityThreshold &&
      variance.z < stabilityThreshold &&
      gravityCheck;

    if (!isStable && this.calibrationSamples.length >= this.MIN_CALIBRATION_SAMPLES) {
      console.warn(
        '🔧 Device stability check - variance:',
        {
          x: variance.x.toFixed(3),
          y: variance.y.toFixed(3),
          z: variance.z.toFixed(3),
          threshold: stabilityThreshold,
        },
        'magnitude:',
        magnitude.toFixed(2),
        'gravity_diff:',
        Math.abs(magnitude - this.GRAVITY_MAGNITUDE).toFixed(2)
      );
    } else {
      console.log('✅ Device stability check passed for calibration');
    }

    return isStable;
  }

  /**
   * Complete calibration by calculating gravity vector and bias
   */
  private completeCalibration(): void {
    if (this.calibrationSamples.length < this.MIN_CALIBRATION_SAMPLES) {
      return;
    }

    // Calculate average gravity vector
    const avgGravity = this.calibrationSamples.reduce(
      (acc, sample) => ({
        x: acc.x + sample.x,
        y: acc.y + sample.y,
        z: acc.z + sample.z,
      }),
      { x: 0, y: 0, z: 0 }
    );

    avgGravity.x /= this.calibrationSamples.length;
    avgGravity.y /= this.calibrationSamples.length;
    avgGravity.z /= this.calibrationSamples.length;

    // Detect device orientation based on gravity vector
    const deviceOrientation = this.detectDeviceOrientation(avgGravity);

    // Calculate device bias (difference from expected gravity magnitude)
    const gravityMagnitude = Math.sqrt(
      avgGravity.x * avgGravity.x + avgGravity.y * avgGravity.y + avgGravity.z * avgGravity.z
    );

    const biasScale = gravityMagnitude - this.GRAVITY_MAGNITUDE;

    // Create identity matrix for now (can be enhanced with gyroscope data)
    const orientationMatrix = [
      [1, 0, 0],
      [0, 1, 0],
      [0, 0, 1],
    ];

    this.calibrationData = {
      gravityVector: avgGravity,
      deviceBias: {
        x: avgGravity.x * (biasScale / gravityMagnitude),
        y: avgGravity.y * (biasScale / gravityMagnitude),
        z: avgGravity.z * (biasScale / gravityMagnitude),
      },
      orientationMatrix,
      isCalibrated: true,
      deviceOrientation,
      drivingAxis: deviceOrientation.tertiary, // Use the axis with weakest gravity as driving axis
    };

    console.log('🎯 Sensor calibration completed:', {
      gravityVector: this.calibrationData.gravityVector,
      gravityMagnitude: gravityMagnitude.toFixed(2),
      bias: this.calibrationData.deviceBias,
      orientation: deviceOrientation.description,
      drivingAxis: deviceOrientation.tertiary,
      confidence: (deviceOrientation.confidence * 100).toFixed(0) + '%',
      samples: this.calibrationSamples.length,
    });
  }

  /**
   * Compensate for gravity and device bias with improved logic
   */
  private compensateGravity(raw: Vector3D): Vector3D {
    if (!this.calibrationData) {
      return raw;
    }

    const { gravityVector, deviceBias } = this.calibrationData;

    // Improved gravity compensation accounting for potential rotation
    // Calculate current gravity magnitude to detect if device has rotated significantly
    const currentMagnitude = Math.sqrt(raw.x * raw.x + raw.y * raw.y + raw.z * raw.z);
    const calibratedMagnitude = Math.sqrt(
      gravityVector.x * gravityVector.x +
        gravityVector.y * gravityVector.y +
        gravityVector.z * gravityVector.z
    );

    // If the magnitude has changed significantly, device may have rotated
    const magnitudeRatio = currentMagnitude / calibratedMagnitude;

    // Apply adaptive compensation based on magnitude ratio
    if (magnitudeRatio > 0.8 && magnitudeRatio < 1.2) {
      // Normal compensation when magnitudes are similar
      return {
        x: raw.x - gravityVector.x - deviceBias.x,
        y: raw.y - gravityVector.y - deviceBias.y,
        z: raw.z - gravityVector.z - deviceBias.z,
      };
    } else {
      // Device may have rotated - use magnitude-based compensation
      const normalizedGravity = {
        x: gravityVector.x / calibratedMagnitude,
        y: gravityVector.y / calibratedMagnitude,
        z: gravityVector.z / calibratedMagnitude,
      };

      const projectedGravity = {
        x: normalizedGravity.x * currentMagnitude,
        y: normalizedGravity.y * currentMagnitude,
        z: normalizedGravity.z * currentMagnitude,
      };

      return {
        x: raw.x - projectedGravity.x - deviceBias.x,
        y: raw.y - projectedGravity.y - deviceBias.y,
        z: raw.z - projectedGravity.z - deviceBias.z,
      };
    }
  }

  /**
   * Calculate driving-specific acceleration from compensated data
   */
  private calculateDrivingAcceleration(compensated: Vector3D): number {
    if (!this.calibrationData || !this.calibrationData.drivingAxis) {
      // Use magnitude when orientation is unknown - this is more reliable
      // than assuming any specific axis
      return Math.sqrt(
        compensated.x * compensated.x +
          compensated.y * compensated.y +
          compensated.z * compensated.z
      );
    }

    // Use the axis determined during calibration with improved confidence weighting
    const axis = this.calibrationData.drivingAxis;
    const confidence = this.calibrationData.deviceOrientation.confidence;

    let primaryAcceleration: number;

    // Get the primary axis acceleration WITH SIGN for proper acceleration/braking detection
    switch (axis) {
      case 'x':
        primaryAcceleration = compensated.x; // Keep sign to distinguish acceleration vs braking
        break;
      case 'y':
        primaryAcceleration = compensated.y; // Keep sign to distinguish acceleration vs braking
        break;
      case 'z':
        primaryAcceleration = compensated.z; // Keep sign to distinguish acceleration vs braking
        break;
      default:
        // Fallback to magnitude (this will always be positive)
        primaryAcceleration = Math.sqrt(
          compensated.x * compensated.x +
            compensated.y * compensated.y +
            compensated.z * compensated.z
        );
    }

    // Improved confidence blending - use magnitude as baseline for low confidence
    if (confidence < 0.8) {
      // Increased threshold from 0.7 to 0.8 for better reliability
      const magnitude = Math.sqrt(
        compensated.x * compensated.x +
          compensated.y * compensated.y +
          compensated.z * compensated.z
      );

      // For low confidence, blend signed axis value with magnitude
      // This preserves sign when possible but falls back to magnitude for very low confidence
      const blendFactor = Math.max(0.3, confidence); // Minimum 30% weight on detected axis
      if (axis !== 'x' && axis !== 'y' && axis !== 'z') {
        // If no valid axis detected, use magnitude
        primaryAcceleration = magnitude;
      } else {
        // Blend signed axis value with unsigned magnitude
        // Use the sign of the axis but adjust magnitude based on confidence
        const signedAxisValue = primaryAcceleration;
        const axisSign = Math.sign(signedAxisValue);
        const axisMagnitude = Math.abs(signedAxisValue);
        const blendedMagnitude = blendFactor * axisMagnitude + (1 - blendFactor) * magnitude;
        primaryAcceleration = axisSign * blendedMagnitude;
      }
    }

    return primaryAcceleration;
  }

  /**
   * Calculate data quality score based on sensor stability and fusion
   */
  private calculateDataQuality(accelerometer: Vector3D, gyroscope?: Vector3D): number {
    let quality = 0.5; // Base quality - reduced from 0.7 to be more conservative

    // Boost quality if we have gyroscope data
    if (gyroscope) {
      quality += 0.2;
    }

    // Boost quality if calibrated
    if (this.isCalibrated()) {
      quality += 0.2;
    }

    // Reduce quality for very high magnitude readings (potential shaking/vibration)
    const magnitude = Math.sqrt(
      accelerometer.x * accelerometer.x +
        accelerometer.y * accelerometer.y +
        accelerometer.z * accelerometer.z
    );

    // Improved thresholds based on realistic driving scenarios
    if (magnitude > 25) {
      // Extremely high readings suggest very poor conditions or device issues
      quality *= 0.3;
    } else if (magnitude > 20) {
      // Very high readings suggest poor conditions
      quality *= 0.5;
    } else if (magnitude > 15) {
      // High readings but potentially still valid during aggressive driving
      quality *= 0.7;
    } else if (magnitude < 5) {
      // Very low readings might indicate sensor issues
      quality *= 0.8;
    }

    // Additional quality factors
    if (this.calibrationData) {
      // Boost quality based on orientation confidence
      const orientationConfidence = this.calibrationData.deviceOrientation.confidence;
      quality *= 0.5 + 0.5 * orientationConfidence;
    }

    return Math.max(0, Math.min(1, quality));
  }

  /**
   * Detect device orientation based on gravity vector
   */
  private detectDeviceOrientation(gravity: Vector3D): DeviceOrientation {
    const absX = Math.abs(gravity.x);
    const absY = Math.abs(gravity.y);
    const absZ = Math.abs(gravity.z);

    // Sort axes by strength of gravity component
    const axes = [
      { axis: 'x', value: absX, component: gravity.x },
      { axis: 'y', value: absY, component: gravity.y },
      { axis: 'z', value: absZ, component: gravity.z },
    ].sort((a, b) => b.value - a.value);

    const primary = axes[0];
    const secondary = axes[1];
    const tertiary = axes[2];

    // Calculate confidence based on how clearly separated the primary axis is
    const confidence = (primary.value - secondary.value) / primary.value;

    // Determine orientation description
    let description = 'Unknown';
    if (primary.axis === 'z' && primary.component > 0) {
      description = 'Portrait (Face Up)';
    } else if (primary.axis === 'z' && primary.component < 0) {
      description = 'Portrait (Face Down)';
    } else if (primary.axis === 'y' && primary.component > 0) {
      description = 'Landscape (Top Up)';
    } else if (primary.axis === 'y' && primary.component < 0) {
      description = 'Landscape (Top Down)';
    } else if (primary.axis === 'x') {
      description = primary.component > 0 ? 'Landscape (Right Up)' : 'Landscape (Left Up)';
    }

    return {
      primary: primary.axis as 'x' | 'y' | 'z',
      secondary: secondary.axis as 'x' | 'y' | 'z',
      tertiary: tertiary.axis as 'x' | 'y' | 'z',
      confidence,
      description,
    };
  }

  /**
   * Reset calibration data
   */
  public resetCalibration(): void {
    this.calibrationData = null;
    this.calibrationSamples = [];
  }

  /**
   * Get current calibration data (for debugging)
   */
  public getCalibrationData(): CalibrationData | null {
    return this.calibrationData;
  }
}
