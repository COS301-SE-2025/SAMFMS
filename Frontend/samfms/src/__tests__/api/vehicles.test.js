/**
 * Vehicles API Tests
 * Tests for vehicles.js API functions
 */
import {
  createVehicle,
  getVehicles,
  getVehicle,
  updateVehicle,
  deleteVehicle,
  searchVehicles,
  getVehicleStatistics,
  getVehicleAssignments,
  getVehicleMaintenanceHistory,
  VEHICLE_ENDPOINTS,
} from '../../backend/api/vehicles';

describe('Vehicles API', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    global.fetch.mockClear();
  });

  describe('Vehicle Endpoints', () => {
    test('should have correct API endpoints', () => {
      expect(VEHICLE_ENDPOINTS.list).toBe('/api/vehicles');
      expect(VEHICLE_ENDPOINTS.create).toBe('/api/vehicles');
      expect(VEHICLE_ENDPOINTS.get).toBe('/api/vehicles');
      expect(VEHICLE_ENDPOINTS.update).toBe('/api/vehicles');
      expect(VEHICLE_ENDPOINTS.delete).toBe('/api/vehicles');
      expect(VEHICLE_ENDPOINTS.search).toBe('/api/vehicles/search');
    });
  });

  describe('Create Vehicle', () => {
    test('should create vehicle successfully', async () => {
      const mockResponse = {
        success: true,
        data: {
          id: 1,
          make: 'Toyota',
          model: 'Camry',
          year: 2023,
          license_plate: 'ABC123',
          status: 'active',
        },
      };

      global.mockFetch(mockResponse);

      const vehicleData = {
        make: 'Toyota',
        model: 'Camry',
        year: 2023,
        license_plate: 'ABC123',
        status: 'active',
      };

      const result = await createVehicle(vehicleData);

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/vehicles'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
          body: JSON.stringify(vehicleData),
        })
      );

      expect(result).toEqual(mockResponse);
    });

    test('should handle create vehicle error', async () => {
      const mockError = new Error('Vehicle creation failed');
      global.mockFetchError(mockError);

      const vehicleData = {
        make: 'Toyota',
        model: 'Camry',
        year: 2023,
        license_plate: 'ABC123',
      };

      await expect(createVehicle(vehicleData)).rejects.toThrow('Vehicle creation failed');
    });
  });

  describe('Get Vehicles', () => {
    test('should get vehicles list successfully', async () => {
      const mockResponse = {
        success: true,
        data: [
          { id: 1, make: 'Toyota', model: 'Camry', license_plate: 'ABC123' },
          { id: 2, make: 'Honda', model: 'Civic', license_plate: 'XYZ789' },
        ],
        pagination: {
          total: 2,
          page: 1,
          per_page: 10,
          total_pages: 1,
        },
      };

      global.mockFetch(mockResponse);

      const result = await getVehicles();

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/vehicles'),
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      );

      expect(result).toEqual(mockResponse);
    });

    test('should get vehicles with query parameters', async () => {
      const mockResponse = {
        success: true,
        data: [{ id: 1, make: 'Toyota', model: 'Camry', license_plate: 'ABC123' }],
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
        make_filter: 'Toyota',
      };

      const result = await getVehicles(params);

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining(
          '/api/vehicles?skip=0&limit=10&status_filter=active&make_filter=Toyota'
        ),
        expect.objectContaining({
          method: 'GET',
        })
      );

      expect(result).toEqual(mockResponse);
    });

    test('should handle get vehicles error', async () => {
      const mockError = new Error('Failed to fetch vehicles');
      global.mockFetchError(mockError);

      await expect(getVehicles()).rejects.toThrow('Failed to fetch vehicles');
    });
  });

  describe('Get Vehicle', () => {
    test('should get single vehicle successfully', async () => {
      const mockResponse = {
        success: true,
        data: {
          id: 1,
          make: 'Toyota',
          model: 'Camry',
          year: 2023,
          license_plate: 'ABC123',
          status: 'active',
        },
      };

      global.mockFetch(mockResponse);

      const result = await getVehicle(1);

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/vehicles/1'),
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      );

      expect(result).toEqual(mockResponse);
    });

    test('should handle get vehicle error', async () => {
      const mockError = new Error('Vehicle not found');
      global.mockFetchError(mockError);

      await expect(getVehicle(999)).rejects.toThrow('Vehicle not found');
    });
  });

  describe('Update Vehicle', () => {
    test('should update vehicle successfully', async () => {
      const mockResponse = {
        success: true,
        data: {
          id: 1,
          make: 'Toyota',
          model: 'Camry',
          year: 2023,
          license_plate: 'ABC123',
          status: 'inactive',
        },
      };

      global.mockFetch(mockResponse);

      const updateData = {
        status: 'inactive',
      };

      const result = await updateVehicle(1, updateData);

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/vehicles/1'),
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

    test('should handle update vehicle error', async () => {
      const mockError = new Error('Vehicle update failed');
      global.mockFetchError(mockError);

      const updateData = { status: 'inactive' };

      await expect(updateVehicle(1, updateData)).rejects.toThrow('Vehicle update failed');
    });
  });

  describe('Delete Vehicle', () => {
    test('should delete vehicle successfully', async () => {
      const mockResponse = {
        success: true,
        message: 'Vehicle deleted successfully',
      };

      global.mockFetch(mockResponse);

      const result = await deleteVehicle(1);

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/vehicles/1'),
        expect.objectContaining({
          method: 'DELETE',
        })
      );

      expect(result).toEqual(mockResponse);
    });

    test('should handle delete vehicle error', async () => {
      const mockError = new Error('Vehicle deletion failed');
      global.mockFetchError(mockError);

      await expect(deleteVehicle(1)).rejects.toThrow('Vehicle deletion failed');
    });
  });

  describe('Search Vehicles', () => {
    test('should search vehicles successfully', async () => {
      const mockResponse = {
        success: true,
        data: [{ id: 1, make: 'Toyota', model: 'Camry', license_plate: 'ABC123' }],
        pagination: {
          total: 1,
          page: 1,
          per_page: 10,
          total_pages: 1,
        },
      };

      global.mockFetch(mockResponse);

      const searchParams = {
        query: 'Toyota',
        filters: {
          status: 'active',
          year_from: 2020,
          year_to: 2023,
        },
      };

      const result = await searchVehicles(searchParams);

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/vehicles/search'),
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

    test('should handle search vehicles error', async () => {
      const mockError = new Error('Search failed');
      global.mockFetchError(mockError);

      const searchParams = { query: 'Toyota' };

      await expect(searchVehicles(searchParams)).rejects.toThrow('Search failed');
    });
  });

  describe('Vehicle Statistics', () => {
    test('should get vehicle statistics successfully', async () => {
      const mockResponse = {
        success: true,
        data: {
          total_vehicles: 100,
          active_vehicles: 85,
          inactive_vehicles: 15,
          by_make: {
            Toyota: 30,
            Honda: 25,
            Ford: 20,
          },
          by_status: {
            active: 85,
            inactive: 15,
          },
        },
      };

      global.mockFetch(mockResponse);

      const result = await getVehicleStatistics();

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/vehicles/statistics'),
        expect.objectContaining({
          method: 'GET',
        })
      );

      expect(result).toEqual(mockResponse);
    });
  });

  describe('Vehicle Assignments', () => {
    test('should get vehicle assignments successfully', async () => {
      const mockResponse = {
        success: true,
        data: [
          {
            id: 1,
            vehicle_id: 1,
            driver_id: 1,
            start_date: '2023-01-01',
            end_date: '2023-12-31',
            status: 'active',
          },
        ],
      };

      global.mockFetch(mockResponse);

      const result = await getVehicleAssignments(1);

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/vehicles/1/assignments'),
        expect.objectContaining({
          method: 'GET',
        })
      );

      expect(result).toEqual(mockResponse);
    });
  });

  describe('Vehicle Maintenance History', () => {
    test('should get vehicle maintenance history successfully', async () => {
      const mockResponse = {
        success: true,
        data: [
          {
            id: 1,
            vehicle_id: 1,
            maintenance_type: 'oil_change',
            date: '2023-01-15',
            cost: 50.0,
            description: 'Regular oil change',
          },
        ],
      };

      global.mockFetch(mockResponse);

      const result = await getVehicleMaintenanceHistory(1);

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/vehicles/1/maintenance'),
        expect.objectContaining({
          method: 'GET',
        })
      );

      expect(result).toEqual(mockResponse);
    });
  });
});
