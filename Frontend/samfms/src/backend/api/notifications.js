/**
 * API functions for notification maexport const sendNotification = async (notificationData) => {
  return httpClient.post(NOTIFICATIONS_BASE_URL, notificationData);
};
 */

import {httpClient} from '../services/httpClient';
import {API_CONFIG} from '../../config/apiConfig';

const NOTIFICATIONS_BASE_URL = `${API_CONFIG.baseURL}/trips/notifications`;

/**
 * Get notifications for the current user
 * @param {Object} params - Query parameters
 * @param {boolean} params.unread_only - Get only unread notifications
 * @param {number} params.limit - Number of notifications to retrieve
 * @param {number} params.skip - Number of notifications to skip
 * @returns {Promise<Object>} Notifications response
 */
export const getNotifications = async (params = {}) => {
  const queryParams = new URLSearchParams({
    unread_only: params.unread_only || false,
    limit: params.limit || 50,
    skip: params.skip || 0,
  }).toString();

  return httpClient.get(`${NOTIFICATIONS_BASE_URL}?${queryParams}`);
};

/**
 * Send a notification to specified users (admin/fleet_manager only)
 * @param {Object} notificationData - Notification data
 * @param {string[]} notificationData.user_ids - Array of user IDs
 * @param {string} notificationData.type - Notification type
 * @param {string} notificationData.title - Notification title
 * @param {string} notificationData.message - Notification message
 * @param {string} notificationData.trip_id - Related trip ID (optional)
 * @param {string} notificationData.driver_id - Related driver ID (optional)
 * @param {Object} notificationData.data - Additional data (optional)
 * @param {string[]} notificationData.channels - Notification channels (optional)
 * @param {string} notificationData.scheduled_for - Schedule for later (optional)
 * @returns {Promise<Object>} Send notification response
 */
export const sendNotification = async notificationData => {
  return httpClient.post(NOTIFICATIONS_BASE_URL, notificationData);
};

/**
 * Mark a notification as read
 * @param {string} notificationId - Notification ID
 * @returns {Promise<Object>} Mark read response
 */
export const markNotificationRead = async notificationId => {
  return httpClient.put(`${NOTIFICATIONS_BASE_URL}/${notificationId}/read`);
};

/**
 * Get count of unread notifications for the current user
 * @returns {Promise<Object>} Unread count response
 */
export const getUnreadNotificationCount = async () => {
  return httpClient.get(`${NOTIFICATIONS_BASE_URL}/unread/count`);
};

/**
 * Get notification preferences for the current user
 * @returns {Promise<Object>} Notification preferences response
 */
export const getNotificationPreferences = async () => {
  return httpClient.get(`${NOTIFICATIONS_BASE_URL}/preferences`);
};

/**
 * Update notification preferences for the current user
 * @param {Object} preferencesData - Preference data
 * @param {boolean} preferencesData.email_enabled - Enable email notifications
 * @param {boolean} preferencesData.push_enabled - Enable push notifications
 * @param {boolean} preferencesData.sms_enabled - Enable SMS notifications
 * @param {Object} preferencesData.quiet_hours - Quiet hours configuration
 * @param {Object} preferencesData.notification_types - Notification type preferences
 * @returns {Promise<Object>} Update preferences response
 */
export const updateNotificationPreferences = async preferencesData => {
  return httpClient.put(`${NOTIFICATIONS_BASE_URL}/preferences`, preferencesData);
};

/**
 * Get driver-specific notifications (combines with trip data)
 * @returns {Promise<Object>} Driver notifications response
 */
export const getDriverNotifications = async () => {
  try {
    // Get regular notifications
    const response = await getNotifications({limit: 20});

    // Handle nested response structure from trip planning service
    // The response structure is: response.data.data.notifications (double nested)
    const notificationsData =
      response?.data?.data?.notifications || response?.data?.notifications || [];

    // Convert backend notification format to frontend format
    if (notificationsData && Array.isArray(notificationsData)) {
      const notifications = notificationsData.map(notification => {
        // Map notification types to frontend types
        let type = 'info';
        if (notification.type?.includes('URGENT') || notification.type?.includes('ALERT')) {
          type = 'urgent';
        } else if (notification.type?.includes('WARNING')) {
          type = 'warning';
        } else if (
          notification.type?.includes('SUCCESS') ||
          notification.type?.includes('COMPLETED')
        ) {
          type = 'success';
        }

        return {
          id: notification.id,
          type,
          title: notification.title,
          message: notification.message,
          time: notification.time || 'Just now',
          read: notification.read || false,
          trip_id: notification.trip_id,
          driver_id: notification.driver_id,
          data: notification.data,
        };
      });

      // Return with consistent structure
      return {
        data: {
          notifications,
          total: response?.data?.data?.total || notifications.length,
          unread_count:
            response?.data?.data?.unread_count || notifications.filter(n => !n.read).length,
        },
      };
    }

    // Return empty notifications if no data
    return {
      data: {
        notifications: [],
        total: 0,
        unread_count: 0,
      },
    };
  } catch (error) {
    console.error('Error fetching driver notifications:', error);
    throw error;
  }
};

export const getUserNotifications = async () => {
  try {
    const response = await httpClient.get(`${NOTIFICATIONS_BASE_URL}/my-notifications`);
    return response;
  } catch (error) {
    console.error('Error fetching user notifications:', error);
    throw error;
  }
};

const notificationsApi = {
  getNotifications,
  sendNotification,
  markNotificationRead,
  getUnreadNotificationCount,
  getNotificationPreferences,
  updateNotificationPreferences,
  getDriverNotifications,
};

export default notificationsApi;
