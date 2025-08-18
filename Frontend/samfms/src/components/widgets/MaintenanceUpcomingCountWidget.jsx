import React, { useState, useEffect } from 'react';
import { BaseWidget } from '../dashboard/BaseWidget';
import { maintenanceAPI } from '../../backend/api/maintenance';
import { registerWidget, WIDGET_TYPES, WIDGET_CATEGORIES } from '../../utils/widgetRegistry';
import { Calendar } from 'lucide-react';

const MaintenanceUpcomingCountWidget = ({ id, config = {} }) => {
  const [rawAnalyticsData, setRawAnalyticsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchAnalyticsData = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await maintenanceAPI.getMaintenanceAnalytics(
          config.vehicleId || null,
          config.startDate || null,
          config.endDate || null
        );

        let analyticsData = {};
        if (response?.data?.data?.analytics) {
          analyticsData = response.data.data.analytics;
        } else if (response?.data?.analytics) {
          analyticsData = response.data.analytics;
        } else if (response?.data) {
          analyticsData = response.data;
        }

        setRawAnalyticsData(analyticsData);
      } catch (err) {
        console.error('Failed to fetch maintenance analytics:', err);
        setError('Failed to load maintenance analytics data');
      } finally {
        setLoading(false);
      }
    };

    fetchAnalyticsData();

    const refreshInterval = (config.refreshInterval || 300) * 1000;
    const interval = setInterval(fetchAnalyticsData, refreshInterval);

    return () => clearInterval(interval);
  }, [config.refreshInterval, config.vehicleId, config.startDate, config.endDate]);

  const upcomingCount = rawAnalyticsData?.maintenance_summary?.upcoming_count || 0;

  return (
    <BaseWidget
      id={id}
      title={config.title || 'Upcoming Maintenance'}
      loading={loading}
      error={error}
      className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-950 dark:to-blue-900"
    >
      <div className="flex items-center justify-between h-full">
        <div className="flex-1">
          <div className="text-3xl font-bold text-blue-800 dark:text-blue-200 mb-1">
            {upcomingCount}
          </div>
          <div className="text-sm text-blue-600 dark:text-blue-400">
            {upcomingCount === 1 ? 'Task Scheduled' : 'Tasks Scheduled'}
          </div>
        </div>
        <div className="flex-shrink-0">
          <div className="w-12 h-12 bg-blue-200 dark:bg-blue-800 rounded-full flex items-center justify-center">
            <Calendar className="h-6 w-6 text-blue-600 dark:text-blue-300" />
          </div>
        </div>
      </div>
    </BaseWidget>
  );
};

registerWidget(WIDGET_TYPES.MAINTENANCE_UPCOMING_COUNT, MaintenanceUpcomingCountWidget, {
  title: 'Upcoming Maintenance Count',
  description: 'Count of upcoming scheduled maintenance tasks',
  category: WIDGET_CATEGORIES.MAINTENANCE,
  icon: Calendar,
  defaultConfig: {
    refreshInterval: 300,
    vehicleId: null,
    startDate: null,
    endDate: null,
  },
  configSchema: {
    refreshInterval: {
      type: 'number',
      label: 'Refresh Interval (seconds)',
      min: 60,
      max: 3600,
      default: 300,
    },
    vehicleId: {
      type: 'string',
      label: 'Vehicle ID (optional)',
      default: null,
    },
    startDate: {
      type: 'date',
      label: 'Start Date (optional)',
      default: null,
    },
    endDate: {
      type: 'date',
      label: 'End Date (optional)',
      default: null,
    },
  },
  defaultSize: { w: 3, h: 2 },
  minSize: { w: 2, h: 1 },
  maxSize: { w: 4, h: 3 },
});

export default MaintenanceUpcomingCountWidget;
