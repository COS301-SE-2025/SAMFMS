import { Vector3D } from './sensorFusion';

export interface DatasetSensorData {
  timestamp: string;
  milliseconds: number;
  x: number;
  y: number;
  z: number;
  unixTimestamp?: number;
}

export interface ProcessedDatasetEntry {
  timestamp: number; // Unix timestamp in milliseconds
  accelerometer: Vector3D;
  gyroscope?: Vector3D;
}

export interface DatasetSession {
  name: string;
  type: 'safe' | 'risky';
  data: ProcessedDatasetEntry[];
  duration: number; // in milliseconds
  totalSamples: number;
  averageSamplingRate: number; // Hz
}

export interface DatasetMetadata {
  sessionName: string;
  behaviorType: 'safe' | 'risky';
  vehicle?: string;
  driver?: string;
  device?: string;
  tripDistance?: string;
}

export class DatasetLoader {
  /**
   * Parse CSV data from string content
   */
  private parseCSV(csvContent: string): DatasetSensorData[] {
    const lines = csvContent.trim().split('\n');
    const headers = lines[0].split(',');

    // Validate headers
    const hasUnixTimestamp = headers.includes('Unix Timestamp');

    const data: DatasetSensorData[] = [];

    for (let i = 1; i < lines.length; i++) {
      const values = lines[i].split(',');
      if (values.length >= 5) {
        const entry: DatasetSensorData = {
          timestamp: values[0],
          milliseconds: parseInt(values[hasUnixTimestamp ? 2 : 1], 10),
          x: parseFloat(values[hasUnixTimestamp ? 3 : 2]),
          y: parseFloat(values[hasUnixTimestamp ? 4 : 3]),
          z: parseFloat(values[hasUnixTimestamp ? 5 : 4]),
        };

        if (hasUnixTimestamp) {
          entry.unixTimestamp = parseInt(values[1], 10);
        }

        data.push(entry);
      }
    }

    return data;
  }

  /**
   * Convert parsed CSV data to our internal format
   */
  private processDatasetEntry(
    accelerometerData: DatasetSensorData[],
    gyroscopeData?: DatasetSensorData[]
  ): ProcessedDatasetEntry[] {
    const processed: ProcessedDatasetEntry[] = [];

    // Create a map of gyroscope data for quick lookup
    const gyroMap = new Map<number, Vector3D>();
    if (gyroscopeData) {
      gyroscopeData.forEach(entry => {
        const timestamp = this.parseTimestamp(entry.timestamp, entry.milliseconds);
        gyroMap.set(timestamp, { x: entry.x, y: entry.y, z: entry.z });
      });
    }

    accelerometerData.forEach(entry => {
      const timestamp = this.parseTimestamp(entry.timestamp, entry.milliseconds);
      const accelerometer: Vector3D = { x: entry.x, y: entry.y, z: entry.z };

      // Find closest gyroscope reading (within 50ms)
      let gyroscope: Vector3D | undefined;
      if (gyroMap.size > 0) {
        // Look for exact match first
        gyroscope = gyroMap.get(timestamp);

        // If no exact match, find closest within 50ms
        if (!gyroscope) {
          for (const [gyroTimestamp, gyroData] of gyroMap.entries()) {
            if (Math.abs(gyroTimestamp - timestamp) <= 50) {
              gyroscope = gyroData;
              break;
            }
          }
        }
      }

      processed.push({
        timestamp,
        accelerometer,
        gyroscope,
      });
    });

    return processed.sort((a, b) => a.timestamp - b.timestamp);
  }

  /**
   * Parse timestamp string to Unix timestamp in milliseconds
   */
  private parseTimestamp(dateStr: string, milliseconds: number): number {
    // Handle different date formats
    let parsedDate: Date;

    if (dateStr.includes('-')) {
      // Format: "23-05-2020 13:17" or "02-02-21 10:28"
      const parts = dateStr.split(' ');
      const datePart = parts[0];
      const timePart = parts[1] || '00:00';

      const [day, month, year] = datePart.split('-');
      const [hour, minute] = timePart.split(':');

      // Handle 2-digit vs 4-digit year
      const fullYear = year.length === 2 ? 2000 + parseInt(year, 10) : parseInt(year, 10);

      parsedDate = new Date(
        fullYear,
        parseInt(month, 10) - 1,
        parseInt(day, 10),
        parseInt(hour, 10),
        parseInt(minute, 10)
      );
    } else {
      parsedDate = new Date(dateStr);
    }

    return parsedDate.getTime() + milliseconds;
  }

  /**
   * Extract metadata from session name
   */
  private extractMetadata(sessionName: string): DatasetMetadata {
    const metadata: DatasetMetadata = {
      sessionName,
      behaviorType: 'safe', // default
    };

    // Determine behavior type from session name
    if (sessionName.includes('-R') || sessionName.toLowerCase().includes('risky')) {
      metadata.behaviorType = 'risky';
    } else if (sessionName.includes('-S') || sessionName.toLowerCase().includes('safe')) {
      metadata.behaviorType = 'safe';
    }

    // Extract driver information
    if (sessionName.includes('Driver-')) {
      const driverMatch = sessionName.match(/Driver-(\d+)/);
      if (driverMatch) {
        metadata.driver = `Driver ${driverMatch[1]}`;
      }
    }

    // Add additional metadata based on research context
    metadata.vehicle = 'Ford Figo 1.2 / Maruti Swift VXI / Tata Nexon XMS';
    metadata.device = 'Redmi 4 / MI A3';
    metadata.tripDistance = '10-25 km round trip';

    return metadata;
  }

  /**
   * Load a dataset session from CSV content
   */
  public async loadSession(
    sessionName: string,
    accelerometerCSV: string,
    gyroscopeCSV?: string
  ): Promise<DatasetSession> {
    const accelerometerData = this.parseCSV(accelerometerCSV);
    const gyroscopeData = gyroscopeCSV ? this.parseCSV(gyroscopeCSV) : undefined;

    const processedData = this.processDatasetEntry(accelerometerData, gyroscopeData);
    const metadata = this.extractMetadata(sessionName);

    // Calculate session statistics
    const timestamps = processedData.map(entry => entry.timestamp);
    const duration = Math.max(...timestamps) - Math.min(...timestamps);
    const averageSamplingRate = (processedData.length / duration) * 1000; // Convert to Hz

    return {
      name: sessionName,
      type: metadata.behaviorType,
      data: processedData,
      duration,
      totalSamples: processedData.length,
      averageSamplingRate,
    };
  }

  /**
   * Resample data to a target frequency (for consistent testing)
   */
  public resampleSession(session: DatasetSession, targetHz: number = 10): DatasetSession {
    const targetIntervalMs = 1000 / targetHz;
    const resampledData: ProcessedDatasetEntry[] = [];

    const startTime = session.data[0].timestamp;
    const endTime = session.data[session.data.length - 1].timestamp;

    for (let time = startTime; time <= endTime; time += targetIntervalMs) {
      // Find closest data point
      let closestEntry = session.data[0];
      let minDiff = Math.abs(session.data[0].timestamp - time);

      for (const entry of session.data) {
        const diff = Math.abs(entry.timestamp - time);
        if (diff < minDiff) {
          minDiff = diff;
          closestEntry = entry;
        }

        // Stop searching if we've passed the target time
        if (entry.timestamp > time) break;
      }

      // Only include if within reasonable tolerance (50ms)
      if (minDiff <= 50) {
        resampledData.push({
          timestamp: time,
          accelerometer: closestEntry.accelerometer,
          gyroscope: closestEntry.gyroscope,
        });
      }
    }

    return {
      ...session,
      data: resampledData,
      totalSamples: resampledData.length,
      averageSamplingRate: targetHz,
    };
  }

  /**
   * Get available dataset files from the datasets directory
   */
  public getAvailableDatasets(): string[] {
    // Return list of known dataset sessions
    return [
      'Day-1R',
      'Day-1S',
      'Day-2R',
      'Day-2S',
      'Day-3R',
      'Day-3S',
      'Day-4R',
      'Day-4S',
      'Day-5S',
      'Day-6R',
      'Day-6S',
      'Day-7S',
      'Driver-1',
      'Driver-2',
      'Driver-3',
      'Driver-4',
      'Driver-5',
      'Driver-6',
      'Driver-7',
    ];
  }
}
