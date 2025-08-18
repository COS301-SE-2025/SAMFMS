import React, { createContext, useContext, useState, useCallback } from 'react';
import Notification from '../components/common/Notification';

const NotificationContext = createContext();

export const useNotification = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotification must be used within a NotificationProvider');
  }
  return context;
};

export const NotificationProvider = ({ children }) => {
  const [notifications, setNotifications] = useState([]);

  const addNotification = useCallback((message, type = 'info', options = {}) => {
    const id = Date.now() + Math.random();
    const notification = {
      id,
      message,
      type,
      isVisible: true,
      ...options,
    };

    setNotifications(prev => [...prev, notification]);

    return id;
  }, []);

  const removeNotification = useCallback(id => {
    setNotifications(prev => prev.filter(notification => notification.id !== id));
  }, []);

  const showSuccess = useCallback(
    (message, options = {}) => {
      return addNotification(message, 'success', options);
    },
    [addNotification]
  );

  const showError = useCallback(
    (message, options = {}) => {
      return addNotification(message, 'error', { autoClose: false, ...options });
    },
    [addNotification]
  );

  const showWarning = useCallback(
    (message, options = {}) => {
      return addNotification(message, 'warning', options);
    },
    [addNotification]
  );

  const showInfo = useCallback(
    (message, options = {}) => {
      return addNotification(message, 'info', options);
    },
    [addNotification]
  );
  const clearAll = useCallback(() => {
    setNotifications([]);
  }, []);

  // Generic showNotification function that routes to specific type functions
  const showNotification = useCallback(
    (message, type = 'info', options = {}) => {
      switch (type) {
        case 'success':
          return showSuccess(message, options);
        case 'error':
          return showError(message, options);
        case 'warning':
          return showWarning(message, options);
        case 'info':
        default:
          return showInfo(message, options);
      }
    },
    [showSuccess, showError, showWarning, showInfo]
  );

  const value = {
    notifications,
    addNotification,
    removeNotification,
    showSuccess,
    showError,
    showWarning,
    showInfo,
    showNotification,
    clearAll,
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}

      {/* Render notifications */}
      <div className="fixed bottom-4 left-4 z-50 space-y-2">
        {notifications.map((notification, index) => (
          <div
            key={notification.id}
            style={{
              transform: `translateY(-${index * 10}px)`,
              zIndex: 50 - index,
            }}
          >
            <Notification
              message={notification.message}
              type={notification.type}
              isVisible={notification.isVisible}
              onClose={() => removeNotification(notification.id)}
              duration={notification.duration}
              autoClose={notification.autoClose}
            />
          </div>
        ))}
      </div>
    </NotificationContext.Provider>
  );
};

export default NotificationProvider;
