/**
 * Assignments API Tests
 * Tests for assignments.js API functions
 */
import {
  createAssignment,
  getAssignments,
  getAssignment,
  updateAssignment,
  deleteAssignment,
  getAssignmentStatistics,
  getDriverAssignments,
  getVehicleAssignments,
  ASSIGNMENT_ENDPOINTS,
} from '../../backend/api/assignments';

describe('Assignments API', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    global.fetch.mockClear();
  });

  describe('Assignment Endpoints', () => {
    test('should have correct API endpoints', () => {
      expect(ASSIGNMENT_ENDPOINTS.list).toBe('/api/assignments');
      expect(ASSIGNMENT_ENDPOINTS.create).toBe('/api/assignments');
      expect(ASSIGNMENT_ENDPOINTS.get).toBe('/api/assignments');
      expect(ASSIGNMENT_ENDPOINTS.update).toBe('/api/assignments');
      expect(ASSIGNMENT_ENDPOINTS.delete).toBe('/api/assignments');
    });
  });

  describe('Create Assignment', () => {
    test('should create assignment successfully', async () => {
      const mockResponse = {
        success: true,
        data: {
          id: 1,
          vehicle_id: 1,
          driver_id: 1,
          start_date: '2023-01-01',
          end_date: '2023-12-31',
          status: 'active',
        },
      };

      global.mockFetch(mockResponse);

      const assignmentData = {
        vehicle_id: 1,
        driver_id: 1,
        start_date: '2023-01-01',
        end_date: '2023-12-31',
      };

      const result = await createAssignment(assignmentData);

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/assignments'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
          body: JSON.stringify(assignmentData),
        })
      );

      expect(result).toEqual(mockResponse);
    });

    test('should handle create assignment error', async () => {
      const mockError = new Error('Assignment creation failed');
      global.mockFetchError(mockError);

      const assignmentData = {
        vehicle_id: 1,
        driver_id: 1,
        start_date: '2023-01-01',
      };

      await expect(createAssignment(assignmentData)).rejects.toThrow('Assignment creation failed');
    });
  });

  describe('Get Assignments', () => {
    test('should get assignments list successfully', async () => {
      const mockResponse = {
        success: true,
        data: [
          { id: 1, vehicle_id: 1, driver_id: 1, start_date: '2023-01-01', status: 'active' },
          { id: 2, vehicle_id: 2, driver_id: 2, start_date: '2023-01-15', status: 'active' },
        ],
        pagination: {
          total: 2,
          page: 1,
          per_page: 10,
          total_pages: 1,
        },
      };

      global.mockFetch(mockResponse);

      const result = await getAssignments();

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/assignments'),
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      );

      expect(result).toEqual(mockResponse);
    });

    test('should get assignments with query parameters', async () => {
      const mockResponse = {
        success: true,
        data: [{ id: 1, vehicle_id: 1, driver_id: 1, start_date: '2023-01-01', status: 'active' }],
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
        driver_id: 1,
        status: 'active',
      };

      const result = await getAssignments(params);

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining(
          '/api/assignments?skip=0&limit=10&vehicle_id=1&driver_id=1&status=active'
        ),
        expect.objectContaining({
          method: 'GET',
        })
      );

      expect(result).toEqual(mockResponse);
    });

    test('should handle get assignments error', async () => {
      const mockError = new Error('Failed to fetch assignments');
      global.mockFetchError(mockError);

      await expect(getAssignments()).rejects.toThrow('Failed to fetch assignments');
    });
  });

  describe('Get Assignment', () => {
    test('should get single assignment successfully', async () => {
      const mockResponse = {
        success: true,
        data: {
          id: 1,
          vehicle_id: 1,
          driver_id: 1,
          start_date: '2023-01-01',
          end_date: '2023-12-31',
          status: 'active',
        },
      };

      global.mockFetch(mockResponse);

      const result = await getAssignment(1);

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/assignments/1'),
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      );

      expect(result).toEqual(mockResponse);
    });

    test('should handle get assignment error', async () => {
      const mockError = new Error('Assignment not found');
      global.mockFetchError(mockError);

      await expect(getAssignment(999)).rejects.toThrow('Assignment not found');
    });
  });

  describe('Update Assignment', () => {
    test('should update assignment successfully', async () => {
      const mockResponse = {
        success: true,
        data: {
          id: 1,
          vehicle_id: 1,
          driver_id: 1,
          start_date: '2023-01-01',
          end_date: '2023-12-31',
          status: 'inactive',
        },
      };

      global.mockFetch(mockResponse);

      const updateData = {
        status: 'inactive',
      };

      const result = await updateAssignment(1, updateData);

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/assignments/1'),
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

    test('should handle update assignment error', async () => {
      const mockError = new Error('Assignment update failed');
      global.mockFetchError(mockError);

      const updateData = { status: 'inactive' };

      await expect(updateAssignment(1, updateData)).rejects.toThrow('Assignment update failed');
    });
  });

  describe('Delete Assignment', () => {
    test('should delete assignment successfully', async () => {
      const mockResponse = {
        success: true,
        message: 'Assignment deleted successfully',
      };

      global.mockFetch(mockResponse);

      const result = await deleteAssignment(1);

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/assignments/1'),
        expect.objectContaining({
          method: 'DELETE',
        })
      );

      expect(result).toEqual(mockResponse);
    });

    test('should handle delete assignment error', async () => {
      const mockError = new Error('Assignment deletion failed');
      global.mockFetchError(mockError);

      await expect(deleteAssignment(1)).rejects.toThrow('Assignment deletion failed');
    });
  });

  describe('Assignment Statistics', () => {
    test('should get assignment statistics successfully', async () => {
      const mockResponse = {
        success: true,
        data: {
          total_assignments: 25,
          active_assignments: 20,
          inactive_assignments: 5,
          by_status: {
            active: 20,
            inactive: 5,
          },
          average_assignment_duration: 180,
        },
      };

      global.mockFetch(mockResponse);

      const result = await getAssignmentStatistics();

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/assignments/statistics'),
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
            vehicle_id: 1,
            driver_id: 1,
            start_date: '2023-01-01',
            end_date: '2023-12-31',
            status: 'active',
          },
        ],
      };

      global.mockFetch(mockResponse);

      const result = await getDriverAssignments(1);

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/assignments/driver/1'),
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
        expect.stringContaining('/api/assignments/vehicle/1'),
        expect.objectContaining({
          method: 'GET',
        })
      );

      expect(result).toEqual(mockResponse);
    });
  });
});
