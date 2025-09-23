import { SessionTestResult } from './sensorTestHarness';

export interface ValidationMetrics {
  // Classification performance
  truePositiveRate: number; // Correctly identified risky behavior
  falsePositiveRate: number; // Safe driving flagged as risky
  trueNegativeRate: number; // Correctly identified safe behavior
  falseNegativeRate: number; // Risky driving missed
  accuracy: number; // Overall accuracy
  precision: number; // Precision for risky detection
  recall: number; // Recall for risky detection
  f1Score: number; // F1 score

  // Operational metrics
  avgViolationRateSafe: number;
  avgViolationRateRisky: number;
  violationRateDifference: number;

  // Quality metrics
  avgDataQuality: number;
  calibrationSuccessRate: number;
  avgCalibrationTime: number;

  // Performance metrics
  avgProcessingTime: number;
  samplesSkippedRate: number;
}

export interface ComparisonReport {
  configurationName: string;
  metrics: ValidationMetrics;
  safeSessions: SessionSummary;
  riskySessions: SessionSummary;
  improvements: ImprovementAnalysis;
}

export interface SessionSummary {
  count: number;
  avgViolationRate: number;
  minViolationRate: number;
  maxViolationRate: number;
  stdViolationRate: number;
  avgQuality: number;
  calibrationSuccessRate: number;
  totalViolations: number;
}

export interface ImprovementAnalysis {
  falsePositiveReduction: number; // % reduction compared to baseline
  qualityImprovement: number; // % improvement in data quality
  calibrationImprovement: number; // % improvement in calibration success
  overallScore: number; // Combined improvement score (0-100)
}

export class ValidationMetricsCalculator {
  /**
   * Calculate comprehensive validation metrics for a test configuration
   */
  public calculateMetrics(results: SessionTestResult[]): ValidationMetrics {
    const safeResults = results.filter(r => r.behaviorType === 'safe');
    const riskyResults = results.filter(r => r.behaviorType === 'risky');

    // Define violation rate thresholds for classification
    const VIOLATION_THRESHOLD = 5; // violations per minute

    // Calculate classification metrics
    const truePositives = riskyResults.filter(r => r.violationRate >= VIOLATION_THRESHOLD).length;
    const falsePositives = safeResults.filter(r => r.violationRate >= VIOLATION_THRESHOLD).length;
    const trueNegatives = safeResults.filter(r => r.violationRate < VIOLATION_THRESHOLD).length;
    const falseNegatives = riskyResults.filter(r => r.violationRate < VIOLATION_THRESHOLD).length;

    const total = results.length;
    const accuracy = (truePositives + trueNegatives) / total;
    const precision = truePositives / (truePositives + falsePositives) || 0;
    const recall = truePositives / (truePositives + falseNegatives) || 0;
    const f1Score = (2 * (precision * recall)) / (precision + recall) || 0;

    // Calculate operational metrics
    const avgViolationRateSafe = this.calculateAverage(safeResults.map(r => r.violationRate));
    const avgViolationRateRisky = this.calculateAverage(riskyResults.map(r => r.violationRate));

    // Calculate quality metrics
    const avgDataQuality = this.calculateAverage(results.map(r => r.averageQuality));
    const calibrationSuccessRate =
      results.filter(r => r.calibrationSuccess).length / results.length;
    const avgCalibrationTime = this.calculateAverage(results.map(r => r.calibrationTime));

    // Calculate performance metrics
    const avgProcessingTime = this.calculateAverage(results.map(r => r.processingTime));
    const totalSamples = results.reduce((sum, r) => sum + r.samplesProcessed + r.samplesSkipped, 0);
    const totalSkipped = results.reduce((sum, r) => sum + r.samplesSkipped, 0);
    const samplesSkippedRate = totalSamples > 0 ? (totalSkipped / totalSamples) * 100 : 0;

    return {
      truePositiveRate: truePositives / (truePositives + falseNegatives) || 0,
      falsePositiveRate: falsePositives / (falsePositives + trueNegatives) || 0,
      trueNegativeRate: trueNegatives / (trueNegatives + falsePositives) || 0,
      falseNegativeRate: falseNegatives / (falseNegatives + truePositives) || 0,
      accuracy,
      precision,
      recall,
      f1Score,

      avgViolationRateSafe,
      avgViolationRateRisky,
      violationRateDifference: avgViolationRateRisky - avgViolationRateSafe,

      avgDataQuality,
      calibrationSuccessRate,
      avgCalibrationTime,

      avgProcessingTime,
      samplesSkippedRate,
    };
  }

  /**
   * Generate a detailed session summary
   */
  public generateSessionSummary(results: SessionTestResult[]): SessionSummary {
    if (results.length === 0) {
      return {
        count: 0,
        avgViolationRate: 0,
        minViolationRate: 0,
        maxViolationRate: 0,
        stdViolationRate: 0,
        avgQuality: 0,
        calibrationSuccessRate: 0,
        totalViolations: 0,
      };
    }

    const violationRates = results.map(r => r.violationRate);
    const avgViolationRate = this.calculateAverage(violationRates);
    const stdViolationRate = this.calculateStandardDeviation(violationRates);

    return {
      count: results.length,
      avgViolationRate,
      minViolationRate: Math.min(...violationRates),
      maxViolationRate: Math.max(...violationRates),
      stdViolationRate,
      avgQuality: this.calculateAverage(results.map(r => r.averageQuality)),
      calibrationSuccessRate: results.filter(r => r.calibrationSuccess).length / results.length,
      totalViolations: results.reduce((sum, r) => sum + r.totalViolations, 0),
    };
  }

  /**
   * Compare results against a baseline to calculate improvements
   */
  public calculateImprovements(
    current: ValidationMetrics,
    baseline: ValidationMetrics
  ): ImprovementAnalysis {
    const falsePositiveReduction =
      baseline.falsePositiveRate > 0
        ? ((baseline.falsePositiveRate - current.falsePositiveRate) / baseline.falsePositiveRate) *
          100
        : 0;

    const qualityImprovement =
      baseline.avgDataQuality > 0
        ? ((current.avgDataQuality - baseline.avgDataQuality) / baseline.avgDataQuality) * 100
        : 0;

    const calibrationImprovement =
      baseline.calibrationSuccessRate > 0
        ? ((current.calibrationSuccessRate - baseline.calibrationSuccessRate) /
            baseline.calibrationSuccessRate) *
          100
        : 0;

    // Calculate overall improvement score (weighted average)
    const overallScore = Math.max(
      0,
      Math.min(
        100,
        falsePositiveReduction * 0.4 +
          qualityImprovement * 0.3 +
          calibrationImprovement * 0.2 +
          current.accuracy * 10 // Bonus for high accuracy
      )
    );

    return {
      falsePositiveReduction,
      qualityImprovement,
      calibrationImprovement,
      overallScore,
    };
  }

  /**
   * Generate a comprehensive comparison report
   */
  public generateComparisonReport(
    configName: string,
    results: SessionTestResult[],
    baseline?: ValidationMetrics
  ): ComparisonReport {
    const metrics = this.calculateMetrics(results);
    const safeResults = results.filter(r => r.behaviorType === 'safe');
    const riskyResults = results.filter(r => r.behaviorType === 'risky');

    const safeSessions = this.generateSessionSummary(safeResults);
    const riskySessions = this.generateSessionSummary(riskyResults);

    const improvements = baseline
      ? this.calculateImprovements(metrics, baseline)
      : {
          falsePositiveReduction: 0,
          qualityImprovement: 0,
          calibrationImprovement: 0,
          overallScore: metrics.accuracy * 100,
        };

    return {
      configurationName: configName,
      metrics,
      safeSessions,
      riskySessions,
      improvements,
    };
  }

  /**
   * Generate a formatted text report
   */
  public generateTextReport(report: ComparisonReport): string {
    const { configurationName, metrics, safeSessions, riskySessions, improvements } = report;

    return `
# Driver Behavior Detection Validation Report
## Configuration: ${configurationName}

### Classification Performance
- **Accuracy**: ${(metrics.accuracy * 100).toFixed(1)}%
- **Precision**: ${(metrics.precision * 100).toFixed(1)}%
- **Recall**: ${(metrics.recall * 100).toFixed(1)}%
- **F1 Score**: ${(metrics.f1Score * 100).toFixed(1)}%
- **False Positive Rate**: ${(metrics.falsePositiveRate * 100).toFixed(1)}%

### Behavior Detection Results
#### Safe Driving Sessions (${safeSessions.count} sessions)
- **Average Violation Rate**: ${safeSessions.avgViolationRate.toFixed(2)} violations/min
- **Range**: ${safeSessions.minViolationRate.toFixed(2)} - ${safeSessions.maxViolationRate.toFixed(
      2
    )} violations/min
- **Total Violations**: ${safeSessions.totalViolations}
- **Data Quality**: ${(safeSessions.avgQuality * 100).toFixed(1)}%

#### Risky Driving Sessions (${riskySessions.count} sessions)
- **Average Violation Rate**: ${riskySessions.avgViolationRate.toFixed(2)} violations/min
- **Range**: ${riskySessions.minViolationRate.toFixed(
      2
    )} - ${riskySessions.maxViolationRate.toFixed(2)} violations/min
- **Total Violations**: ${riskySessions.totalViolations}
- **Data Quality**: ${(riskySessions.avgQuality * 100).toFixed(1)}%

### System Performance
- **Calibration Success Rate**: ${(metrics.calibrationSuccessRate * 100).toFixed(1)}%
- **Average Calibration Time**: ${(metrics.avgCalibrationTime / 1000).toFixed(1)} seconds
- **Samples Skipped**: ${metrics.samplesSkippedRate.toFixed(1)}% (due to low quality)
- **Average Processing Time**: ${metrics.avgProcessingTime.toFixed(0)}ms per session

### Improvements Over Baseline
- **False Positive Reduction**: ${improvements.falsePositiveReduction.toFixed(1)}%
- **Data Quality Improvement**: ${improvements.qualityImprovement.toFixed(1)}%
- **Calibration Improvement**: ${improvements.calibrationImprovement.toFixed(1)}%
- **Overall Improvement Score**: ${improvements.overallScore.toFixed(1)}/100

### Key Insights
- Risky sessions show ${
      (riskySessions.avgViolationRate / safeSessions.avgViolationRate - 1) * 100 > 0
        ? `${((riskySessions.avgViolationRate / safeSessions.avgViolationRate - 1) * 100).toFixed(
            0
          )}% more violations`
        : 'comparable violation rates'
    } compared to safe sessions
- Algorithm distinguishes between safe and risky behavior with ${metrics.violationRateDifference.toFixed(
      2
    )} violations/min difference
- ${(metrics.calibrationSuccessRate * 100).toFixed(0)}% of sessions achieved successful calibration
`;
  }

  /**
   * Utility method to calculate average
   */
  private calculateAverage(values: number[]): number {
    if (values.length === 0) return 0;
    return values.reduce((sum, val) => sum + val, 0) / values.length;
  }

  /**
   * Utility method to calculate standard deviation
   */
  private calculateStandardDeviation(values: number[]): number {
    if (values.length === 0) return 0;
    const avg = this.calculateAverage(values);
    const squaredDiffs = values.map(val => Math.pow(val - avg, 2));
    return Math.sqrt(this.calculateAverage(squaredDiffs));
  }
}
