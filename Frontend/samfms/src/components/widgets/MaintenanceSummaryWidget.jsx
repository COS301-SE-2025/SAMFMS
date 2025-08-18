import React, { useState, useEffect } from 'react';
import { BaseWidget } from '../dashboard/BaseWidget';
import { maintenanceAPI } from '../../backend/api/maintenance';
import { registerWidget, WIDGET_TYPES, WIDGET_CATEGORIES } from '../../utils/widgetRegistry';
import { Dock, AlertTriangle, Calendar, DollarSign } from 'lucide-react';

const MaintenanceSummaryWidget = ({ id, config = {} }) => {
  const [data, setData] = useState({
    total_records: 0,
    overdue_count: 0,
    upcoming_count: 0,
    total_cost_this_month: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await maintenanceAPI.getMaintenanceDashboard();
        const dashboardData = response.data?.data || response.data || {};
        const analytics = dashboardData.analytics || {};

        const transformedData = {
          total_records: analytics.maintenance_summary?.total_records || 0,
          overdue_count: analytics.maintenance_summary?.overdue_count || 0,
          upcoming_count: analytics.maintenance_summary?.upcoming_count || 0,
          total_cost_this_month:
            analytics.performance_metrics?.total_cost_period ||
            analytics.cost_analysis?.total_cost ||
            0,
        };

        setData(transformedData);
      } catch (err) {
        console.error('Failed to fetch maintenance summary:', err);
        setError('Failed to load maintenance data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();

    // Set up refresh interval
    const refreshInterval = (config.refreshInterval || 30) * 1000;
    const interval = setInterval(fetchData, refreshInterval);

    return () => clearInterval(interval);
  }, [config.refreshInterval]);

  const summaryCards = [
    {
      title: 'Maintenance Records',
      value: data.total_records,
      icon: <Dock className="h-6 w-6 text-blue-600" />,
      color: 'bg-blue-100 dark:bg-blue-900',
      textColor: 'text-blue-800 dark:text-blue-200',
    },
    {
      title: 'Overdue',
      value: data.overdue_count,
      icon: <AlertTriangle className="h-6 w-6 text-red-600" />,
      color: 'bg-red-100 dark:bg-red-900',
      textColor: 'text-red-800 dark:text-red-200',
    },
    {
      title: 'Upcoming',
      value: data.upcoming_count,
      icon: <Calendar className="h-6 w-6 text-yellow-600" />,
      color: 'bg-yellow-100 dark:bg-yellow-900',
      textColor: 'text-yellow-800 dark:text-yellow-200',
    },
    {
      title: 'Spent this month',
      value: `R${data.total_cost_this_month?.toLocaleString() || 0}`,
      icon: <DollarSign className="h-6 w-6 text-green-600" />,
      color: 'bg-green-100 dark:bg-green-900',
      textColor: 'text-green-800 dark:text-green-200',
    },
  ];

  return (
    <BaseWidget
      id={id}
      title={config.title || 'Maintenance Summary'}
      config={config}
      loading={loading}
      error={error}
    >
      <div className="grid grid-cols-4 sm:grid-cols-4 gap-3 h-full">
        {summaryCards.map((card, index) => (
          <div key={index} className="flex items-center space-x-2 min-h-0">
            <div className={`p-2 rounded-lg ${card.color} flex-shrink-0`}>
              {card.icon}
              <div className="min-w-0 flex-1">
                <p className="text-xs text-muted-foreground truncate">{card.title}</p>
                <p className={`text-lg font-bold ${card.textColor} truncate`}>{card.value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </BaseWidget>
  );
};

// Register the widget
registerWidget(WIDGET_TYPES.MAINTENANCE_SUMMARY, MaintenanceSummaryWidget, {
  title: 'Maintenance Summary',
  description: 'Overview of maintenance records, overdue items, and costs',
  category: WIDGET_CATEGORIES.MAINTENANCE,
  defaultSize: { w: 3, h: 6 },
  minSize: { w: 3, h: 4 },
  maxSize: { w: 8, h: 8 },
  icon: Dock,
  configSchema: {
    title: { type: 'string', default: 'Maintenance Summary' },
    refreshInterval: { type: 'number', default: 30, min: 5 },
  },
});

export default MaintenanceSummaryWidget;
