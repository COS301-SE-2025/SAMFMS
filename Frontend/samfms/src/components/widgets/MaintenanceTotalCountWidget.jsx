import React, { useState, useEffect } from 'react';
import { BaseWidget } from '../dashboard/BaseWidget';
import { maintenanceAPI } from '../../backend/api/maintenance';
import { registerWidget, WIDGET_TYPES, WIDGET_CATEGORIES } from '../../utils/widgetRegistry';
import { ClipboardList } from 'lucide-react';

const MaintenanceTotalCountWidget = ({ id, config = {} }) => {
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
  const overdueCount = rawAnalyticsData?.maintenance_summary?.overdue_count || 0;
  const totalCount = upcomingCount + overdueCount;
  const onTimePercentage = totalCount > 0 ? Math.round((upcomingCount / totalCount) * 100) : 100;

  return (
    <BaseWidget
      id={id}
      title={config.title || 'Total Maintenance'}
      loading={loading}
      error={error}
      className="bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-950 dark:to-gray-900"
    >
      <div className="flex items-center justify-between h-full">
        <div className="flex-1">
          <div className="text-3xl font-bold text-gray-800 dark:text-gray-200 mb-1">
            {totalCount}
          </div>
          <div className="text-sm text-gray-600 dark:text-gray-400">
            {totalCount === 1 ? 'Total Task' : 'Total Tasks'}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            {onTimePercentage}% on-time performance
          </div>
        </div>
        <div className="flex-shrink-0">
          <div className="w-12 h-12 bg-gray-200 dark:bg-gray-800 rounded-full flex items-center justify-center">
            <ClipboardList className="h-6 w-6 text-gray-600 dark:text-gray-300" />
          </div>
        </div>
      </div>
    </BaseWidget>
  );
};

registerWidget(WIDGET_TYPES.MAINTENANCE_TOTAL_COUNT, MaintenanceTotalCountWidget, {
  title: 'Total Maintenance Count',
  description: 'Total count of scheduled maintenance tasks with performance metrics',
  category: WIDGET_CATEGORIES.MAINTENANCE,
  icon: ClipboardList,
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

export default MaintenanceTotalCountWidget;
