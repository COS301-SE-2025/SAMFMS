import React, { useState, useEffect } from 'react';
import { BaseWidget } from '../dashboard/BaseWidget';
import { maintenanceAPI } from '../../backend/api/maintenance';
import { registerWidget, WIDGET_TYPES, WIDGET_CATEGORIES } from '../../utils/widgetRegistry';
import { Wrench } from 'lucide-react';

const MaintenanceRecordsWidget = ({ id, config = {} }) => {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchRecords = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await maintenanceAPI.getMaintenanceDashboard();
        const dashboardData = response.data?.data || response.data || {};

        setRecords(dashboardData.recent_records || []);
      } catch (err) {
        console.error('Failed to fetch maintenance records:', err);
        setError('Failed to load maintenance records');
      } finally {
        setLoading(false);
      }
    };

    fetchRecords();

    // Set up refresh interval
    const refreshInterval = (config.refreshInterval || 60) * 1000;
    const interval = setInterval(fetchRecords, refreshInterval);

    return () => clearInterval(interval);
  }, [config.refreshInterval]);

  const getStatusColor = status => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'in_progress':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      case 'scheduled':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    }
  };

  return (
    <BaseWidget
      id={id}
      title={config.title || 'Recent Maintenance Records'}
      config={config}
      loading={loading}
      error={error}
    >
      {records && records.length > 0 ? (
        <div className="space-y-2 h-full overflow-y-auto">
          {records.slice(0, config.maxRecords || 5).map(record => (
            <div
              key={record.id}
              className="flex items-center justify-between p-2 border border-border rounded-lg hover:bg-accent/5 transition-colors"
            >
              <div className="flex-1 min-w-0">
                <p className="font-medium text-xs truncate">{record.maintenance_type}</p>
                <p className="text-xs text-muted-foreground truncate">
                  Vehicle: {record.vehicle_id} •{' '}
                  {new Date(record.date_performed).toLocaleDateString()}
                </p>
              </div>
              <div className="text-right flex-shrink-0 ml-2">
                <p className="font-medium text-xs">R{record.cost?.toLocaleString() || 0}</p>
                <span
                  className={`px-1 py-0.5 rounded-full text-xs ${getStatusColor(record.status)}`}
                >
                  {record.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-8">
          <Wrench className="h-12 w-12 text-muted-foreground mx-auto mb-2" />
          <p className="text-muted-foreground">No recent maintenance records</p>
        </div>
      )}
    </BaseWidget>
  );
};

// Register the widget
registerWidget(WIDGET_TYPES.MAINTENANCE_RECORDS, MaintenanceRecordsWidget, {
  title: 'Recent Maintenance Records',
  description: 'Shows the most recent maintenance activities across your fleet',
  category: WIDGET_CATEGORIES.MAINTENANCE,
  defaultSize: { w: 4, h: 3 },
  minSize: { w: 3, h: 2 },
  maxSize: { w: 6, h: 4 },
  icon: <Wrench size={20} />,
  configSchema: {
    title: { type: 'string', default: 'Recent Maintenance Records' },
    refreshInterval: { type: 'number', default: 60, min: 10 },
    maxRecords: { type: 'number', default: 5, min: 3, max: 10 },
  },
});

export default MaintenanceRecordsWidget;
