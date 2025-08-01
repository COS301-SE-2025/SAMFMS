// src/backend/api/maintenance.js
import { httpClient } from '../services/httpClient';
import { API_ENDPOINTS } from '../../config/apiConfig';
import {
  withRetry,
  handleApiResponse,
  parseApiError,
  validateRequiredFields,
  ERROR_TYPES,
} from '../../utils/errorHandler';

export const maintenanceAPI = {
  // Maintenance Records
  async getMaintenanceRecords(vehicleId = null, status = null, page = 1, size = 20) {
    return withRetry(async () => {
      const params = new URLSearchParams();
      if (vehicleId) params.append('vehicle_id', vehicleId);
      if (status) params.append('status', status);
      params.append('skip', (page - 1) * size);
      params.append('limit', size);

      const response = await httpClient.get(`${API_ENDPOINTS.MAINTENANCE.RECORDS.LIST}?${params}`);
      const result = handleApiResponse(response);

      // Transform backend data to match frontend expectations
      if (result.data && Array.isArray(result.data)) {
        result.data = result.data.map(record => transformMaintenanceRecord(record));
      }

      return result;
    });
  },

  async createMaintenanceRecord(recordData) {
    validateRequiredFields(recordData, [
      'vehicle_id',
      'maintenance_type',
      'title',
      'scheduled_date',
    ]);

    // Validate dates
    if (recordData.scheduled_date) {
      const scheduledDate = new Date(recordData.scheduled_date);
      if (isNaN(scheduledDate.getTime())) {
        throw parseApiError({
          response: {
            status: 400,
            data: { message: 'Invalid scheduled_date format', error_code: ERROR_TYPES.VALIDATION },
          },
        });
      }
      // Ensure proper ISO format
      recordData.scheduled_date = scheduledDate.toISOString();
    }

    // Validate cost fields
    const costFields = ['estimated_cost', 'actual_cost', 'labor_cost', 'parts_cost'];
    costFields.forEach(field => {
      if (recordData[field] !== undefined && recordData[field] !== null) {
        const cost = parseFloat(recordData[field]);
        if (isNaN(cost) || cost < 0) {
          throw parseApiError({
            response: {
              status: 400,
              data: {
                message: `Invalid ${field}: must be a positive number`,
                error_code: ERROR_TYPES.VALIDATION,
              },
            },
          });
        }
        recordData[field] = cost;
      }
    });

    return withRetry(
      async () => {
        const response = await httpClient.post(
          API_ENDPOINTS.MAINTENANCE.RECORDS.CREATE,
          recordData
        );
        const result = handleApiResponse(response);

        // Transform response data
        if (result.data) {
          result.data = transformMaintenanceRecord(result.data);
        }

        return result;
      },
      { maxRetries: 1 }
    );
  },

  async updateMaintenanceRecord(recordId, recordData) {
    if (!recordId) {
      throw parseApiError({
        response: {
          status: 400,
          data: { message: 'Record ID is required', error_code: ERROR_TYPES.VALIDATION },
        },
      });
    }

    return withRetry(
      async () => {
        const response = await httpClient.put(
          API_ENDPOINTS.MAINTENANCE.RECORDS.UPDATE(recordId),
          recordData
        );
        return handleApiResponse(response);
      },
      { maxRetries: 1 }
    );
  },

  async deleteMaintenanceRecord(recordId) {
    if (!recordId) {
      throw parseApiError({
        response: {
          status: 400,
          data: { message: 'Record ID is required', error_code: ERROR_TYPES.VALIDATION },
        },
      });
    }

    return withRetry(
      async () => {
        const response = await httpClient.delete(
          API_ENDPOINTS.MAINTENANCE.RECORDS.DELETE(recordId)
        );
        return handleApiResponse(response);
      },
      { maxRetries: 1 }
    );
  },

  async getMaintenanceRecord(recordId) {
    if (!recordId) {
      throw parseApiError({
        response: {
          status: 400,
          data: { message: 'Record ID is required', error_code: ERROR_TYPES.VALIDATION },
        },
      });
    }

    return withRetry(async () => {
      const response = await httpClient.get(API_ENDPOINTS.MAINTENANCE.RECORDS.GET(recordId));
      return handleApiResponse(response);
    });
  },

  async getVehicleMaintenanceHistory(vehicleId) {
    if (!vehicleId) {
      throw parseApiError({
        response: {
          status: 400,
          data: { message: 'Vehicle ID is required', error_code: ERROR_TYPES.VALIDATION },
        },
      });
    }

    return withRetry(async () => {
      const response = await httpClient.get(
        API_ENDPOINTS.MAINTENANCE.RECORDS.BY_VEHICLE(vehicleId)
      );
      return handleApiResponse(response);
    });
  },

  async getOverdueMaintenanceRecords() {
    return withRetry(async () => {
      const response = await httpClient.get(API_ENDPOINTS.MAINTENANCE.RECORDS.OVERDUE);
      return handleApiResponse(response);
    });
  },

  // Maintenance Schedules
  async getMaintenanceSchedules(vehicleId = null) {
    return withRetry(async () => {
      const params = vehicleId ? `?vehicle_id=${vehicleId}` : '';
      const response = await httpClient.get(`${API_ENDPOINTS.MAINTENANCE.SCHEDULES.LIST}${params}`);
      return handleApiResponse(response);
    });
  },

  async createMaintenanceSchedule(scheduleData) {
    validateRequiredFields(scheduleData, [
      'vehicle_id',
      'maintenance_type',
      'title',
      'scheduled_date',
      'interval_type',
      'interval_value',
    ]);

    return withRetry(
      async () => {
        const response = await httpClient.post(
          API_ENDPOINTS.MAINTENANCE.SCHEDULES.CREATE,
          scheduleData
        );
        return handleApiResponse(response);
      },
      { maxRetries: 1 }
    );
  },

  async updateMaintenanceSchedule(scheduleId, scheduleData) {
    if (!scheduleId) {
      throw parseApiError({
        response: {
          status: 400,
          data: { message: 'Schedule ID is required', error_code: ERROR_TYPES.VALIDATION },
        },
      });
    }

    return withRetry(
      async () => {
        const response = await httpClient.put(
          API_ENDPOINTS.MAINTENANCE.SCHEDULES.UPDATE(scheduleId),
          scheduleData
        );
        return handleApiResponse(response);
      },
      { maxRetries: 1 }
    );
  },

  async deleteMaintenanceSchedule(scheduleId) {
    if (!scheduleId) {
      throw parseApiError({
        response: {
          status: 400,
          data: { message: 'Schedule ID is required', error_code: ERROR_TYPES.VALIDATION },
        },
      });
    }

    return withRetry(
      async () => {
        const response = await httpClient.delete(
          API_ENDPOINTS.MAINTENANCE.SCHEDULES.DELETE(scheduleId)
        );
        return handleApiResponse(response);
      },
      { maxRetries: 1 }
    );
  },

  // License Records
  async getLicenseRecords(vehicleId = null, licenseType = null) {
    return withRetry(async () => {
      const params = new URLSearchParams();
      if (vehicleId) params.append('vehicle_id', vehicleId);
      if (licenseType) params.append('license_type', licenseType);

      const response = await httpClient.get(`${API_ENDPOINTS.MAINTENANCE.LICENSES.LIST}?${params}`);
      return handleApiResponse(response);
    });
  },

  async createLicenseRecord(licenseData) {
    validateRequiredFields(licenseData, [
      'entity_id',
      'entity_type',
      'license_type',
      'issue_date',
      'expiry_date',
    ]);

    return withRetry(
      async () => {
        const response = await httpClient.post(
          API_ENDPOINTS.MAINTENANCE.LICENSES.CREATE,
          licenseData
        );
        return handleApiResponse(response);
      },
      { maxRetries: 1 }
    );
  },

  async updateLicenseRecord(licenseId, licenseData) {
    if (!licenseId) {
      throw parseApiError({
        response: {
          status: 400,
          data: { message: 'License ID is required', error_code: ERROR_TYPES.VALIDATION },
        },
      });
    }

    return withRetry(
      async () => {
        const response = await httpClient.put(
          API_ENDPOINTS.MAINTENANCE.LICENSES.UPDATE(licenseId),
          licenseData
        );
        return handleApiResponse(response);
      },
      { maxRetries: 1 }
    );
  },

  async deleteLicenseRecord(licenseId) {
    if (!licenseId) {
      throw parseApiError({
        response: {
          status: 400,
          data: { message: 'License ID is required', error_code: ERROR_TYPES.VALIDATION },
        },
      });
    }

    return withRetry(
      async () => {
        const response = await httpClient.delete(
          API_ENDPOINTS.MAINTENANCE.LICENSES.DELETE(licenseId)
        );
        return handleApiResponse(response);
      },
      { maxRetries: 1 }
    );
  },

  async getExpiringLicenses(days = 30) {
    return withRetry(async () => {
      const response = await httpClient.get(
        `${API_ENDPOINTS.MAINTENANCE.LICENSES.EXPIRING}?days=${days}`
      );
      return handleApiResponse(response);
    });
  },

  // Maintenance Vendors
  async getMaintenanceVendors() {
    return withRetry(async () => {
      const response = await httpClient.get(API_ENDPOINTS.MAINTENANCE.VENDORS.LIST);
      return handleApiResponse(response);
    });
  },

  async createMaintenanceVendor(vendorData) {
    validateRequiredFields(vendorData, ['name', 'contact_info']);

    return withRetry(
      async () => {
        const response = await httpClient.post(
          API_ENDPOINTS.MAINTENANCE.VENDORS.CREATE,
          vendorData
        );
        return handleApiResponse(response);
      },
      { maxRetries: 1 }
    );
  },

  async updateMaintenanceVendor(vendorId, vendorData) {
    if (!vendorId) {
      throw parseApiError({
        response: {
          status: 400,
          data: { message: 'Vendor ID is required', error_code: ERROR_TYPES.VALIDATION },
        },
      });
    }

    return withRetry(
      async () => {
        const response = await httpClient.put(
          API_ENDPOINTS.MAINTENANCE.VENDORS.UPDATE(vendorId),
          vendorData
        );
        return handleApiResponse(response);
      },
      { maxRetries: 1 }
    );
  },

  async deleteMaintenanceVendor(vendorId) {
    if (!vendorId) {
      throw parseApiError({
        response: {
          status: 400,
          data: { message: 'Vendor ID is required', error_code: ERROR_TYPES.VALIDATION },
        },
      });
    }

    return withRetry(
      async () => {
        const response = await httpClient.delete(
          API_ENDPOINTS.MAINTENANCE.VENDORS.DELETE(vendorId)
        );
        return handleApiResponse(response);
      },
      { maxRetries: 1 }
    );
  },

  // Analytics
  async getMaintenanceAnalytics(vehicleId = null, startDate = null, endDate = null) {
    return withRetry(async () => {
      const params = new URLSearchParams();
      if (vehicleId) params.append('vehicle_id', vehicleId);
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);

      const response = await httpClient.get(
        `${API_ENDPOINTS.MAINTENANCE.ANALYTICS.OVERVIEW}?${params}`
      );
      return handleApiResponse(response);
    });
  },

  async getCostAnalytics(period = 'monthly', vehicleId = null) {
    return withRetry(async () => {
      const params = new URLSearchParams();
      params.append('period', period);
      if (vehicleId) params.append('vehicle_id', vehicleId);

      const response = await httpClient.get(
        `${API_ENDPOINTS.MAINTENANCE.ANALYTICS.COSTS}?${params}`
      );
      return handleApiResponse(response);
    });
  },

  async getMaintenanceDashboard() {
    return withRetry(async () => {
      const response = await httpClient.get(API_ENDPOINTS.MAINTENANCE.ANALYTICS.DASHBOARD);
      return handleApiResponse(response);
    });
  },

  // Notifications
  async getMaintenanceNotifications(page = 1, size = 20) {
    return withRetry(async () => {
      const response = await httpClient.get(
        `${API_ENDPOINTS.MAINTENANCE.NOTIFICATIONS.LIST}?page=${page}&size=${size}`
      );
      return handleApiResponse(response);
    });
  },

  async markNotificationAsRead(notificationId) {
    if (!notificationId) {
      throw parseApiError({
        response: {
          status: 400,
          data: { message: 'Notification ID is required', error_code: ERROR_TYPES.VALIDATION },
        },
      });
    }

    return withRetry(
      async () => {
        const response = await httpClient.put(
          API_ENDPOINTS.MAINTENANCE.NOTIFICATIONS.MARK_READ(notificationId)
        );
        return handleApiResponse(response);
      },
      { maxRetries: 1 }
    );
  },

  async deleteNotification(notificationId) {
    if (!notificationId) {
      throw parseApiError({
        response: {
          status: 400,
          data: { message: 'Notification ID is required', error_code: ERROR_TYPES.VALIDATION },
        },
      });
    }

    return withRetry(
      async () => {
        const response = await httpClient.delete(
          API_ENDPOINTS.MAINTENANCE.NOTIFICATIONS.DELETE(notificationId)
        );
        return handleApiResponse(response);
      },
      { maxRetries: 1 }
    );
  },
};

/**
 * Transform maintenance record from backend format to frontend format
 */
function transformMaintenanceRecord(record) {
  if (!record) return record;

  const transformed = {
    ...record,
    // Ensure dates are properly formatted
    scheduled_date: record.scheduled_date ? new Date(record.scheduled_date).toISOString() : null,
    actual_start_date: record.actual_start_date
      ? new Date(record.actual_start_date).toISOString()
      : null,
    actual_completion_date: record.actual_completion_date
      ? new Date(record.actual_completion_date).toISOString()
      : null,
    created_at: record.created_at ? new Date(record.created_at).toISOString() : null,
    updated_at: record.updated_at ? new Date(record.updated_at).toISOString() : null,

    // Calculate computed fields
    total_cost: calculateTotalCost(record),
    is_overdue: isMaintenanceOverdue(record),
    days_until_due: calculateDaysUntilDue(record),

    // Ensure numeric fields are properly typed
    estimated_cost: parseFloat(record.estimated_cost) || 0,
    actual_cost: parseFloat(record.actual_cost) || 0,
    labor_cost: parseFloat(record.labor_cost) || 0,
    parts_cost: parseFloat(record.parts_cost) || 0,
    other_costs: parseFloat(record.other_costs) || 0,

    // Ensure arrays exist
    parts_used: record.parts_used || [],
    photos: record.photos || [],
    documents: record.documents || [],
  };

  return transformed;
}

/**
 * Calculate total cost from individual cost components
 */
function calculateTotalCost(record) {
  const labor = parseFloat(record.labor_cost) || 0;
  const parts = parseFloat(record.parts_cost) || 0;
  const other = parseFloat(record.other_costs) || 0;
  const actual = parseFloat(record.actual_cost) || 0;

  // Use actual_cost if available, otherwise sum components
  return actual > 0 ? actual : labor + parts + other;
}

/**
 * Check if maintenance is overdue
 */
function isMaintenanceOverdue(record) {
  if (record.status === 'completed' || record.status === 'cancelled') {
    return false;
  }

  const scheduledDate = new Date(record.scheduled_date);
  const now = new Date();

  return scheduledDate < now;
}

/**
 * Calculate days until maintenance is due
 */
function calculateDaysUntilDue(record) {
  if (record.status === 'completed' || record.status === 'cancelled') {
    return null;
  }

  const scheduledDate = new Date(record.scheduled_date);
  const now = new Date();
  const diffTime = scheduledDate - now;
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

  return diffDays;
}

/**
 * Maintenance error codes specific to maintenance service
 */
export const MAINTENANCE_ERROR_CODES = {
  INVALID_VEHICLE: 'INVALID_VEHICLE',
  INVALID_MAINTENANCE_TYPE: 'INVALID_MAINTENANCE_TYPE',
  INVALID_DATE: 'INVALID_DATE',
  INVALID_COST: 'INVALID_COST',
  DUPLICATE_MAINTENANCE: 'DUPLICATE_MAINTENANCE',
  VENDOR_NOT_FOUND: 'VENDOR_NOT_FOUND',
  TECHNICIAN_NOT_AVAILABLE: 'TECHNICIAN_NOT_AVAILABLE',
  PARTS_NOT_AVAILABLE: 'PARTS_NOT_AVAILABLE',
};

export default maintenanceAPI;
