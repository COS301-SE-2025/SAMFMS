// src/backend/api/maintenance.js
import API from '../API';

export const maintenanceAPI = {
  // Maintenance Records
  async getMaintenanceRecords(vehicleId = null, status = null, page = 1, size = 20) {
    const params = new URLSearchParams();
    if (vehicleId) params.append('vehicle_id', vehicleId);
    if (status) params.append('status', status);
    params.append('page', page);
    params.append('size', size);
    
    const response = await API.get(`/maintenance/records?${params}`);
    return response.data;
  },

  async createMaintenanceRecord(recordData) {
    const response = await API.post('/maintenance/records', recordData);
    return response.data;
  },

  async updateMaintenanceRecord(recordId, recordData) {
    const response = await API.put(`/maintenance/records/${recordId}`, recordData);
    return response.data;
  },

  async deleteMaintenanceRecord(recordId) {
    const response = await API.delete(`/maintenance/records/${recordId}`);
    return response.data;
  },

  async getMaintenanceRecord(recordId) {
    const response = await API.get(`/maintenance/records/${recordId}`);
    return response.data;
  },

  async getVehicleMaintenanceHistory(vehicleId) {
    const response = await API.get(`/maintenance/records/vehicle/${vehicleId}`);
    return response.data;
  },

  async getOverdueMaintenanceRecords() {
    const response = await API.get('/maintenance/records/overdue');
    return response.data;
  },

  // Maintenance Schedules
  async getMaintenanceSchedules(vehicleId = null) {
    const params = vehicleId ? `?vehicle_id=${vehicleId}` : '';
    const response = await API.get(`/maintenance/schedules${params}`);
    return response.data;
  },

  async createMaintenanceSchedule(scheduleData) {
    const response = await API.post('/maintenance/schedules', scheduleData);
    return response.data;
  },

  async updateMaintenanceSchedule(scheduleId, scheduleData) {
    const response = await API.put(`/maintenance/schedules/${scheduleId}`, scheduleData);
    return response.data;
  },

  async deleteMaintenanceSchedule(scheduleId) {
    const response = await API.delete(`/maintenance/schedules/${scheduleId}`);
    return response.data;
  },

  // License Records
  async getLicenseRecords(vehicleId = null, licenseType = null) {
    const params = new URLSearchParams();
    if (vehicleId) params.append('vehicle_id', vehicleId);
    if (licenseType) params.append('license_type', licenseType);
    
    const response = await API.get(`/maintenance/licenses?${params}`);
    return response.data;
  },

  async createLicenseRecord(licenseData) {
    const response = await API.post('/maintenance/licenses', licenseData);
    return response.data;
  },

  async updateLicenseRecord(licenseId, licenseData) {
    const response = await API.put(`/maintenance/licenses/${licenseId}`, licenseData);
    return response.data;
  },

  async deleteLicenseRecord(licenseId) {
    const response = await API.delete(`/maintenance/licenses/${licenseId}`);
    return response.data;
  },

  async getExpiringLicenses(days = 30) {
    const response = await API.get(`/maintenance/licenses/expiring?days=${days}`);
    return response.data;
  },

  // Maintenance Vendors
  async getMaintenanceVendors() {
    const response = await API.get('/maintenance/vendors');
    return response.data;
  },

  async createMaintenanceVendor(vendorData) {
    const response = await API.post('/maintenance/vendors', vendorData);
    return response.data;
  },

  async updateMaintenanceVendor(vendorId, vendorData) {
    const response = await API.put(`/maintenance/vendors/${vendorId}`, vendorData);
    return response.data;
  },

  async deleteMaintenanceVendor(vendorId) {
    const response = await API.delete(`/maintenance/vendors/${vendorId}`);
    return response.data;
  },

  // Analytics
  async getMaintenanceAnalytics(vehicleId = null, startDate = null, endDate = null) {
    const params = new URLSearchParams();
    if (vehicleId) params.append('vehicle_id', vehicleId);
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    
    const response = await API.get(`/maintenance/analytics?${params}`);
    return response.data;
  },

  async getCostAnalytics(period = 'monthly', vehicleId = null) {
    const params = new URLSearchParams();
    params.append('period', period);
    if (vehicleId) params.append('vehicle_id', vehicleId);
    
    const response = await API.get(`/maintenance/analytics/costs?${params}`);
    return response.data;
  },

  async getMaintenanceDashboard() {
    const response = await API.get('/maintenance/analytics/dashboard');
    return response.data;
  },

  // Notifications
  async getMaintenanceNotifications(page = 1, size = 20) {
    const response = await API.get(`/maintenance/notifications?page=${page}&size=${size}`);
    return response.data;
  },

  async markNotificationAsRead(notificationId) {
    const response = await API.put(`/maintenance/notifications/${notificationId}/read`);
    return response.data;
  },

  async deleteNotification(notificationId) {
    const response = await API.delete(`/maintenance/notifications/${notificationId}`);
    return response.data;
  }
};

export default maintenanceAPI;
