/**
 * Drivers API Tests
 * Tests for drivers.js API functions
 */
import {
  createDriver,
  getDrivers,
  getDriver,
  updateDriver,
  deleteDriver,
  searchDrivers,
  getDriverStatistics,
  getDriverAssignments,
  DRIVER_ENDPOINTS,
} from '../../backend/api/drivers';

describe('Drivers API', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    global.fetch.mockClear();
  });

  describe('Driver Endpoints', () => {
    test('should have correct API endpoints', () => {
      expect(DRIVER_ENDPOINTS.list).toBe('/api/drivers');
      expect(DRIVER_ENDPOINTS.create).toBe('/api/drivers');
      expect(DRIVER_ENDPOINTS.get).toBe('/api/drivers');
      expect(DRIVER_ENDPOINTS.update).toBe('/api/drivers');
      expect(DRIVER_ENDPOINTS.delete).toBe('/api/drivers');
    });
  });

  describe('Create Driver', () => {
    test('should create driver successfully', async () => {
      const mockResponse = {
        success: true,
        data: {
          id: 1,
          first_name: 'John',
          last_name: 'Doe',
          email: 'john.doe@example.com',
          phone: '+1234567890',
          license_number: 'DL123456',
          license_expiry: '2025-12-31',
          status: 'active',
        },
      };

      global.mockFetch(mockResponse);

      const driverData = {
        first_name: 'John',
        last_name: 'Doe',
        email: 'john.doe@example.com',
        phone: '+1234567890',
        license_number: 'DL123456',
        license_expiry: '2025-12-31',
        status: 'active',
      };

      const result = await createDriver(driverData);

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/drivers'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
          body: JSON.stringify(driverData),
        })
      );

      expect(result).toEqual(mockResponse);
    });

    test('should handle create driver error', async () => {
      const mockError = new Error('Driver creation failed');
      global.mockFetchError(mockError);

      const driverData = {
        first_name: 'John',
        last_name: 'Doe',
        email: 'john.doe@example.com',
      };

      await expect(createDriver(driverData)).rejects.toThrow('Driver creation failed');
    });
  });

  describe('Get Drivers', () => {
    test('should get drivers list successfully', async () => {
      const mockResponse = {
        success: true,
        data: [
          { id: 1, first_name: 'John', last_name: 'Doe', email: 'john.doe@example.com' },
          { id: 2, first_name: 'Jane', last_name: 'Smith', email: 'jane.smith@example.com' },
        ],
        pagination: {
          total: 2,
          page: 1,
          per_page: 10,
          total_pages: 1,
        },
      };

      global.mockFetch(mockResponse);

      const result = await getDrivers();

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/drivers'),
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      );

      expect(result).toEqual(mockResponse);
    });

    test('should get drivers with query parameters', async () => {
      const mockResponse = {
        success: true,
        data: [{ id: 1, first_name: 'John', last_name: 'Doe', email: 'john.doe@example.com' }],
        pagination: {
          total: 1,
          page: 1,
          per_page: 10,
          total_pages: 1,
        },
      };

      global.mockFetch(mockResponse);

      const params = {
        skip: 0,
        limit: 10,
        status_filter: 'active',
        search: 'John',
      };

      const result = await getDrivers(params);

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/drivers?skip=0&limit=10&status_filter=active&search=John'),
        expect.objectContaining({
          method: 'GET',
        })
      );

      expect(result).toEqual(mockResponse);
    });

    test('should handle get drivers error', async () => {
      const mockError = new Error('Failed to fetch drivers');
      global.mockFetchError(mockError);

      await expect(getDrivers()).rejects.toThrow('Failed to fetch drivers');
    });
  });

  describe('Get Driver', () => {
    test('should get single driver successfully', async () => {
      const mockResponse = {
        success: true,
        data: {
          id: 1,
          first_name: 'John',
          last_name: 'Doe',
          email: 'john.doe@example.com',
          phone: '+1234567890',
          license_number: 'DL123456',
          license_expiry: '2025-12-31',
          status: 'active',
        },
      };

      global.mockFetch(mockResponse);

      const result = await getDriver(1);

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/drivers/1'),
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      );

      expect(result).toEqual(mockResponse);
    });

    test('should handle get driver error', async () => {
      const mockError = new Error('Driver not found');
      global.mockFetchError(mockError);

      await expect(getDriver(999)).rejects.toThrow('Driver not found');
    });
  });

  describe('Update Driver', () => {
    test('should update driver successfully', async () => {
      const mockResponse = {
        success: true,
        data: {
          id: 1,
          first_name: 'John',
          last_name: 'Doe',
          email: 'john.doe@example.com',
          phone: '+1234567890',
          license_number: 'DL123456',
          license_expiry: '2025-12-31',
          status: 'inactive',
        },
      };

      global.mockFetch(mockResponse);

      const updateData = {
        status: 'inactive',
      };

      const result = await updateDriver(1, updateData);

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/drivers/1'),
        expect.objectContaining({
          method: 'PUT',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
          body: JSON.stringify(updateData),
        })
      );

      expect(result).toEqual(mockResponse);
    });

    test('should handle update driver error', async () => {
      const mockError = new Error('Driver update failed');
      global.mockFetchError(mockError);

      const updateData = { status: 'inactive' };

      await expect(updateDriver(1, updateData)).rejects.toThrow('Driver update failed');
    });
  });

  describe('Delete Driver', () => {
    test('should delete driver successfully', async () => {
      const mockResponse = {
        success: true,
        message: 'Driver deleted successfully',
      };

      global.mockFetch(mockResponse);

      const result = await deleteDriver(1);

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/drivers/1'),
        expect.objectContaining({
          method: 'DELETE',
        })
      );

      expect(result).toEqual(mockResponse);
    });

    test('should handle delete driver error', async () => {
      const mockError = new Error('Driver deletion failed');
      global.mockFetchError(mockError);

      await expect(deleteDriver(1)).rejects.toThrow('Driver deletion failed');
    });
  });

  describe('Search Drivers', () => {
    test('should search drivers successfully', async () => {
      const mockResponse = {
        success: true,
        data: [{ id: 1, first_name: 'John', last_name: 'Doe', email: 'john.doe@example.com' }],
        pagination: {
          total: 1,
          page: 1,
          per_page: 10,
          total_pages: 1,
        },
      };

      global.mockFetch(mockResponse);

      const searchParams = {
        query: 'John',
        filters: {
          status: 'active',
          license_expiry_from: '2024-01-01',
          license_expiry_to: '2025-12-31',
        },
      };

      const result = await searchDrivers(searchParams);

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/drivers/search'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
          body: JSON.stringify(searchParams),
        })
      );

      expect(result).toEqual(mockResponse);
    });

    test('should handle search drivers error', async () => {
      const mockError = new Error('Search failed');
      global.mockFetchError(mockError);

      const searchParams = { query: 'John' };

      await expect(searchDrivers(searchParams)).rejects.toThrow('Search failed');
    });
  });

  describe('Driver Statistics', () => {
    test('should get driver statistics successfully', async () => {
      const mockResponse = {
        success: true,
        data: {
          total_drivers: 50,
          active_drivers: 42,
          inactive_drivers: 8,
          by_status: {
            active: 42,
            inactive: 8,
          },
          license_expiry_warnings: 3,
        },
      };

      global.mockFetch(mockResponse);

      const result = await getDriverStatistics();

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/drivers/statistics'),
        expect.objectContaining({
          method: 'GET',
        })
      );

      expect(result).toEqual(mockResponse);
    });
  });

  describe('Driver Assignments', () => {
    test('should get driver assignments successfully', async () => {
      const mockResponse = {
        success: true,
        data: [
          {
            id: 1,
            driver_id: 1,
            vehicle_id: 1,
            start_date: '2023-01-01',
            end_date: '2023-12-31',
            status: 'active',
          },
        ],
      };

      global.mockFetch(mockResponse);

      const result = await getDriverAssignments(1);

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/drivers/1/assignments'),
        expect.objectContaining({
          method: 'GET',
        })
      );

      expect(result).toEqual(mockResponse);
    });
  });
});
