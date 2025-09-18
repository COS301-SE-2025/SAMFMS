/**
 * Enhanced Algorithm Comparison Test Runner
 * Compares original algorithm vs enhanced algorithm with detailed metrics
 */

const fs = require('fs');
const path = require('path');
const { RealDatasetLoader } = require('./realDatasetLoader');
const { SimpleAlgorithmTester } = require('./simpleAlgorithmTester');
const { EnhancedAlgorithmTester } = require('./enhancedAlgorithmTester');

console.log('🚗 Enhanced Driver Behavior Algorithm Testing Suite');
console.log('================================================\n');

/**
 * Configuration sets for testing both algorithms
 */
const enhancedConfigurations = [
  {
    name: 'Enhanced - Adaptive Balanced',
    config: {
      useAdaptiveThresholds: true,
      baseAccelerationThreshold: 2.0,
      baseBrakingThreshold: -2.0,
      thresholdMultiplier: 2.5,
      enableJerkDetection: true,
      enableSmoothing: true,
      enableEventScoring: true,
    },
  },
  {
    name: 'Enhanced - Adaptive Sensitive',
    config: {
      useAdaptiveThresholds: true,
      baseAccelerationThreshold: 1.5,
      baseBrakingThreshold: -1.5,
      thresholdMultiplier: 2.0,
      enableJerkDetection: true,
      enableSmoothing: true,
      enableEventScoring: true,
      violationScoreThreshold: 0.8,
    },
  },
  {
    name: 'Enhanced - Fixed Improved',
    config: {
      useAdaptiveThresholds: false,
      baseAccelerationThreshold: 2.0,
      baseBrakingThreshold: -2.0,
      enableJerkDetection: true,
      enableSmoothing: true,
      enableEventScoring: false,
    },
  },
];

const originalConfigurations = [
  {
    name: 'Original - Default',
    config: {
      accelerationThreshold: 6.5,
      brakingThreshold: -6.5,
      qualityThreshold: 0.6,
      enableFiltering: true,
    },
  },
  {
    name: 'Original - Lowered Thresholds',
    config: {
      accelerationThreshold: 2.5,
      brakingThreshold: -2.5,
      qualityThreshold: 0.6,
      enableFiltering: true,
    },
  },
];

/**
 * Load datasets
 */
async function loadDatasets() {
  console.log('📂 Loading real datasets...');

  const datasetsPath = path.join(__dirname, 'datasets');
  if (!fs.existsSync(datasetsPath)) {
    throw new Error(`Datasets folder not found at: ${datasetsPath}`);
  }

  const loader = new RealDatasetLoader();
  const datasets = await loader.loadAllDatasets(datasetsPath);

  console.log(`✓ Loaded ${datasets.length} datasets for comparison\n`);

  return datasets;
}

/**
 * Test enhanced algorithm configurations
 */
async function testEnhancedAlgorithm(datasets) {
  console.log('🔧 Testing Enhanced Algorithm Configurations');
  console.log('═'.repeat(50));

  const allResults = [];

  for (const testConfig of enhancedConfigurations) {
    console.log(`\n🎯 Configuration: ${testConfig.name}`);
    console.log('─'.repeat(40));

    const tester = new EnhancedAlgorithmTester(testConfig.config);
    const configResults = [];

    for (const dataset of datasets) {
      const result = await tester.testDataset(dataset);
      configResults.push(result);
      allResults.push({
        ...result,
        configName: testConfig.name,
        algorithmType: 'enhanced',
        config: testConfig.config,
      });

      const thresholds = result.adaptiveThresholds
        ? `±${result.adaptiveThresholds.acceleration.toFixed(2)}`
        : `±${testConfig.config.baseAccelerationThreshold}`;

      console.log(
        `  ✓ ${result.sessionName}: ${
          result.totalViolations
        } violations (${result.violationRate.toFixed(2)}/min), Thresholds: ${thresholds}`
      );
    }

    // Configuration summary
    const metrics = EnhancedAlgorithmTester.calculateValidationMetrics(configResults);
    console.log(`\n  📊 Enhanced Algorithm Summary:`);
    console.log(`    Accuracy: ${(metrics.accuracy * 100).toFixed(1)}%`);
    console.log(`    Precision: ${(metrics.precision * 100).toFixed(1)}%`);
    console.log(`    Recall: ${(metrics.recall * 100).toFixed(1)}%`);
    console.log(
      `    F1-Score: ${(
        ((2 * metrics.precision * metrics.recall) / (metrics.precision + metrics.recall)) *
        100
      ).toFixed(1)}%`
    );
    console.log(`    Dynamic Threshold: ${metrics.dynamicThreshold.toFixed(1)} violations/min`);
  }

  return allResults;
}

/**
 * Test original algorithm for comparison
 */
async function testOriginalAlgorithm(datasets) {
  console.log('\n🔧 Testing Original Algorithm Configurations');
  console.log('═'.repeat(50));

  const allResults = [];

  for (const testConfig of originalConfigurations) {
    console.log(`\n📊 Configuration: ${testConfig.name}`);
    console.log('─'.repeat(40));

    const tester = new SimpleAlgorithmTester(testConfig.config);
    const configResults = [];

    for (const dataset of datasets) {
      const result = await tester.testDataset(dataset);
      configResults.push(result);
      allResults.push({
        ...result,
        configName: testConfig.name,
        algorithmType: 'original',
        config: testConfig.config,
      });

      console.log(
        `  ✓ ${result.sessionName}: ${
          result.totalViolations
        } violations (${result.violationRate.toFixed(2)}/min)`
      );
    }

    // Configuration summary
    const metrics = SimpleAlgorithmTester.calculateValidationMetrics(configResults);
    console.log(`\n  📊 Original Algorithm Summary:`);
    console.log(`    Accuracy: ${(metrics.accuracy * 100).toFixed(1)}%`);
    console.log(`    Precision: ${(metrics.precision * 100).toFixed(1)}%`);
    console.log(`    Recall: ${(metrics.recall * 100).toFixed(1)}%`);
  }

  return allResults;
}

/**
 * Compare algorithm performance
 */
function compareAlgorithms(enhancedResults, originalResults) {
  console.log('\n📈 Algorithm Performance Comparison');
  console.log('═'.repeat(60));

  // Group results by algorithm type
  const enhancedByConfig = {};
  const originalByConfig = {};

  enhancedResults.forEach(result => {
    if (!enhancedByConfig[result.configName]) {
      enhancedByConfig[result.configName] = [];
    }
    enhancedByConfig[result.configName].push(result);
  });

  originalResults.forEach(result => {
    if (!originalByConfig[result.configName]) {
      originalByConfig[result.configName] = [];
    }
    originalByConfig[result.configName].push(result);
  });

  // Calculate metrics for each configuration
  const comparisonResults = [];

  console.log('\n🏆 Enhanced Algorithm Performance:');
  Object.entries(enhancedByConfig).forEach(([configName, results]) => {
    const metrics = EnhancedAlgorithmTester.calculateValidationMetrics(results);
    const f1Score =
      metrics.precision + metrics.recall > 0
        ? (2 * metrics.precision * metrics.recall) / (metrics.precision + metrics.recall)
        : 0;

    console.log(`  ${configName}:`);
    console.log(`    Accuracy: ${(metrics.accuracy * 100).toFixed(1)}%`);
    console.log(`    Precision: ${(metrics.precision * 100).toFixed(1)}%`);
    console.log(`    Recall: ${(metrics.recall * 100).toFixed(1)}%`);
    console.log(`    F1-Score: ${(f1Score * 100).toFixed(1)}%`);
    console.log(`    Violation Rate Separation: ${metrics.violationRateDifference.toFixed(2)}/min`);

    comparisonResults.push({
      algorithm: 'Enhanced',
      configuration: configName,
      metrics: { ...metrics, f1Score },
    });
  });

  console.log('\n📊 Original Algorithm Performance:');
  Object.entries(originalByConfig).forEach(([configName, results]) => {
    const metrics = SimpleAlgorithmTester.calculateValidationMetrics(results);
    const f1Score =
      metrics.precision + metrics.recall > 0
        ? (2 * metrics.precision * metrics.recall) / (metrics.precision + metrics.recall)
        : 0;

    console.log(`  ${configName}:`);
    console.log(`    Accuracy: ${(metrics.accuracy * 100).toFixed(1)}%`);
    console.log(`    Precision: ${(metrics.precision * 100).toFixed(1)}%`);
    console.log(`    Recall: ${(metrics.recall * 100).toFixed(1)}%`);
    console.log(`    F1-Score: ${(f1Score * 100).toFixed(1)}%`);
    console.log(`    Violation Rate Separation: ${metrics.violationRateDifference.toFixed(2)}/min`);

    comparisonResults.push({
      algorithm: 'Original',
      configuration: configName,
      metrics: { ...metrics, f1Score },
    });
  });

  // Find best performers
  const bestEnhanced = comparisonResults
    .filter(r => r.algorithm === 'Enhanced')
    .reduce((best, current) => (current.metrics.f1Score > best.metrics.f1Score ? current : best));

  const bestOriginal = comparisonResults
    .filter(r => r.algorithm === 'Original')
    .reduce((best, current) => (current.metrics.f1Score > best.metrics.f1Score ? current : best));

  console.log('\n🥇 Best Performers:');
  console.log(
    `  Enhanced: ${bestEnhanced.configuration} (F1: ${(bestEnhanced.metrics.f1Score * 100).toFixed(
      1
    )}%)`
  );
  console.log(
    `  Original: ${bestOriginal.configuration} (F1: ${(bestOriginal.metrics.f1Score * 100).toFixed(
      1
    )}%)`
  );

  // Improvement calculation
  const improvement =
    ((bestEnhanced.metrics.f1Score - bestOriginal.metrics.f1Score) / bestOriginal.metrics.f1Score) *
    100;
  console.log(`\n📈 Overall Improvement: ${improvement.toFixed(1)}% better F1-Score`);

  return { comparisonResults, bestEnhanced, bestOriginal, improvement };
}

/**
 * Export detailed results
 */
function exportResults(enhancedResults, originalResults, comparison) {
  const exportData = {
    timestamp: new Date().toISOString(),
    testType: 'Enhanced Algorithm Comparison',
    summary: {
      totalDatasets: new Set([...enhancedResults, ...originalResults].map(r => r.sessionName)).size,
      enhancedConfigurations: enhancedConfigurations.length,
      originalConfigurations: originalConfigurations.length,
      bestPerformer: comparison.bestEnhanced,
      improvement: comparison.improvement,
    },
    enhancedResults,
    originalResults,
    comparison: comparison.comparisonResults,
  };

  const outputPath = path.join(__dirname, 'test-results', 'enhanced-algorithm-comparison.json');
  const resultsDir = path.dirname(outputPath);
  if (!fs.existsSync(resultsDir)) {
    fs.mkdirSync(resultsDir, { recursive: true });
  }

  fs.writeFileSync(outputPath, JSON.stringify(exportData, null, 2));
  console.log(`\n💾 Comparison results exported to: ${outputPath}`);
}

/**
 * Main execution
 */
async function main() {
  try {
    const startTime = Date.now();

    console.log('🔍 Starting enhanced algorithm comparison...');

    // Load datasets
    const datasets = await loadDatasets();

    // Test both algorithms
    const enhancedResults = await testEnhancedAlgorithm(datasets);
    const originalResults = await testOriginalAlgorithm(datasets);

    // Compare performance
    const comparison = compareAlgorithms(enhancedResults, originalResults);

    // Export results
    exportResults(enhancedResults, originalResults, comparison);

    const duration = Date.now() - startTime;
    console.log(`\n⏱️  Comparison completed in ${(duration / 1000).toFixed(2)} seconds`);
    console.log(`🎯 Best enhanced algorithm: ${comparison.bestEnhanced.configuration}`);
    console.log(`📊 Performance improvement: ${comparison.improvement.toFixed(1)}%`);
  } catch (error) {
    console.error('❌ Comparison failed:', error.message);
    console.error(error.stack);
    process.exit(1);
  }
}

// Run the comparison if this file is executed directly
if (require.main === module) {
  main();
}

module.exports = { main, testEnhancedAlgorithm, testOriginalAlgorithm };
