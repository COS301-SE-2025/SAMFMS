import React, { useState, useEffect } from 'react';
import { BaseWidget } from '../dashboard/BaseWidget';
import { maintenanceAPI } from '../../backend/api/maintenance';
import { registerWidget, WIDGET_TYPES, WIDGET_CATEGORIES } from '../../utils/widgetRegistry';
import { Bell, AlertCircle } from 'lucide-react';

const MaintenanceAlertsWidget = ({ id, config = {} }) => {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchNotifications = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await maintenanceAPI.getMaintenanceNotifications(1, config.maxAlerts || 5);
        const notificationsData = response.data?.data || response.data || {};
        const notifications = notificationsData.notifications || notificationsData || [];

        setNotifications(notifications);
      } catch (err) {
        console.error('Failed to fetch maintenance notifications:', err);
        setError('Failed to load maintenance alerts');
      } finally {
        setLoading(false);
      }
    };

    fetchNotifications();

    // Set up refresh interval
    const refreshInterval = (config.refreshInterval || 30) * 1000;
    const interval = setInterval(fetchNotifications, refreshInterval);

    return () => clearInterval(interval);
  }, [config.refreshInterval, config.maxAlerts]);

  const markNotificationAsRead = async notificationId => {
    try {
      await maintenanceAPI.markNotificationAsRead(notificationId);
      setNotifications(prev =>
        prev.map(notif => (notif.id === notificationId ? { ...notif, is_read: true } : notif))
      );
    } catch (err) {
      console.error('Error marking notification as read:', err);
    }
  };

  const getPriorityColor = priority => {
    switch (priority) {
      case 'high':
        return 'border-red-500 bg-red-50 dark:bg-red-950/20';
      case 'medium':
        return 'border-yellow-500 bg-yellow-50 dark:bg-yellow-950/20';
      case 'low':
        return 'border-blue-500 bg-blue-50 dark:bg-blue-950/20';
      default:
        return 'border-gray-500 bg-gray-50 dark:bg-gray-950/20';
    }
  };

  const getPriorityIcon = priority => {
    switch (priority) {
      case 'high':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      case 'medium':
        return <AlertCircle className="h-4 w-4 text-yellow-500" />;
      default:
        return <Bell className="h-4 w-4 text-blue-500" />;
    }
  };

  return (
    <BaseWidget
      id={id}
      title={config.title || 'Maintenance Alerts'}
      config={config}
      loading={loading}
      error={error}
    >
      {notifications.length > 0 ? (
        <div className="space-y-2 h-full overflow-y-auto">
          {notifications.map(notification => (
            <div
              key={notification.id}
              className={`p-2 rounded-lg border-l-4 cursor-pointer transition ${getPriorityColor(
                notification.priority
              )} ${notification.is_read ? 'opacity-60' : ''}`}
              onClick={() => !notification.is_read && markNotificationAsRead(notification.id)}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2 flex-1 min-w-0">
                  {getPriorityIcon(notification.priority)}
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-xs truncate">{notification.title}</p>
                    <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                      {notification.message}
                    </p>
                  </div>
                </div>
                {!notification.is_read && (
                  <div className="w-2 h-2 bg-primary rounded-full flex-shrink-0"></div>
                )}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                {new Date(notification.created_at).toLocaleDateString()}
              </p>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-4 h-full flex items-center justify-center">
          <Bell className="h-12 w-12 text-muted-foreground mx-auto mb-2" />
          <p className="text-muted-foreground">No maintenance alerts</p>
        </div>
      )}
    </BaseWidget>
  );
};

// Register the widget
registerWidget(WIDGET_TYPES.MAINTENANCE_ALERTS, MaintenanceAlertsWidget, {
  title: 'Maintenance Alerts',
  description: 'Important maintenance notifications and alerts',
  category: WIDGET_CATEGORIES.MAINTENANCE,
  defaultSize: { w: 3, h: 3 },
  minSize: { w: 2, h: 2 },
  maxSize: { w: 4, h: 4 },
  icon: <Bell size={20} />,
  configSchema: {
    title: { type: 'string', default: 'Maintenance Alerts' },
    refreshInterval: { type: 'number', default: 30, min: 10 },
    maxAlerts: { type: 'number', default: 5, min: 3, max: 10 },
  },
});

export default MaintenanceAlertsWidget;
