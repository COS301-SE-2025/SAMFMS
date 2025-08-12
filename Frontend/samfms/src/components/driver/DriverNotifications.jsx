import React, { useState } from 'react';
import { Bell, AlertCircle, Info, CheckCircle, Clock, ChevronDown, ChevronUp } from 'lucide-react';

const DriverNotifications = () => {
  const [isCollapsed, setIsCollapsed] = useState(false);

  // Static notifications data for now
  const notifications = [
    {
      id: 1,
      type: 'urgent',
      title: 'Trip Assignment',
      message: 'New trip assigned for tomorrow 9:00 AM to Downtown',
      time: '2 minutes ago',
      read: false,
    },
    {
      id: 2,
      type: 'info',
      title: 'Vehicle Maintenance',
      message: 'Vehicle VH-001 is due for maintenance next week',
      time: '1 hour ago',
      read: false,
    },
    {
      id: 3,
      type: 'success',
      title: 'Trip Completed',
      message: 'Successfully completed trip to Airport Terminal',
      time: '3 hours ago',
      read: true,
    },
    {
      id: 4,
      type: 'warning',
      title: 'Traffic Alert',
      message: 'Heavy traffic reported on Route 45. Consider alternate routes.',
      time: '5 hours ago',
      read: true,
    },
    {
      id: 5,
      type: 'info',
      title: 'System Update',
      message: 'SAMFMS will undergo maintenance this weekend',
      time: '1 day ago',
      read: true,
    },
  ];

  const getNotificationIcon = type => {
    switch (type) {
      case 'urgent':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      case 'warning':
        return <Clock className="h-5 w-5 text-yellow-500" />;
      case 'success':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'info':
      default:
        return <Info className="h-5 w-5 text-blue-500" />;
    }
  };

  const getNotificationBgColor = (type, read) => {
    if (read) return 'bg-background';

    switch (type) {
      case 'urgent':
        return 'bg-red-50 border-red-200';
      case 'warning':
        return 'bg-yellow-50 border-yellow-200';
      case 'success':
        return 'bg-green-50 border-green-200';
      case 'info':
      default:
        return 'bg-blue-50 border-blue-200';
    }
  };

  const unreadCount = notifications.filter(n => !n.read).length;

  return (
    <div className="bg-card rounded-lg shadow-sm border border-border h-full">
      {/* Header */}
      <div className="p-3 sm:p-4 border-b border-border">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Bell className="h-5 w-5 text-foreground" />
            <h3 className="text-base sm:text-lg font-semibold text-foreground">Notifications</h3>
          </div>
          <div className="flex items-center space-x-2">
            {unreadCount > 0 && (
              <span className="bg-red-500 text-white text-xs rounded-full px-2 py-1 min-w-[20px] text-center">
                {unreadCount}
              </span>
            )}
            <button
              onClick={() => setIsCollapsed(!isCollapsed)}
              className="p-1 hover:bg-accent rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary focus:ring-opacity-50"
              aria-label={isCollapsed ? 'Expand notifications' : 'Collapse notifications'}
            >
              {isCollapsed ? (
                <ChevronDown className="h-5 w-5" />
              ) : (
                <ChevronUp className="h-5 w-5" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Notifications List - Collapsible */}
      {!isCollapsed && (
        <div className="max-h-[280px] sm:max-h-[400px] overflow-y-auto overscroll-contain">
          {notifications.length === 0 ? (
            <div className="p-6 text-center text-muted-foreground">
              <Bell className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p>No notifications</p>
            </div>
          ) : (
            <div className="divide-y divide-border">
              {notifications.map(notification => (
                <div
                  key={notification.id}
                  className={`py-3 px-3 sm:p-4 hover:bg-accent/50 transition-colors cursor-pointer ${getNotificationBgColor(
                    notification.type,
                    notification.read
                  )}`}
                >
                  <div className="flex items-start space-x-2 sm:space-x-3">
                    <div className="flex-shrink-0 mt-0.5 sm:mt-1">
                      {getNotificationIcon(notification.type)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-0.5 sm:mb-1">
                        <p
                          className={`text-xs sm:text-sm font-medium ${
                            notification.read ? 'text-muted-foreground' : 'text-foreground'
                          }`}
                        >
                          {notification.title}
                        </p>
                        {!notification.read && (
                          <div className="w-1.5 sm:w-2 h-1.5 sm:h-2 bg-primary rounded-full flex-shrink-0 ml-2"></div>
                        )}
                      </div>
                      <p
                        className={`text-xs sm:text-sm line-clamp-2 ${
                          notification.read ? 'text-muted-foreground' : 'text-foreground'
                        }`}
                      >
                        {notification.message}
                      </p>
                      <p className="text-[10px] sm:text-xs text-muted-foreground mt-0.5 sm:mt-1">
                        {notification.time}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Footer */}
      {!isCollapsed && notifications.length > 0 && (
        <div className="p-3 border-t border-border">
          <button className="w-full text-sm text-primary hover:text-primary/80 font-medium transition-colors">
            View All Notifications
          </button>
        </div>
      )}
    </div>
  );
};

export default DriverNotifications;
