import React, { useState, useEffect } from 'react';
import { maintenanceAPI } from '../../backend/api/maintenance';

const MaintenanceDashboard = ({ vehicles }) => {
  const [dashboardData, setDashboardData] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const [dashboardResponse, notificationsResponse] = await Promise.all([
        maintenanceAPI.getMaintenanceDashboard(),
        maintenanceAPI.getMaintenanceNotifications(1, 10),
      ]);

      // Handle nested data structure from backend
      const dashboardData = dashboardResponse.data?.data || dashboardResponse.data || {};
      const analytics = dashboardData.analytics || {};

      // Transform analytics data to match component expectations
      const transformedData = {
        total_records: analytics.maintenance_summary?.total_records || 0,
        overdue_count: analytics.maintenance_summary?.overdue_count || 0,
        upcoming_count: analytics.maintenance_summary?.upcoming_count || 0,
        total_cost_this_month:
          analytics.performance_metrics?.total_cost_period ||
          analytics.cost_analysis?.total_cost ||
          0,
        recent_records: dashboardData.recent_records || [],
        completion_rate:
          analytics.maintenance_summary?.completion_rate ||
          analytics.performance_metrics?.on_time_completion ||
          0,
        average_cost:
          analytics.performance_metrics?.average_cost_per_maintenance ||
          analytics.cost_analysis?.average_cost ||
          0,
      };

      setDashboardData(transformedData);

      // Handle notifications data
      const notificationsData =
        notificationsResponse.data?.data || notificationsResponse.data || {};
      const notifications = notificationsData.notifications || notificationsData || [];
      setNotifications(notifications);
    } catch (err) {
      console.error('Error loading dashboard data:', err);
      setError('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

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

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        <span className="ml-3">Loading dashboard...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
        <h3 className="text-red-800 dark:text-red-200 font-semibold">Error</h3>
        <p className="text-red-600 dark:text-red-400 mt-2">{error}</p>
      </div>
    );
  }

  const defaultData = {
    total_records: 0,
    overdue_count: 0,
    upcoming_count: 0,
    total_cost_this_month: 0,
    recent_records: [],
  };

  const data = dashboardData || defaultData;

return (
  <div className="space-y-6">
    {/* Summary Cards */}
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
    <div className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 rounded-lg shadow-md p-6">
  <div className="flex items-center justify-between">
    <div>
      <p className="text-sm font-medium text-muted-foreground">Total Records</p>
      <p className="text-2xl font-bold">{data.total_records}</p>
    </div>
    {/* Icon container */}
    <div className="flex items-center justify-center w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900">
  <svg
    className="w-5 h-5 text-blue-500"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.5"
    viewBox="0 0 24 24"
  >
    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
  </svg>
</div>
  </div>
</div>


        <div className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Overdue</p>
              <p className="text-2xl font-bold text-red-600">{data.overdue_count}</p>
            </div>
            <div className="text-red-500">
              <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
                  clipRule="evenodd"
                ></path>
              </svg>
            </div>
          </div>
        </div>

        <div className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Upcoming (30 days)</p>
              <p className="text-2xl font-bold text-yellow-600">{data.upcoming_count}</p>
            </div>
            <div className="text-yellow-500">
              <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z"
                  clipRule="evenodd"
                ></path>
              </svg>
            </div>
          </div>
        </div>

        <div className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">This Month Cost</p>
              <p className="text-2xl font-bold text-green-600">
                R{data.total_cost_this_month?.toLocaleString() || 0}
              </p>
            </div>
            <div className="text-green-500">
              <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
                <path d="M8.433 7.418c.155-.103.346-.196.567-.267v1.698a2.305 2.305 0 01-.567-.267C8.07 8.34 8 8.114 8 8c0-.114.07-.34.433-.582zM11 12.849v-1.698c.22.071.412.164.567.267.364.243.433.468.433.582 0 .114-.07.34-.433.582a2.305 2.305 0 01-.567.267z"></path>
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-13a1 1 0 10-2 0v.092a4.535 4.535 0 00-1.676.662C6.602 6.234 6 7.009 6 8c0 .99.602 1.765 1.324 2.246.48.32 1.054.545 1.676.662v1.941c-.391-.127-.68-.317-.843-.504a1 1 0 10-1.51 1.31c.562.649 1.413 1.076 2.353 1.253V15a1 1 0 102 0v-.092a4.535 4.535 0 001.676-.662C13.398 13.766 14 12.991 14 12c0-.99-.602-1.765-1.324-2.246A4.535 4.535 0 0011 9.092V7.151c.391.127.68.317.843.504a1 1 0 101.51-1.31c-.562-.649-1.413-1.076-2.353-1.253V5z"
                  clipRule="evenodd"
                ></path>
              </svg>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Maintenance Records */}
        <div className="lg:col-span-2 bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold mb-4">Recent Maintenance Records</h3>
          {data.recent_records && data.recent_records.length > 0 ? (
            <div className="space-y-3">
              {data.recent_records.map(record => (
                <div
                  key={record.id}
                  className="flex items-center justify-between p-3 border border-border rounded-lg"
                >
                  <div>
                    <p className="font-medium">{record.maintenance_type}</p>
                    <p className="text-sm text-muted-foreground">
                      Vehicle: {record.vehicle_id} •{' '}
                      {new Date(record.date_performed).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="font-medium">R{record.cost?.toLocaleString() || 0}</p>
                    <span
                      className={`px-2 py-1 rounded-full text-xs ${
                        record.status === 'completed'
                          ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                          : record.status === 'in_progress'
                          ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                          : 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200'
                      }`}
                    >
                      {record.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground text-center py-8">No recent maintenance records</p>
          )}
        </div>

        {/* Notifications/Alerts */}
        <div className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold mb-4">Alerts & Notifications</h3>
          {notifications.length > 0 ? (
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {notifications.map(notification => (
                <div
                  key={notification.id}
                  className={`p-3 rounded-lg border-l-4 cursor-pointer transition ${
                    notification.priority === 'high'
                      ? 'border-red-500 bg-red-50 dark:bg-red-950/20'
                      : notification.priority === 'medium'
                      ? 'border-yellow-500 bg-yellow-50 dark:bg-yellow-950/20'
                      : 'border-blue-500 bg-blue-50 dark:bg-blue-950/20'
                  } ${notification.is_read ? 'opacity-60' : ''}`}
                  onClick={() => !notification.is_read && markNotificationAsRead(notification.id)}
                >
                  <p className="font-medium text-sm">{notification.title}</p>
                  <p className="text-xs text-muted-foreground mt-1">{notification.message}</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {new Date(notification.created_at).toLocaleDateString()}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground text-center py-8">No notifications</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default MaintenanceDashboard;
