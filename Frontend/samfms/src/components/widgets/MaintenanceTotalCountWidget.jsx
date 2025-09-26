import React, {useState, useEffect} from 'react';
import {BaseWidget} from '../dashboard/BaseWidget';
import {maintenanceAPI} from '../../backend/api/maintenance';
import {registerWidget, WIDGET_TYPES, WIDGET_CATEGORIES} from '../../utils/widgetRegistry';
import {ClipboardList} from 'lucide-react';

const MaintenanceTotalCountWidget = ({id, config = {}}) => {
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchMaintenanceData = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await maintenanceAPI.getMaintenanceDashboard();

        // Use the exact same data path as MaintenanceDashboard
        const dashboardData = response.data?.data || response.data || {};
        const analytics = dashboardData.analytics || {};
        const totalRecords = analytics.maintenance_summary?.total_records || 0;
        setTotalCount(totalRecords);

      } catch (err) {
        console.error('Failed to fetch maintenance dashboard data:', err);
        setError('Failed to load maintenance data');
        setTotalCount(0);
      } finally {
        setLoading(false);
      }
    };

    fetchMaintenanceData();

    const refreshInterval = (config.refreshInterval || 300) * 1000;
    const interval = setInterval(fetchMaintenanceData, refreshInterval);

    return () => clearInterval(interval);
  }, [config.refreshInterval]);

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
            {totalCount === 1 ? 'Total Record' : 'Total Records'}
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
  description: 'Total count of maintenance records',
  category: WIDGET_CATEGORIES.MAINTENANCE,
  icon: ClipboardList,
  defaultConfig: {
    refreshInterval: 300,
  },
  configSchema: {
    refreshInterval: {
      type: 'number',
      label: 'Refresh Interval (seconds)',
      min: 60,
      max: 3600,
      default: 300,
    },
  },
  defaultSize: {w: 3, h: 2},
  minSize: {w: 2, h: 1},
  maxSize: {w: 4, h: 3},
});

export default MaintenanceTotalCountWidget;
