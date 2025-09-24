import React, { useState, useEffect } from 'react';
import { Bell, Play, CheckCircle, AlertTriangle, MapPinOff } from 'lucide-react';
import { getNotifications, readNotification } from '../../backend/api/trips';

const Notifications = () => {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchNotifications = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await getNotifications();
      // Assuming the API returns response.data as an array of notifications
      // Sort by sent_at descending
      const sortedNotifications = (response.data || []).sort((a, b) => 
        new Date(b.sent_at) - new Date(a.sent_at)
      );
      setNotifications(sortedNotifications);
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
          notif.id === notificationId ? { ...notif, is_read: true } : notif
        )
      );
    } catch (err) {
      console.error('Error marking notification as read:', err);
    }
  };

  const getIcon = (type) => {
    switch (type) {
      case 'TRIP_STARTED':
        return <Play size={20} className="text-green-500" />;
      case 'TRIP_COMPLETED':
        return <CheckCircle size={20} className="text-blue-500" />;
      case 'TRAFFIC_ALERT':
        return <AlertTriangle size={20} className="text-yellow-500" />;
      case 'GEOFENCE_ALERT':
        return <MapPinOff size={20} className="text-red-500" />;
      default:
        return <Bell size={20} className="text-gray-500" />;
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        <span className="ml-2">Loading notifications...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
        <p>{error}</p>
        <button
          onClick={fetchNotifications}
          className="mt-2 bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6">
        <h2 className="text-xl font-bold mb-4 flex items-center gap-2 text-foreground">
          <Bell size={20} />
          Notifications
        </h2>
        {notifications.length === 0 ? (
          <p className="text-muted-foreground">No notifications available.</p>
        ) : (
          <div className="space-y-4">
            {notifications.map(notif => (
              <div
                key={notif.id}
                className={`border rounded-lg p-4 ${notif.is_read ? 'bg-gray-50 text-muted-foreground' : 'bg-white text-foreground'}`}
              >
                <div className="flex items-center gap-2 mb-2">
                  {getIcon(notif.type)}
                  <h3 className="font-semibold">{notif.title || 'Notification'}</h3>
                </div>
                <p>{notif.message || 'No message available.'}</p>
                {notif.data && (
                  <pre className="mt-2 p-2 bg-gray-100 rounded text-sm overflow-auto">
                    {JSON.stringify(notif.data, null, 2)}
                  </pre>
                )}
                <p className="text-sm mt-2">
                  {notif.sent_at
                    ? new Date(notif.sent_at).toLocaleString()
                    : 'Unknown time'}
                </p>
                {!notif.is_read && (
                  <button
                    onClick={() => handleMarkAsRead(notif.id)}
                    className="mt-3 bg-primary text-white px-4 py-2 rounded-md hover:bg-primary/90 transition"
                  >
                    Mark as Read
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Notifications;