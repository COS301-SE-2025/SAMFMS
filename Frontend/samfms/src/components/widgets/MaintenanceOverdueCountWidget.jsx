import React, { useState, useEffect } from 'react';
import { BaseWidget } from '../dashboard/BaseWidget';
import { maintenanceAPI } from '../../backend/api/maintenance';
import { registerWidget, WIDGET_TYPES, WIDGET_CATEGORIES } from '../../utils/widgetRegistry';
import { AlertTriangle } from 'lucide-react';

const MaintenanceOverdueCountWidget = ({ id, config = {} }) => {
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

  const overdueCount = rawAnalyticsData?.maintenance_summary?.overdue_count || 0;

  return (
    <BaseWidget
      id={id}
      title={config.title || 'Overdue Maintenance'}
      loading={loading}
      error={error}
      className="bg-gradient-to-br from-red-50 to-red-100 dark:from-red-950 dark:to-red-900"
    >
      <div className="flex items-center justify-between h-full">
        <div className="flex-1">
          <div className="text-3xl font-bold text-red-800 dark:text-red-200 mb-1">
            {overdueCount}
          </div>
          <div className="text-sm text-red-600 dark:text-red-400">
            {overdueCount === 1 ? 'Task Overdue' : 'Tasks Overdue'}
          </div>
          {overdueCount > 0 && (
            <div className="text-xs text-red-500 dark:text-red-400 mt-1">
              Requires immediate attention
            </div>
          )}
        </div>
        <div className="flex-shrink-0">
          <div className="w-12 h-12 bg-red-200 dark:bg-red-800 rounded-full flex items-center justify-center">
            <AlertTriangle className="h-6 w-6 text-red-600 dark:text-red-300" />
          </div>
        </div>
      </div>
    </BaseWidget>
  );
};

registerWidget(WIDGET_TYPES.MAINTENANCE_OVERDUE_COUNT, MaintenanceOverdueCountWidget, {
  title: 'Overdue Maintenance Count',
  description: 'Count of overdue maintenance tasks requiring attention',
  category: WIDGET_CATEGORIES.MAINTENANCE,
  icon: AlertTriangle,
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

export default MaintenanceOverdueCountWidget;
