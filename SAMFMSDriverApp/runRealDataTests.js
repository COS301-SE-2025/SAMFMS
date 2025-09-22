/**
 * Standalone Algorithm Testing Suite with Real Data
 * Runs comprehensive validation using actual CSV datasets
 */

const fs = require('fs');
const path = require('path');
const { RealDatasetLoader } = require('./realDatasetLoader');
const { SimpleAlgorithmTester } = require('./simpleAlgorithmTester');

console.log('🚗 Driver Behavior Algorithm Testing Suite (Real Data)');
console.log('====================================================\n');

/**
 * Test configuration sets
 */
const testConfigurations = [
  {
    name: 'Default Settings',
    config: {
      accelerationThreshold: 6.5,
      brakingThreshold: -6.5,
      qualityThreshold: 0.6,
      calibrationPeriod: 15000,
      alertCooldown: 2000,
      enableFiltering: true,
    },
  },
  {
    name: 'Sensitive Detection',
    config: {
      accelerationThreshold: 5.0,
      brakingThreshold: -5.0,
      qualityThreshold: 0.5,
      calibrationPeriod: 10000,
      alertCooldown: 1500,
      enableFiltering: true,
    },
  },
  {
    name: 'Conservative Detection',
    config: {
      accelerationThreshold: 8.0,
      brakingThreshold: -8.0,
      qualityThreshold: 0.8,
      calibrationPeriod: 20000,
      alertCooldown: 3000,
      enableFiltering: true,
    },
  },
  {
    name: 'No Filtering (Baseline)',
    config: {
      accelerationThreshold: 6.5,
      brakingThreshold: -6.5,
      qualityThreshold: 0.6,
      calibrationPeriod: 15000,
      alertCooldown: 2000,
      enableFiltering: false,
    },
  },
];

/**
 * Load all available datasets
 */
async function loadDatasets() {
  console.log('📂 Loading real datasets...');

  const datasetsPath = path.join(__dirname, 'datasets');
  if (!fs.existsSync(datasetsPath)) {
    throw new Error(`Datasets folder not found at: ${datasetsPath}`);
  }
  const loader = new RealDatasetLoader();
  const datasets = await loader.loadAllDatasets(datasetsPath);

  console.log(`✓ Loaded ${datasets.length} datasets:`);
  datasets.forEach(dataset => {
    const duration = (dataset.duration / 60000).toFixed(1);
    console.log(
      `  • ${dataset.name} (${dataset.type}) - ${duration} min, ${dataset.data.length} samples`
    );
  });

  return datasets;
}

/**
 * Run comprehensive algorithm tests with real data
 */
async function runComprehensiveTests() {
  console.log('\n📊 Running comprehensive algorithm validation...\n');

  // Load real datasets
  const datasets = await loadDatasets();
  if (datasets.length === 0) {
    throw new Error('No datasets found to test with');
  }

  const allResults = [];

  for (const testConfig of testConfigurations) {
    console.log(`\n🔧 Testing Configuration: ${testConfig.name}`);
    console.log('─'.repeat(60));

    const tester = new SimpleAlgorithmTester(testConfig.config);
    const configResults = [];

    for (const dataset of datasets) {
      const result = await tester.testDataset(dataset);
      configResults.push(result);
      allResults.push({
        ...result,
        configName: testConfig.name,
        config: testConfig.config,
      });

      console.log(
        `  ✓ ${result.sessionName}: ${
          result.totalViolations
        } violations (${result.violationRate.toFixed(2)}/min), Quality: ${(
          result.averageQuality * 100
        ).toFixed(1)}%`
      );
    }

    // Configuration summary
    const metrics = SimpleAlgorithmTester.calculateValidationMetrics(configResults);
    console.log(`\n  📋 Configuration Summary:`);
    console.log(`    Accuracy: ${(metrics.accuracy * 100).toFixed(1)}%`);
    console.log(`    Precision: ${(metrics.precision * 100).toFixed(1)}%`);
    console.log(`    Recall: ${(metrics.recall * 100).toFixed(1)}%`);
    console.log(`    Avg Quality: ${(metrics.avgDataQuality * 100).toFixed(1)}%`);
    console.log(`    Calibration Success: ${(metrics.calibrationSuccessRate * 100).toFixed(1)}%`);
  }

  return allResults;
}

/**
 * Calculate detailed performance analysis
 */
function calculateDetailedMetrics(results) {
  console.log('\n📈 Detailed Performance Analysis');
  console.log('═'.repeat(60));

  // Group by configuration
  const byConfig = {};
  results.forEach(result => {
    if (!byConfig[result.configName]) {
      byConfig[result.configName] = [];
    }
    byConfig[result.configName].push(result);
  });

  const configPerformance = [];

  // Analyze each configuration
  Object.entries(byConfig).forEach(([configName, configResults]) => {
    console.log(`\n🔧 ${configName}:`);

    const metrics = SimpleAlgorithmTester.calculateValidationMetrics(configResults);
    configPerformance.push({
      name: configName,
      ...metrics,
    });

    console.log(`  Classification Metrics:`);
    console.log(`    Accuracy: ${(metrics.accuracy * 100).toFixed(1)}%`);
    console.log(`    Precision: ${(metrics.precision * 100).toFixed(1)}%`);
    console.log(`    Recall: ${(metrics.recall * 100).toFixed(1)}%`);
    console.log(`    False Positive Rate: ${(metrics.falsePositiveRate * 100).toFixed(1)}%`);

    console.log(`  Data Quality:`);
    console.log(`    Average Quality: ${(metrics.avgDataQuality * 100).toFixed(1)}%`);
    console.log(`    Calibration Success: ${(metrics.calibrationSuccessRate * 100).toFixed(1)}%`);

    console.log(`  Violation Analysis:`);
    console.log(`    Safe Driving: ${metrics.avgViolationRateSafe.toFixed(2)}/min`);
    console.log(`    Risky Driving: ${metrics.avgViolationRateRisky.toFixed(2)}/min`);
    console.log(`    Separation: ${metrics.violationRateDifference.toFixed(2)}/min`);

    console.log(`  Confusion Matrix:`);
    console.log(`    True Positives: ${metrics.truePositives}`);
    console.log(`    False Positives: ${metrics.falsePositives}`);
    console.log(`    True Negatives: ${metrics.trueNegatives}`);
    console.log(`    False Negatives: ${metrics.falseNegatives}`);
  });

  // Find best configuration
  const bestConfig = configPerformance.reduce((best, current) =>
    current.accuracy > best.accuracy ? current : best
  );

  console.log('\n🏆 Best Configuration:');
  console.log(`  ${bestConfig.name} - ${(bestConfig.accuracy * 100).toFixed(1)}% accuracy`);

  return configPerformance;
}

/**
 * Export results to JSON
 */
function exportResults(results, configPerformance) {
  const exportData = {
    timestamp: new Date().toISOString(),
    totalDatasets: new Set(results.map(r => r.sessionName)).size,
    totalConfigurations: testConfigurations.length,
    detailedResults: results,
    configurationSummary: configPerformance,
    testSettings: testConfigurations,
  };

  const outputPath = path.join(__dirname, 'test-results', 'algorithm-validation-results.json');

  // Create results directory if it doesn't exist
  const resultsDir = path.dirname(outputPath);
  if (!fs.existsSync(resultsDir)) {
    fs.mkdirSync(resultsDir, { recursive: true });
  }

  fs.writeFileSync(outputPath, JSON.stringify(exportData, null, 2));
  console.log(`\n💾 Results exported to: ${outputPath}`);
}

/**
 * Main execution
 */
async function main() {
  try {
    const startTime = Date.now();

    console.log('🔍 Starting real data validation...');

    const results = await runComprehensiveTests();
    const configPerformance = calculateDetailedMetrics(results);

    // Export results
    exportResults(results, configPerformance);

    const duration = Date.now() - startTime;
    const bestAccuracy = Math.max(...configPerformance.map(c => c.accuracy));

    console.log(`\n⏱️  Test completed in ${(duration / 1000).toFixed(2)} seconds`);
    console.log(`🎯 Best overall accuracy: ${(bestAccuracy * 100).toFixed(1)}%`);
    console.log(`📊 Tested ${results.length} dataset-configuration combinations`);
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    console.error(error.stack);
    process.exit(1);
  }
}

// Run the tests if this file is executed directly
if (require.main === module) {
  main();
}

module.exports = { main, loadDatasets, runComprehensiveTests };
