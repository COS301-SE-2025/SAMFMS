const fs = require('fs');
const path = require('path');

/**
 * Real Dataset CSV Loader for Node.js
 * Loads actual accelerometer and gyroscope data from CSV files
 */
class RealDatasetLoader {
  constructor() {
    this.datasetsPath = path.join(process.cwd(), 'datasets');
  }

  /**
   * Load all available datasets from the datasets folder
   */
  async loadAllDatasets() {
    console.log('📂 Loading real datasets from CSV files...');
    const datasets = [];

    try {
      const entries = fs.readdirSync(this.datasetsPath);

      for (const entry of entries) {
        if (entry.startsWith('Day-') && (entry.endsWith('S') || entry.endsWith('R'))) {
          const dataset = await this.loadDataset(entry);
          if (dataset) {
            datasets.push(dataset);
          }
        }
      }

      console.log(`✅ Loaded ${datasets.length} real datasets successfully`);
      return datasets;
    } catch (error) {
      console.error('❌ Error loading datasets:', error.message);
      throw error;
    }
  }

  /**
   * Load a single dataset from CSV files
   */
  async loadDataset(folderName) {
    try {
      const datasetPath = path.join(this.datasetsPath, folderName, folderName);

      if (!fs.existsSync(datasetPath)) {
        console.warn(`⚠️  Dataset path not found: ${datasetPath}`);
        return null;
      }

      const accelerometerPath = path.join(datasetPath, 'Accelerometer.csv');
      const gyroscopePath = path.join(datasetPath, 'Gyroscope.csv');

      if (!fs.existsSync(accelerometerPath) || !fs.existsSync(gyroscopePath)) {
        console.warn(`⚠️  Missing CSV files for dataset: ${folderName}`);
        return null;
      }

      const accelerometerData = this.parseCSV(accelerometerPath);
      const gyroscopeData = this.parseCSV(gyroscopePath);

      // Determine behavior type from folder name
      const behaviorType = folderName.endsWith('S') ? 'safe' : 'risky';

      const dataset = {
        name: folderName,
        type: behaviorType,
        accelerometer: accelerometerData,
        gyroscope: gyroscopeData,
        totalSamples: accelerometerData.length,
        duration: this.calculateDuration(accelerometerData),
        data: this.synchronizeData(accelerometerData, gyroscopeData),
      };

      console.log(
        `📊 Loaded ${folderName}: ${dataset.totalSamples} samples, ${(
          dataset.duration / 60000
        ).toFixed(1)} minutes, ${behaviorType} driving`
      );

      return dataset;
    } catch (error) {
      console.error(`❌ Error loading dataset ${folderName}:`, error.message);
      return null;
    }
  }

  /**
   * Parse CSV file into structured data
   */
  parseCSV(filePath) {
    const content = fs.readFileSync(filePath, 'utf-8');
    const lines = content.split('\n');
    const data = [];

    // Skip header row
    for (let i = 1; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line) continue;

      const parts = line.split(',');
      if (parts.length >= 5) {
        try {
          const timestamp = this.parseTimestamp(parts[0], parts[1]);
          const x = parseFloat(parts[2]);
          const y = parseFloat(parts[3]);
          const z = parseFloat(parts[4]);

          if (!isNaN(timestamp) && !isNaN(x) && !isNaN(y) && !isNaN(z)) {
            data.push({
              timestamp,
              x,
              y,
              z,
            });
          }
        } catch (e) {
          // Skip malformed lines
          continue;
        }
      }
    }

    return data;
  }

  /**
   * Parse timestamp from date and milliseconds
   */
  parseTimestamp(dateStr, millisecondsStr) {
    try {
      // Parse date like "23-05-2020 07:46"
      const [datePart, timePart] = dateStr.split(' ');
      const [day, month, year] = datePart.split('-');
      const [hour, minute] = timePart.split(':');

      const date = new Date(
        parseInt(year),
        parseInt(month) - 1,
        parseInt(day),
        parseInt(hour),
        parseInt(minute)
      );
      const milliseconds = parseInt(millisecondsStr) || 0;

      return date.getTime() + milliseconds;
    } catch (e) {
      return Date.now(); // Fallback
    }
  }

  /**
   * Calculate duration of dataset in milliseconds
   */
  calculateDuration(data) {
    if (data.length < 2) return 0;
    return data[data.length - 1].timestamp - data[0].timestamp;
  }

  /**
   * Synchronize accelerometer and gyroscope data by timestamp
   */
  synchronizeData(accelData, gyroData) {
    const synchronized = [];
    let gyroIndex = 0;

    for (const accelSample of accelData) {
      // Find closest gyroscope sample
      while (
        gyroIndex < gyroData.length - 1 &&
        Math.abs(gyroData[gyroIndex + 1].timestamp - accelSample.timestamp) <
          Math.abs(gyroData[gyroIndex].timestamp - accelSample.timestamp)
      ) {
        gyroIndex++;
      }

      const gyroSample = gyroData[gyroIndex] || { x: 0, y: 0, z: 0 };

      synchronized.push({
        timestamp: accelSample.timestamp,
        accelerometer: {
          x: accelSample.x,
          y: accelSample.y,
          z: accelSample.z,
        },
        gyroscope: {
          x: gyroSample.x,
          y: gyroSample.y,
          z: gyroSample.z,
        },
      });
    }

    return synchronized;
  }
}

module.exports = { RealDatasetLoader };
