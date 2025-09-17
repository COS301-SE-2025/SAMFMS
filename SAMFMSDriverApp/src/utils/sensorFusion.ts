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
  private readonly CALIBRATION_SAMPLES = 50; // 5 seconds at 10Hz
  private readonly GRAVITY_MAGNITUDE = 9.81;

  /**
   * Start calibration process - device should be stationary
   */
  public startCalibration(): void {
    this.calibrationSamples = [];
    this.calibrationData = null;
  }

  /**
   * Add calibration sample during stationary period
   */
  public addCalibrationSample(accelerometerData: Vector3D): boolean {
    if (this.calibrationSamples.length >= this.CALIBRATION_SAMPLES) {
      return false;
    }

    this.calibrationSamples.push({ ...accelerometerData });

    // Complete calibration when enough samples collected
    if (this.calibrationSamples.length === this.CALIBRATION_SAMPLES) {
      this.completeCalibration();
      return true;
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
   * Complete calibration by calculating gravity vector and bias
   */
  private completeCalibration(): void {
    if (this.calibrationSamples.length < this.CALIBRATION_SAMPLES) {
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
    });
  }

  /**
   * Compensate for gravity and device bias
   */
  private compensateGravity(raw: Vector3D): Vector3D {
    if (!this.calibrationData) {
      return raw;
    }

    const { gravityVector, deviceBias } = this.calibrationData;

    return {
      x: raw.x - gravityVector.x - deviceBias.x,
      y: raw.y - gravityVector.y - deviceBias.y,
      z: raw.z - gravityVector.z - deviceBias.z,
    };
  }

  /**
   * Calculate driving-specific acceleration from compensated data
   */
  private calculateDrivingAcceleration(compensated: Vector3D): number {
    if (!this.calibrationData || !this.calibrationData.drivingAxis) {
      // Fallback to Z-axis if no calibration data
      return compensated.z;
    }

    // Use the axis determined during calibration
    const axis = this.calibrationData.drivingAxis;
    switch (axis) {
      case 'x':
        return compensated.x;
      case 'y':
        return compensated.y;
      case 'z':
        return compensated.z;
      default:
        return compensated.z;
    }
  }

  /**
   * Calculate data quality score based on sensor stability and fusion
   */
  private calculateDataQuality(accelerometer: Vector3D, gyroscope?: Vector3D): number {
    let quality = 0.7; // Base quality

    // Boost quality if we have gyroscope data
    if (gyroscope) {
      quality += 0.2;
    }

    // Boost quality if calibrated
    if (this.isCalibrated()) {
      quality += 0.1;
    }

    // Reduce quality for very high magnitude readings (potential shaking/vibration)
    const magnitude = Math.sqrt(
      accelerometer.x * accelerometer.x +
        accelerometer.y * accelerometer.y +
        accelerometer.z * accelerometer.z
    );

    if (magnitude > 20) {
      // Very high readings suggest poor conditions
      quality *= 0.5;
    } else if (magnitude > 15) {
      quality *= 0.8;
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
