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
      params.append('page', page);
      params.append('size', size);

      const response = await httpClient.get(`${API_ENDPOINTS.MAINTENANCE.RECORDS.LIST}?${params}`);
      return handleApiResponse(response);
    });
  },

  async createMaintenanceRecord(recordData) {
    validateRequiredFields(recordData, [
      'vehicle_id',
      'maintenance_type',
      'description',
      'scheduled_date',
    ]);

    return withRetry(
      async () => {
        const response = await httpClient.post(
          API_ENDPOINTS.MAINTENANCE.RECORDS.CREATE,
          recordData
        );
        return handleApiResponse(response);
      },
      { maxRetries: 1 }
    ); // Don't retry create operations multiple times
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

export default maintenanceAPI;
