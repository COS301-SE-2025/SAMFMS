import { Vector3D } from './sensorFusion';

export interface FilterState {
  kalman: KalmanFilterState;
  butterworth: ButterworthFilterState;
  movingAverage: MovingAverageState;
}

export interface KalmanFilterState {
  x: number; // estimated value
  P: number; // estimation error covariance
  Q: number; // process noise covariance
  R: number; // measurement noise covariance
  K: number; // Kalman gain
}

export interface ButterworthFilterState {
  x1: number;
  x2: number;
  y1: number;
  y2: number;
}

export interface MovingAverageState {
  buffer: number[];
  sum: number;
  index: number;
  windowSize: number;
}

export class MultistageFilter {
  private xFilter: FilterState;
  private yFilter: FilterState;
  private zFilter: FilterState;

  constructor(
    private processNoise = 0.01,
    private measurementNoise = 0.1,
    private cutoffFrequency = 2.0, // Hz
    private samplingFrequency = 10.0, // Hz
    private movingAverageWindow = 5
  ) {
    this.xFilter = this.initializeFilterState();
    this.yFilter = this.initializeFilterState();
    this.zFilter = this.initializeFilterState();
  }

  /**
   * Apply multistage filtering to accelerometer data
   */
  public filter(input: Vector3D): Vector3D {
    return {
      x: this.filterAxis(input.x, this.xFilter),
      y: this.filterAxis(input.y, this.yFilter),
      z: this.filterAxis(input.z, this.zFilter),
    };
  }

  /**
   * Reset all filter states
   */
  public reset(): void {
    this.xFilter = this.initializeFilterState();
    this.yFilter = this.initializeFilterState();
    this.zFilter = this.initializeFilterState();
  }

  /**
   * Update filter parameters
   */
  public updateParameters(
    processNoise?: number,
    measurementNoise?: number,
    cutoffFrequency?: number,
    movingAverageWindow?: number
  ): void {
    if (processNoise !== undefined) this.processNoise = processNoise;
    if (measurementNoise !== undefined) this.measurementNoise = measurementNoise;
    if (cutoffFrequency !== undefined) this.cutoffFrequency = cutoffFrequency;
    if (movingAverageWindow !== undefined) {
      this.movingAverageWindow = movingAverageWindow;
      // Reset filters to apply new window size
      this.reset();
    }
  }

  /**
   * Initialize filter state for a single axis
   */
  private initializeFilterState(): FilterState {
    return {
      kalman: {
        x: 0,
        P: 1,
        Q: this.processNoise,
        R: this.measurementNoise,
        K: 0,
      },
      butterworth: {
        x1: 0,
        x2: 0,
        y1: 0,
        y2: 0,
      },
      movingAverage: {
        buffer: new Array(this.movingAverageWindow).fill(0),
        sum: 0,
        index: 0,
        windowSize: this.movingAverageWindow,
      },
    };
  }

  /**
   * Apply three-stage filtering to a single axis
   */
  private filterAxis(input: number, filterState: FilterState): number {
    // Stage 1: Kalman Filter for optimal estimation
    const kalmanFiltered = this.applyKalmanFilter(input, filterState.kalman);

    // Stage 2: Butterworth Low-Pass Filter for frequency domain filtering
    const butterworthFiltered = this.applyButterworthFilter(
      kalmanFiltered,
      filterState.butterworth
    );

    // Stage 3: Moving Average for final smoothing
    const smoothed = this.applyMovingAverage(butterworthFiltered, filterState.movingAverage);

    return smoothed;
  }

  /**
   * Apply Kalman filter for optimal state estimation
   */
  private applyKalmanFilter(measurement: number, state: KalmanFilterState): number {
    // Prediction step
    // x_pred = x_prev (assuming constant acceleration model)
    // P_pred = P_prev + Q
    state.P += state.Q;

    // Update step
    // K = P_pred / (P_pred + R)
    state.K = state.P / (state.P + state.R);

    // x = x_pred + K * (measurement - x_pred)
    state.x = state.x + state.K * (measurement - state.x);

    // P = (1 - K) * P_pred
    state.P = (1 - state.K) * state.P;

    return state.x;
  }

  /**
   * Apply second-order Butterworth low-pass filter
   */
  private applyButterworthFilter(input: number, state: ButterworthFilterState): number {
    // Calculate filter coefficients based on cutoff frequency
    const omega = (2 * Math.PI * this.cutoffFrequency) / this.samplingFrequency;
    const sin = Math.sin(omega);
    const cos = Math.cos(omega);
    const alpha = sin / Math.sqrt(2);

    const b0 = (1 - cos) / 2;
    const b1 = 1 - cos;
    const b2 = (1 - cos) / 2;
    const a0 = 1 + alpha;
    const a1 = -2 * cos;
    const a2 = 1 - alpha;

    // Normalize coefficients
    const nb0 = b0 / a0;
    const nb1 = b1 / a0;
    const nb2 = b2 / a0;
    const na1 = a1 / a0;
    const na2 = a2 / a0;

    // Apply difference equation: y[n] = b0*x[n] + b1*x[n-1] + b2*x[n-2] - a1*y[n-1] - a2*y[n-2]
    const output = nb0 * input + nb1 * state.x1 + nb2 * state.x2 - na1 * state.y1 - na2 * state.y2;

    // Update state
    state.x2 = state.x1;
    state.x1 = input;
    state.y2 = state.y1;
    state.y1 = output;

    return output;
  }

  /**
   * Apply moving average filter for final smoothing
   */
  private applyMovingAverage(input: number, state: MovingAverageState): number {
    // Remove old value from sum
    state.sum -= state.buffer[state.index];

    // Add new value
    state.buffer[state.index] = input;
    state.sum += input;

    // Move to next position
    state.index = (state.index + 1) % state.windowSize;

    // Return average
    return state.sum / state.windowSize;
  }

  /**
   * Get current filter state (for debugging)
   */
  public getFilterState(): {
    x: FilterState;
    y: FilterState;
    z: FilterState;
  } {
    return {
      x: this.xFilter,
      y: this.yFilter,
      z: this.zFilter,
    };
  }
}
