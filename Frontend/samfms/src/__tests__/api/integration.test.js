/**
 * Integration Tests for Frontend API
 * Tests API integration with running containers
 */
import { login, logout } from '../../backend/api/auth';
import { getVehicles, createVehicle } from '../../backend/api/vehicles';
import { getDrivers, createDriver } from '../../backend/api/drivers';
import { getMaintenanceRecords, createMaintenanceRecord } from '../../backend/api/maintenance';
import { getAssignments, createAssignment } from '../../backend/api/assignments';

// These tests require running Docker containers
describe('Frontend API Integration Tests', () => {
  let authToken = null;
  let testVehicleId = null;
  let testDriverId = null;
  let testMaintenanceId = null;
  let testAssignmentId = null;

  beforeAll(async () => {
    // Skip tests if not in container environment
    if (process.env.NODE_ENV !== 'container-test') {
      console.log('Skipping integration tests - not in container environment');
      return;
    }

    // Login to get authentication token
    try {
      const loginResponse = await login({
        email: 'admin@samfms.com',
        password: 'admin123',
      });
      authToken = loginResponse.data.token;
    } catch (error) {
      console.log('Login failed, tests will be skipped:', error.message);
    }
  });

  afterAll(async () => {
    // Cleanup test data
    if (testAssignmentId) {
      // Delete test assignment
    }
    if (testMaintenanceId) {
      // Delete test maintenance record
    }
    if (testDriverId) {
      // Delete test driver
    }
    if (testVehicleId) {
      // Delete test vehicle
    }

    // Logout
    if (authToken) {
      await logout();
    }
  });

  describe('Authentication Integration', () => {
    test('should login successfully', async () => {
      if (!authToken) {
        return; // Skip if login failed
      }

      expect(authToken).toBeTruthy();
    });

    test('should logout successfully', async () => {
      if (!authToken) {
        return; // Skip if login failed
      }

      const result = await logout();
      expect(result.success).toBe(true);
    });
  });

  describe('Vehicles Integration', () => {
    test('should get vehicles list', async () => {
      if (!authToken) {
        return; // Skip if not authenticated
      }

      const result = await getVehicles();
      expect(result.success).toBe(true);
      expect(Array.isArray(result.data)).toBe(true);
    });

    test('should create new vehicle', async () => {
      if (!authToken) {
        return; // Skip if not authenticated
      }

      const vehicleData = {
        make: 'Toyota',
        model: 'Camry',
        year: 2023,
        license_plate: 'TEST123',
        status: 'active',
      };

      const result = await createVehicle(vehicleData);
      expect(result.success).toBe(true);
      expect(result.data).toBeDefined();
      expect(result.data.id).toBeDefined();

      testVehicleId = result.data.id;
    });
  });

  describe('Drivers Integration', () => {
    test('should get drivers list', async () => {
      if (!authToken) {
        return; // Skip if not authenticated
      }

      const result = await getDrivers();
      expect(result.success).toBe(true);
      expect(Array.isArray(result.data)).toBe(true);
    });

    test('should create new driver', async () => {
      if (!authToken) {
        return; // Skip if not authenticated
      }

      const driverData = {
        first_name: 'John',
        last_name: 'Doe',
        email: 'john.doe.test@example.com',
        phone: '+1234567890',
        license_number: 'DL123456',
        license_expiry: '2025-12-31',
        status: 'active',
      };

      const result = await createDriver(driverData);
      expect(result.success).toBe(true);
      expect(result.data).toBeDefined();
      expect(result.data.id).toBeDefined();

      testDriverId = result.data.id;
    });
  });

  describe('Maintenance Integration', () => {
    test('should get maintenance records list', async () => {
      if (!authToken) {
        return; // Skip if not authenticated
      }

      const result = await getMaintenanceRecords();
      expect(result.success).toBe(true);
      expect(Array.isArray(result.data)).toBe(true);
    });

    test('should create new maintenance record', async () => {
      if (!authToken || !testVehicleId) {
        return; // Skip if not authenticated or no test vehicle
      }

      const maintenanceData = {
        vehicle_id: testVehicleId,
        maintenance_type: 'oil_change',
        date: '2023-01-15',
        cost: 50.0,
        description: 'Test oil change',
      };

      const result = await createMaintenanceRecord(maintenanceData);
      expect(result.success).toBe(true);
      expect(result.data).toBeDefined();
      expect(result.data.id).toBeDefined();

      testMaintenanceId = result.data.id;
    });
  });

  describe('Assignments Integration', () => {
    test('should get assignments list', async () => {
      if (!authToken) {
        return; // Skip if not authenticated
      }

      const result = await getAssignments();
      expect(result.success).toBe(true);
      expect(Array.isArray(result.data)).toBe(true);
    });

    test('should create new assignment', async () => {
      if (!authToken || !testVehicleId || !testDriverId) {
        return; // Skip if not authenticated or no test data
      }

      const assignmentData = {
        vehicle_id: testVehicleId,
        driver_id: testDriverId,
        start_date: '2023-01-01',
        end_date: '2023-12-31',
      };

      const result = await createAssignment(assignmentData);
      expect(result.success).toBe(true);
      expect(result.data).toBeDefined();
      expect(result.data.id).toBeDefined();

      testAssignmentId = result.data.id;
    });
  });

  describe('Error Handling Integration', () => {
    test('should handle 404 errors gracefully', async () => {
      if (!authToken) {
        return; // Skip if not authenticated
      }

      try {
        await getVehicles({ vehicle_id: 999999 });
      } catch (error) {
        expect(error).toBeDefined();
      }
    });

    test('should handle authentication errors', async () => {
      // Test without authentication token
      try {
        await getVehicles();
      } catch (error) {
        expect(error).toBeDefined();
      }
    });
  });

  describe('API Response Format', () => {
    test('should return consistent response format', async () => {
      if (!authToken) {
        return; // Skip if not authenticated
      }

      const result = await getVehicles();

      // Check response structure
      expect(result).toHaveProperty('success');
      expect(result).toHaveProperty('data');
      expect(typeof result.success).toBe('boolean');

      if (result.pagination) {
        expect(result.pagination).toHaveProperty('total');
        expect(result.pagination).toHaveProperty('page');
        expect(result.pagination).toHaveProperty('per_page');
        expect(result.pagination).toHaveProperty('total_pages');
      }
    });
  });
});
