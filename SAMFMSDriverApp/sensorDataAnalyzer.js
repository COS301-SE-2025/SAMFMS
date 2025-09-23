/**
 * Sensor Data Analysis Tool
 * Analyzes real datasets to understand acceleration patterns and optimal thresholds
 */

const fs = require('fs');
const path = require('path');
const { RealDatasetLoader } = require('./realDatasetLoader');

class SensorDataAnalyzer {
  constructor() {
    this.loader = new RealDatasetLoader();
  }

  /**
   * Analyze acceleration patterns in datasets
   */
  async analyzeAccelerationPatterns(datasetsPath) {
    console.log('📊 Analyzing acceleration patterns in real datasets...\n');

    const datasets = await this.loader.loadAllDatasets(datasetsPath);
    const analysis = {
      safeDatasets: [],
      riskyDatasets: [],
      overallStats: {},
    };

    for (const dataset of datasets) {
      console.log(`Analyzing ${dataset.name} (${dataset.type})...`);

      const stats = this.analyzeDataset(dataset);

      if (dataset.type === 'safe') {
        analysis.safeDatasets.push(stats);
      } else {
        analysis.riskyDatasets.push(stats);
      }

      this.printDatasetStats(dataset.name, stats);
    }

    // Calculate overall statistics
    analysis.overallStats = this.calculateOverallStats(analysis);
    this.printRecommendations(analysis);

    return analysis;
  }

  /**
   * Analyze a single dataset
   */
  analyzeDataset(dataset) {
    const accelerations = [];
    const linearAccelerations = [];
    const jerks = [];
    const gyroMagnitudes = [];

    // Simple gravity estimation (average of first 150 samples)
    const gravityVector = this.estimateGravity(dataset.data.slice(0, 150));

    for (let i = 0; i < dataset.data.length; i++) {
      const sample = dataset.data[i];
      const accel = sample.accelerometer;
      const gyro = sample.gyroscope;

      // Calculate linear acceleration (gravity removed)
      const linearAccel = {
        x: accel.x - gravityVector.x,
        y: accel.y - gravityVector.y,
        z: accel.z - gravityVector.z,
      };

      // Calculate driving acceleration (using dominant horizontal axis)
      const horizontalMag = Math.sqrt(
        linearAccel.x * linearAccel.x + linearAccel.y * linearAccel.y
      );
      const drivingAccel = linearAccel.x; // Primary forward/backward axis

      accelerations.push(drivingAccel);
      linearAccelerations.push(horizontalMag);

      // Calculate gyroscope magnitude
      const gyroMag = Math.sqrt(gyro.x * gyro.x + gyro.y * gyro.y + gyro.z * gyro.z);
      gyroMagnitudes.push(gyroMag);

      // Calculate jerk (acceleration change rate)
      if (i > 0) {
        const prevAccel = accelerations[i - 1];
        const jerk = Math.abs(drivingAccel - prevAccel);
        jerks.push(jerk);
      }
    }

    return {
      sessionName: dataset.name,
      behaviorType: dataset.type,
      duration: dataset.duration,
      sampleCount: dataset.data.length,

      // Acceleration statistics
      acceleration: this.calculateStats(accelerations),
      linearAcceleration: this.calculateStats(linearAccelerations),
      jerk: this.calculateStats(jerks),
      gyro: this.calculateStats(gyroMagnitudes),

      // Percentile analysis for threshold recommendations
      accelerationPercentiles: this.calculatePercentiles(accelerations.map(Math.abs)),
      jerkPercentiles: this.calculatePercentiles(jerks),

      // Event detection
      significantEvents: this.detectSignificantEvents(accelerations, jerks),
    };
  }

  /**
   * Estimate gravity vector from initial samples
   */
  estimateGravity(samples) {
    if (samples.length === 0) return { x: 0, y: 0, z: -9.81 };

    const avgX = samples.reduce((sum, s) => sum + s.accelerometer.x, 0) / samples.length;
    const avgY = samples.reduce((sum, s) => sum + s.accelerometer.y, 0) / samples.length;
    const avgZ = samples.reduce((sum, s) => sum + s.accelerometer.z, 0) / samples.length;

    return { x: avgX, y: avgY, z: avgZ };
  }

  /**
   * Calculate basic statistics for an array
   */
  calculateStats(values) {
    if (values.length === 0) return { min: 0, max: 0, mean: 0, std: 0 };

    const sorted = [...values].sort((a, b) => a - b);
    const mean = values.reduce((sum, val) => sum + val, 0) / values.length;
    const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / values.length;
    const std = Math.sqrt(variance);

    return {
      min: sorted[0],
      max: sorted[sorted.length - 1],
      mean: mean,
      std: std,
      median: sorted[Math.floor(sorted.length / 2)],
      range: sorted[sorted.length - 1] - sorted[0],
    };
  }

  /**
   * Calculate percentiles for threshold analysis
   */
  calculatePercentiles(values) {
    if (values.length === 0) return {};

    const sorted = [...values].sort((a, b) => a - b);
    const percentiles = [50, 75, 90, 95, 99];
    const result = {};

    percentiles.forEach(p => {
      const index = Math.floor(sorted.length * (p / 100));
      result[`p${p}`] = sorted[Math.min(index, sorted.length - 1)];
    });

    return result;
  }

  /**
   * Detect significant acceleration events
   */
  detectSignificantEvents(accelerations, jerks) {
    const events = {
      strongAcceleration: 0,
      strongBraking: 0,
      highJerk: 0,
      extremeEvents: [],
    };

    const accelThreshold = 3.0; // Lower threshold for analysis
    const jerkThreshold = 2.0;

    for (let i = 0; i < accelerations.length; i++) {
      const accel = accelerations[i];
      const jerk = jerks[i] || 0;

      if (accel > accelThreshold) {
        events.strongAcceleration++;
        if (accel > 5.0) {
          events.extremeEvents.push({ type: 'extreme_accel', value: accel, index: i });
        }
      }

      if (accel < -accelThreshold) {
        events.strongBraking++;
        if (accel < -5.0) {
          events.extremeEvents.push({ type: 'extreme_brake', value: accel, index: i });
        }
      }

      if (jerk > jerkThreshold) {
        events.highJerk++;
      }
    }

    return events;
  }

  /**
   * Calculate overall statistics across all datasets
   */
  calculateOverallStats(analysis) {
    const safe = analysis.safeDatasets;
    const risky = analysis.riskyDatasets;

    const safeAccelStats = this.aggregateStats(safe.map(d => d.acceleration));
    const riskyAccelStats = this.aggregateStats(risky.map(d => d.acceleration));

    const safeJerkStats = this.aggregateStats(safe.map(d => d.jerk));
    const riskyJerkStats = this.aggregateStats(risky.map(d => d.jerk));

    return {
      safe: {
        acceleration: safeAccelStats,
        jerk: safeJerkStats,
        avgEventsPerMin: this.calculateAvgEventsPerMin(safe),
      },
      risky: {
        acceleration: riskyAccelStats,
        jerk: riskyJerkStats,
        avgEventsPerMin: this.calculateAvgEventsPerMin(risky),
      },
    };
  }

  /**
   * Aggregate statistics across multiple datasets
   */
  aggregateStats(statsList) {
    if (statsList.length === 0) return {};

    return {
      avgMean: statsList.reduce((sum, s) => sum + s.mean, 0) / statsList.length,
      avgStd: statsList.reduce((sum, s) => sum + s.std, 0) / statsList.length,
      maxRange: Math.max(...statsList.map(s => s.range)),
      avgMax: statsList.reduce((sum, s) => sum + s.max, 0) / statsList.length,
      avgMin: statsList.reduce((sum, s) => sum + s.min, 0) / statsList.length,
    };
  }

  /**
   * Calculate average events per minute
   */
  calculateAvgEventsPerMin(datasets) {
    const totalEvents = datasets.reduce((sum, d) => {
      const events = d.significantEvents;
      return sum + events.strongAcceleration + events.strongBraking + events.highJerk;
    }, 0);

    const totalMinutes = datasets.reduce((sum, d) => sum + d.duration / 60000, 0);

    return totalMinutes > 0 ? totalEvents / totalMinutes : 0;
  }

  /**
   * Print dataset statistics
   */
  printDatasetStats(name, stats) {
    console.log(`  📈 ${name}:`);
    console.log(`    Duration: ${(stats.duration / 60000).toFixed(1)} min`);
    console.log(
      `    Acceleration range: ${stats.acceleration.min.toFixed(
        2
      )} to ${stats.acceleration.max.toFixed(2)} m/s²`
    );
    console.log(`    Acceleration std: ${stats.acceleration.std.toFixed(2)} m/s²`);
    console.log(`    Jerk 95th percentile: ${stats.jerkPercentiles.p95?.toFixed(2) || 0} m/s³`);
    console.log(
      `    Significant events: ${
        stats.significantEvents.strongAcceleration + stats.significantEvents.strongBraking
      } total`
    );
    console.log(`    Extreme events: ${stats.significantEvents.extremeEvents.length}`);
    console.log('');
  }

  /**
   * Print threshold recommendations
   */
  printRecommendations(analysis) {
    console.log('\n🎯 Threshold Recommendations');
    console.log('═'.repeat(60));

    const safe = analysis.overallStats.safe;
    const risky = analysis.overallStats.risky;

    console.log('\n📊 Acceleration Patterns:');
    console.log(`  Safe driving - Avg std: ${safe.acceleration.avgStd.toFixed(2)} m/s²`);
    console.log(`  Risky driving - Avg std: ${risky.acceleration.avgStd.toFixed(2)} m/s²`);
    console.log(`  Safe driving - Max range: ${safe.acceleration.maxRange.toFixed(2)} m/s²`);
    console.log(`  Risky driving - Max range: ${risky.acceleration.maxRange.toFixed(2)} m/s²`);

    console.log('\n🔧 Recommended Thresholds:');

    // Recommend thresholds based on statistical analysis
    const conservativeThreshold = Math.max(safe.acceleration.avgStd * 3, 2.5);
    const sensitiveThreshold = Math.max(safe.acceleration.avgStd * 2, 1.5);
    const balancedThreshold = Math.max(safe.acceleration.avgStd * 2.5, 2.0);

    console.log(`  Conservative: ±${conservativeThreshold.toFixed(1)} m/s² (low false positives)`);
    console.log(`  Balanced: ±${balancedThreshold.toFixed(1)} m/s² (recommended)`);
    console.log(`  Sensitive: ±${sensitiveThreshold.toFixed(1)} m/s² (high detection)`);

    console.log('\n📈 Event Rates:');
    console.log(`  Safe driving: ${safe.avgEventsPerMin.toFixed(1)} events/min`);
    console.log(`  Risky driving: ${risky.avgEventsPerMin.toFixed(1)} events/min`);

    // Return recommended thresholds
    return {
      conservative: conservativeThreshold,
      balanced: balancedThreshold,
      sensitive: sensitiveThreshold,
    };
  }
}

/**
 * Main analysis execution
 */
async function main() {
  try {
    const analyzer = new SensorDataAnalyzer();
    const datasetsPath = path.join(__dirname, 'datasets');

    const analysis = await analyzer.analyzeAccelerationPatterns(datasetsPath);

    // Export analysis results
    const outputPath = path.join(__dirname, 'test-results', 'sensor-data-analysis.json');
    const resultsDir = path.dirname(outputPath);
    if (!fs.existsSync(resultsDir)) {
      fs.mkdirSync(resultsDir, { recursive: true });
    }

    fs.writeFileSync(outputPath, JSON.stringify(analysis, null, 2));
    console.log(`\n💾 Analysis results exported to: ${outputPath}`);
  } catch (error) {
    console.error('❌ Analysis failed:', error.message);
    process.exit(1);
  }
}

// Run analysis if this file is executed directly
if (require.main === module) {
  main();
}

module.exports = { SensorDataAnalyzer };
