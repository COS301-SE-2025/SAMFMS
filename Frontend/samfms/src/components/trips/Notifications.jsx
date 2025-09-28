import React, { useState, useEffect } from 'react';
import { Bell, Play, CheckCircle, AlertTriangle, MapPinOff } from 'lucide-react';
import { getNotifications, readNotification } from '../../backend/api/trips';

const Notifications = () => {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [unreadCount, setUnreadCount] = useState(0);
  const [total, setTotal] = useState(0);

  const fetchNotifications = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await getNotifications();
      
      // Access notifications from the nested structure
      const notificationsData = response.data?.data?.notifications || [];
      const unreadCount = response.data?.data?.unread_count || 0;
      const total = response.data?.data?.total || 0;
      
      // Sort by time descending
      const sortedNotifications = notificationsData.sort((a, b) => 
        new Date(b.time) - new Date(a.time)
      );
      
      setNotifications(sortedNotifications);
      setUnreadCount(unreadCount);
      setTotal(total);
    } catch (err) {
      setError('Failed to load notifications. Please try again.');
      console.error('Error fetching notifications:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, []);

  const handleMarkAsRead = async (notificationId) => {
    try {
      await readNotification(notificationId);
      // Update local state to reflect the change
      setNotifications(prev =>
        prev.map(notif =>
          notif.id === notificationId ? { ...notif, read: true } : notif
        )
      );
      // Update unread count
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (err) {
      console.error('Error marking notification as read:', err);
    }
  };

  const getIcon = (type) => {
    const normalizedType = type?.toUpperCase();
    switch (normalizedType) {
      case 'TRIP_STARTED':
        return <Play size={20} className="text-green-500 dark:text-green-400" />;
      case 'TRIP_COMPLETED':
        return <CheckCircle size={20} className="text-blue-500 dark:text-blue-400" />;
      case 'TRAFFIC_ALERT':
        return <AlertTriangle size={20} className="text-yellow-500 dark:text-yellow-400" />;
      case 'GEOFENCE_ALERT':
        return <MapPinOff size={20} className="text-red-500 dark:text-red-400" />;
      default:
        return <Bell size={20} className="text-gray-500 dark:text-gray-400" />;
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center p-8 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        <span className="ml-2">Loading notifications...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 dark:bg-red-900 border border-red-400 dark:border-red-600 text-red-700 dark:text-red-300 px-4 py-3 rounded">
        <p>{error}</p>
        <button
          onClick={fetchNotifications}
          className="mt-2 bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600 dark:bg-red-600 dark:hover:bg-red-700 transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md dark:shadow-gray-900/20">
      <div className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold flex items-center gap-2 text-gray-900 dark:text-gray-100">
            <Bell size={20} />
            Notifications
          </h2>
          <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
            <span>Total: {total}</span>
            {unreadCount > 0 && (
              <span className="bg-red-500 dark:bg-red-600 text-white px-2 py-1 rounded-full text-xs">
                {unreadCount} unread
              </span>
            )}
          </div>
        </div>
        
        {notifications.length === 0 ? (
          <p className="text-gray-600 dark:text-gray-400">No notifications available.</p>
        ) : (
          <div className="space-y-4">
            {notifications.map(notif => (
              <div
                key={notif.id}
                className={`border rounded-lg p-4 transition-colors ${
                  notif.read 
                    ? 'bg-gray-50 dark:bg-gray-700 text-gray-600 dark:text-gray-400 border-gray-200 dark:border-gray-600' 
                    : 'bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border-l-4 border-l-blue-500 dark:border-l-blue-400 border-gray-200 dark:border-gray-600'
                }`}
              >
                <div className="flex items-center gap-2 mb-2">
                  {getIcon(notif.type)}
                  <h3 className="font-semibold">{notif.title || 'Notification'}</h3>
                </div>
                <p className="mb-2">{notif.message || 'No message available.'}</p>
                
                {/* Additional info for trip-related notifications */}
                {(notif.trip_id || notif.driver_id) && (
                  <div className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                    {notif.trip_id && <span>Trip ID: {notif.trip_id}</span>}
                    {notif.trip_id && notif.driver_id && <span> • </span>}
                    {notif.driver_id && <span>Driver: {notif.driver_id}</span>}
                  </div>
                )}
                
                {/* {notif.data && (
                  <pre className="mt-2 p-2 bg-gray-100 rounded text-sm overflow-auto">
                    {JSON.stringify(notif.data, null, 2)}
                  </pre>
                )} */}
                
                <div className="flex items-center justify-between mt-3">
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {notif.time
                      ? new Date(notif.time).toLocaleString()
                      : 'Unknown time'}
                  </p>
                  {!notif.read && (
                    <button
                      onClick={() => handleMarkAsRead(notif.id)}
                      className="bg-blue-600 dark:bg-blue-700 text-white px-4 py-2 rounded-md hover:bg-blue-700 dark:hover:bg-blue-800 transition-colors text-sm"
                    >
                      Mark as Read
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Notifications;