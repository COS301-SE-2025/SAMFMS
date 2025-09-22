/**
 * Statistical Validation Framework
 * Provides proper statistical testing and validation for algorithm comparison
 */
class StatisticalValidator {
  /**
   * Perform cross-validation on datasets
   */
  static performCrossValidation(datasets, k = 5) {
    const shuffled = this.shuffleArray([...datasets]);
    const foldSize = Math.floor(shuffled.length / k);
    const folds = [];

    for (let i = 0; i < k; i++) {
      const start = i * foldSize;
      const end = i === k - 1 ? shuffled.length : start + foldSize;

      const testSet = shuffled.slice(start, end);
      const trainSet = [...shuffled.slice(0, start), ...shuffled.slice(end)];

      folds.push({ trainSet, testSet, foldIndex: i });
    }

    return folds;
  }

  /**
   * Calculate confidence intervals for metrics
   */
  static calculateConfidenceInterval(values, confidenceLevel = 0.95) {
    if (values.length === 0) return { mean: 0, lower: 0, upper: 0, margin: 0 };

    const mean = this.calculateMean(values);
    const std = this.calculateStandardDeviation(values);
    const n = values.length;

    // Use t-distribution for small samples
    const df = n - 1;
    const alpha = 1 - confidenceLevel;
    const tValue = this.getTValue(df, alpha / 2);

    const marginOfError = tValue * (std / Math.sqrt(n));

    return {
      mean,
      lower: mean - marginOfError,
      upper: mean + marginOfError,
      margin: marginOfError,
      standardError: std / Math.sqrt(n),
    };
  }

  /**
   * Perform paired t-test to compare two algorithms
   */
  static pairedTTest(baseline, improved) {
    if (baseline.length !== improved.length || baseline.length === 0) {
      throw new Error('Arrays must have same non-zero length for paired t-test');
    }

    const differences = baseline.map((b, i) => improved[i] - b);
    const meanDiff = this.calculateMean(differences);
    const stdDiff = this.calculateStandardDeviation(differences);
    const n = differences.length;

    const tStatistic = meanDiff / (stdDiff / Math.sqrt(n));
    const df = n - 1;
    const pValue = this.getTwoTailedP(Math.abs(tStatistic), df);

    return {
      tStatistic,
      degreesOfFreedom: df,
      pValue,
      meanDifference: meanDiff,
      standardError: stdDiff / Math.sqrt(n),
      isSignificant: pValue < 0.05,
      effectSize: meanDiff / stdDiff, // Cohen's d
    };
  }

  /**
   * Calculate effect size (Cohen's d) for practical significance
   */
  static calculateCohenD(baseline, improved) {
    const mean1 = this.calculateMean(baseline);
    const mean2 = this.calculateMean(improved);
    const std1 = this.calculateStandardDeviation(baseline);
    const std2 = this.calculateStandardDeviation(improved);

    const pooledStd = Math.sqrt(
      ((baseline.length - 1) * std1 * std1 + (improved.length - 1) * std2 * std2) /
        (baseline.length + improved.length - 2)
    );

    const cohenD = (mean2 - mean1) / pooledStd;

    let interpretation;
    if (Math.abs(cohenD) < 0.2) interpretation = 'negligible';
    else if (Math.abs(cohenD) < 0.5) interpretation = 'small';
    else if (Math.abs(cohenD) < 0.8) interpretation = 'medium';
    else interpretation = 'large';

    return {
      value: cohenD,
      interpretation,
      magnitude: Math.abs(cohenD),
    };
  }

  /**
   * Bootstrap confidence intervals for robust estimation
   */
  static bootstrapConfidenceInterval(
    data,
    statFunction,
    iterations = 1000,
    confidenceLevel = 0.95
  ) {
    const bootstrapStats = [];

    for (let i = 0; i < iterations; i++) {
      const sample = this.bootstrapSample(data);
      const stat = statFunction(sample);
      bootstrapStats.push(stat);
    }

    bootstrapStats.sort((a, b) => a - b);

    const alpha = 1 - confidenceLevel;
    const lowerIndex = Math.floor((alpha / 2) * iterations);
    const upperIndex = Math.floor((1 - alpha / 2) * iterations);

    return {
      lower: bootstrapStats[lowerIndex],
      upper: bootstrapStats[upperIndex],
      mean: this.calculateMean(bootstrapStats),
      samples: bootstrapStats,
    };
  }

  /**
   * Generate comprehensive statistical report
   */
  static generateStatisticalReport(baselineResults, improvedResults) {
    const baselineAccuracies = baselineResults.map(r => r.accuracy);
    const improvedAccuracies = improvedResults.map(r => r.accuracy);

    const baselineFPRates = baselineResults.map(r => r.falsePositiveRate);
    const improvedFPRates = improvedResults.map(r => r.falsePositiveRate);

    const baselineQualities = baselineResults.map(r => r.avgDataQuality);
    const improvedQualities = improvedResults.map(r => r.avgDataQuality);

    // Statistical tests
    const accuracyTest = this.pairedTTest(baselineAccuracies, improvedAccuracies);
    const fpRateTest = this.pairedTTest(baselineFPRates, improvedFPRates);
    const qualityTest = this.pairedTTest(baselineQualities, improvedQualities);

    // Effect sizes
    const accuracyEffect = this.calculateCohenD(baselineAccuracies, improvedAccuracies);
    const fpRateEffect = this.calculateCohenD(baselineFPRates, improvedFPRates);
    const qualityEffect = this.calculateCohenD(baselineQualities, improvedQualities);

    // Confidence intervals
    const accuracyCI = this.calculateConfidenceInterval(improvedAccuracies);
    const fpRateCI = this.calculateConfidenceInterval(improvedFPRates);
    const qualityCI = this.calculateConfidenceInterval(improvedQualities);

    return {
      sampleSize: baselineResults.length,
      statisticalTests: {
        accuracy: {
          ...accuracyTest,
          baseline: this.calculateConfidenceInterval(baselineAccuracies),
          improved: accuracyCI,
          effectSize: accuracyEffect,
        },
        falsePositiveRate: {
          ...fpRateTest,
          baseline: this.calculateConfidenceInterval(baselineFPRates),
          improved: fpRateCI,
          effectSize: fpRateEffect,
        },
        dataQuality: {
          ...qualityTest,
          baseline: this.calculateConfidenceInterval(baselineQualities),
          improved: qualityCI,
          effectSize: qualityEffect,
        },
      },
      overallSignificance: {
        anySignificant:
          accuracyTest.isSignificant || fpRateTest.isSignificant || qualityTest.isSignificant,
        significantMetrics: [
          accuracyTest.isSignificant ? 'accuracy' : null,
          fpRateTest.isSignificant ? 'falsePositiveRate' : null,
          qualityTest.isSignificant ? 'dataQuality' : null,
        ].filter(Boolean),
        practicalSignificance: {
          accuracy: accuracyEffect.interpretation,
          falsePositiveRate: fpRateEffect.interpretation,
          dataQuality: qualityEffect.interpretation,
        },
      },
    };
  }

  // Helper methods
  static shuffleArray(array) {
    const shuffled = [...array];
    for (let i = shuffled.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    return shuffled;
  }

  static calculateMean(values) {
    return values.reduce((sum, val) => sum + val, 0) / values.length;
  }

  static calculateStandardDeviation(values) {
    const mean = this.calculateMean(values);
    const squaredDiffs = values.map(val => Math.pow(val - mean, 2));
    const variance = squaredDiffs.reduce((sum, diff) => sum + diff, 0) / (values.length - 1);
    return Math.sqrt(variance);
  }

  static bootstrapSample(data) {
    const sample = [];
    for (let i = 0; i < data.length; i++) {
      const randomIndex = Math.floor(Math.random() * data.length);
      sample.push(data[randomIndex]);
    }
    return sample;
  }

  // Simplified t-distribution critical values (approximation)
  static getTValue(df, alpha) {
    // Simplified approximation for common cases
    if (df >= 30) return 1.96; // Normal approximation

    const tTable = {
      1: 12.706,
      2: 4.303,
      3: 3.182,
      4: 2.776,
      5: 2.571,
      6: 2.447,
      7: 2.365,
      8: 2.306,
      9: 2.262,
      10: 2.228,
      15: 2.131,
      20: 2.086,
      25: 2.06,
      30: 2.042,
    };

    return tTable[df] || tTable[30] || 2.0;
  }

  static getTwoTailedP(tStat, df) {
    // Simplified p-value calculation (approximation)
    if (df >= 30) {
      // Normal approximation
      const z = tStat;
      return 2 * (1 - this.normalCDF(Math.abs(z)));
    }

    // Very rough approximation for small samples
    if (tStat > 3) return 0.01;
    if (tStat > 2) return 0.05;
    if (tStat > 1.5) return 0.15;
    return 0.25;
  }

  static normalCDF(x) {
    // Approximation of normal CDF
    return 0.5 * (1 + this.erf(x / Math.sqrt(2)));
  }

  static erf(x) {
    // Approximation of error function
    const a1 = 0.254829592;
    const a2 = -0.284496736;
    const a3 = 1.421413741;
    const a4 = -1.453152027;
    const a5 = 1.061405429;
    const p = 0.3275911;

    const sign = x >= 0 ? 1 : -1;
    x = Math.abs(x);

    const t = 1.0 / (1.0 + p * x);
    const y = 1.0 - ((((a5 * t + a4) * t + a3) * t + a2) * t + a1) * t * Math.exp(-x * x);

    return sign * y;
  }
}

module.exports = { StatisticalValidator };
