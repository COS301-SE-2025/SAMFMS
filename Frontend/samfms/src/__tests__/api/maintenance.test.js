/**
 * Maintenance API Tests
 * Tests for maintenance.js API functions
 */
import {
  createMaintenanceRecord,
  getMaintenanceRecords,
  getMaintenanceRecord,
  updateMaintenanceRecord,
  deleteMaintenanceRecord,
  scheduleMaintenanceTask,
  getMaintenanceSchedule,
  getMaintenanceAnalytics,
  getMaintenanceStatistics,
  MAINTENANCE_ENDPOINTS,
} from '../../backend/api/maintenance';

describe('Maintenance API', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    global.fetch.mockClear();
  });

  describe('Maintenance Endpoints', () => {
    test('should have correct API endpoints', () => {
      expect(MAINTENANCE_ENDPOINTS.list).toBe('/api/maintenance');
      expect(MAINTENANCE_ENDPOINTS.create).toBe('/api/maintenance');
      expect(MAINTENANCE_ENDPOINTS.get).toBe('/api/maintenance');
      expect(MAINTENANCE_ENDPOINTS.update).toBe('/api/maintenance');
      expect(MAINTENANCE_ENDPOINTS.delete).toBe('/api/maintenance');
      expect(MAINTENANCE_ENDPOINTS.schedule).toBe('/api/maintenance/schedule');
      expect(MAINTENANCE_ENDPOINTS.analytics).toBe('/api/maintenance/analytics');
    });
  });

  describe('Create Maintenance Record', () => {
    test('should create maintenance record successfully', async () => {
      const mockResponse = {
        success: true,
        data: {
          id: 1,
          vehicle_id: 1,
          maintenance_type: 'oil_change',
          date: '2023-01-15',
          cost: 50.0,
          description: 'Regular oil change',
          status: 'completed',
        },
      };

      global.mockFetch(mockResponse);

      const maintenanceData = {
        vehicle_id: 1,
        maintenance_type: 'oil_change',
        date: '2023-01-15',
        cost: 50.0,
        description: 'Regular oil change',
      };

      const result = await createMaintenanceRecord(maintenanceData);

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/maintenance'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
          body: JSON.stringify(maintenanceData),
        })
      );

      expect(result).toEqual(mockResponse);
    });

    test('should handle create maintenance record error', async () => {
      const mockError = new Error('Maintenance record creation failed');
      global.mockFetchError(mockError);

      const maintenanceData = {
        vehicle_id: 1,
        maintenance_type: 'oil_change',
        date: '2023-01-15',
      };

      await expect(createMaintenanceRecord(maintenanceData)).rejects.toThrow(
        'Maintenance record creation failed'
      );
    });
  });

  describe('Get Maintenance Records', () => {
    test('should get maintenance records list successfully', async () => {
      const mockResponse = {
        success: true,
        data: [
          { id: 1, vehicle_id: 1, maintenance_type: 'oil_change', date: '2023-01-15' },
          { id: 2, vehicle_id: 2, maintenance_type: 'tire_rotation', date: '2023-01-20' },
        ],
        pagination: {
          total: 2,
          page: 1,
          per_page: 10,
          total_pages: 1,
        },
      };

      global.mockFetch(mockResponse);

      const result = await getMaintenanceRecords();

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/maintenance'),
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      );

      expect(result).toEqual(mockResponse);
    });

    test('should get maintenance records with query parameters', async () => {
      const mockResponse = {
        success: true,
        data: [{ id: 1, vehicle_id: 1, maintenance_type: 'oil_change', date: '2023-01-15' }],
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
        vehicle_id: 1,
        maintenance_type: 'oil_change',
        date_from: '2023-01-01',
        date_to: '2023-12-31',
      };

      const result = await getMaintenanceRecords(params);

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining(
          '/api/maintenance?skip=0&limit=10&vehicle_id=1&maintenance_type=oil_change&date_from=2023-01-01&date_to=2023-12-31'
        ),
        expect.objectContaining({
          method: 'GET',
        })
      );

      expect(result).toEqual(mockResponse);
    });

    test('should handle get maintenance records error', async () => {
      const mockError = new Error('Failed to fetch maintenance records');
      global.mockFetchError(mockError);

      await expect(getMaintenanceRecords()).rejects.toThrow('Failed to fetch maintenance records');
    });
  });

  describe('Get Maintenance Record', () => {
    test('should get single maintenance record successfully', async () => {
      const mockResponse = {
        success: true,
        data: {
          id: 1,
          vehicle_id: 1,
          maintenance_type: 'oil_change',
          date: '2023-01-15',
          cost: 50.0,
          description: 'Regular oil change',
          status: 'completed',
        },
      };

      global.mockFetch(mockResponse);

      const result = await getMaintenanceRecord(1);

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/maintenance/1'),
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      );

      expect(result).toEqual(mockResponse);
    });

    test('should handle get maintenance record error', async () => {
      const mockError = new Error('Maintenance record not found');
      global.mockFetchError(mockError);

      await expect(getMaintenanceRecord(999)).rejects.toThrow('Maintenance record not found');
    });
  });

  describe('Update Maintenance Record', () => {
    test('should update maintenance record successfully', async () => {
      const mockResponse = {
        success: true,
        data: {
          id: 1,
          vehicle_id: 1,
          maintenance_type: 'oil_change',
          date: '2023-01-15',
          cost: 75.0,
          description: 'Premium oil change',
          status: 'completed',
        },
      };

      global.mockFetch(mockResponse);

      const updateData = {
        cost: 75.0,
        description: 'Premium oil change',
      };

      const result = await updateMaintenanceRecord(1, updateData);

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/maintenance/1'),
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

    test('should handle update maintenance record error', async () => {
      const mockError = new Error('Maintenance record update failed');
      global.mockFetchError(mockError);

      const updateData = { cost: 75.0 };

      await expect(updateMaintenanceRecord(1, updateData)).rejects.toThrow(
        'Maintenance record update failed'
      );
    });
  });

  describe('Delete Maintenance Record', () => {
    test('should delete maintenance record successfully', async () => {
      const mockResponse = {
        success: true,
        message: 'Maintenance record deleted successfully',
      };

      global.mockFetch(mockResponse);

      const result = await deleteMaintenanceRecord(1);

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/maintenance/1'),
        expect.objectContaining({
          method: 'DELETE',
        })
      );

      expect(result).toEqual(mockResponse);
    });

    test('should handle delete maintenance record error', async () => {
      const mockError = new Error('Maintenance record deletion failed');
      global.mockFetchError(mockError);

      await expect(deleteMaintenanceRecord(1)).rejects.toThrow(
        'Maintenance record deletion failed'
      );
    });
  });

  describe('Schedule Maintenance Task', () => {
    test('should schedule maintenance task successfully', async () => {
      const mockResponse = {
        success: true,
        data: {
          id: 1,
          vehicle_id: 1,
          maintenance_type: 'oil_change',
          scheduled_date: '2023-02-15',
          priority: 'medium',
          status: 'scheduled',
        },
      };

      global.mockFetch(mockResponse);

      const scheduleData = {
        vehicle_id: 1,
        maintenance_type: 'oil_change',
        scheduled_date: '2023-02-15',
        priority: 'medium',
      };

      const result = await scheduleMaintenanceTask(scheduleData);

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/maintenance/schedule'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
          body: JSON.stringify(scheduleData),
        })
      );

      expect(result).toEqual(mockResponse);
    });

    test('should handle schedule maintenance task error', async () => {
      const mockError = new Error('Maintenance task scheduling failed');
      global.mockFetchError(mockError);

      const scheduleData = {
        vehicle_id: 1,
        maintenance_type: 'oil_change',
        scheduled_date: '2023-02-15',
      };

      await expect(scheduleMaintenanceTask(scheduleData)).rejects.toThrow(
        'Maintenance task scheduling failed'
      );
    });
  });

  describe('Get Maintenance Schedule', () => {
    test('should get maintenance schedule successfully', async () => {
      const mockResponse = {
        success: true,
        data: [
          {
            id: 1,
            vehicle_id: 1,
            maintenance_type: 'oil_change',
            scheduled_date: '2023-02-15',
            priority: 'medium',
            status: 'scheduled',
          },
          {
            id: 2,
            vehicle_id: 2,
            maintenance_type: 'tire_rotation',
            scheduled_date: '2023-02-20',
            priority: 'low',
            status: 'scheduled',
          },
        ],
      };

      global.mockFetch(mockResponse);

      const params = {
        date_from: '2023-02-01',
        date_to: '2023-02-28',
        vehicle_id: 1,
      };

      const result = await getMaintenanceSchedule(params);

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining(
          '/api/maintenance/schedule?date_from=2023-02-01&date_to=2023-02-28&vehicle_id=1'
        ),
        expect.objectContaining({
          method: 'GET',
        })
      );

      expect(result).toEqual(mockResponse);
    });
  });

  describe('Get Maintenance Analytics', () => {
    test('should get maintenance analytics successfully', async () => {
      const mockResponse = {
        success: true,
        data: {
          total_maintenance_cost: 5000.0,
          average_cost_per_vehicle: 250.0,
          maintenance_by_type: {
            oil_change: 20,
            tire_rotation: 15,
            brake_service: 10,
          },
          maintenance_by_month: {
            '2023-01': 800.0,
            '2023-02': 1200.0,
            '2023-03': 950.0,
          },
          upcoming_maintenance: [
            {
              vehicle_id: 1,
              maintenance_type: 'oil_change',
              scheduled_date: '2023-02-15',
            },
          ],
        },
      };

      global.mockFetch(mockResponse);

      const params = {
        date_from: '2023-01-01',
        date_to: '2023-12-31',
        vehicle_id: 1,
      };

      const result = await getMaintenanceAnalytics(params);

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining(
          '/api/maintenance/analytics?date_from=2023-01-01&date_to=2023-12-31&vehicle_id=1'
        ),
        expect.objectContaining({
          method: 'GET',
        })
      );

      expect(result).toEqual(mockResponse);
    });
  });

  describe('Get Maintenance Statistics', () => {
    test('should get maintenance statistics successfully', async () => {
      const mockResponse = {
        success: true,
        data: {
          total_records: 100,
          completed_records: 85,
          pending_records: 15,
          average_cost: 125.5,
          most_common_type: 'oil_change',
          vehicles_needing_maintenance: 5,
        },
      };

      global.mockFetch(mockResponse);

      const result = await getMaintenanceStatistics();

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/maintenance/statistics'),
        expect.objectContaining({
          method: 'GET',
        })
      );

      expect(result).toEqual(mockResponse);
    });
  });
});
