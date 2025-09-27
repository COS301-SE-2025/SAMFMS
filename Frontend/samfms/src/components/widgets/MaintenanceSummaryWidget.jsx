import React, {useState, useEffect} from 'react';
import {BaseWidget} from '../dashboard/BaseWidget';
import {maintenanceAPI} from '../../backend/api/maintenance';
import {registerWidget, WIDGET_TYPES, WIDGET_CATEGORIES} from '../../utils/widgetRegistry';
import {Dock, AlertTriangle, Calendar, DollarSign} from 'lucide-react';

const MaintenanceSummaryWidget = ({id, config = {}}) => {
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

        // Fetch dashboard data for counts
        const response = await maintenanceAPI.getMaintenanceDashboard();
        // console.log('MaintenanceSummaryWidget - Full API Response:', response);

        const dashboardData = response.data?.data || response.data || {};
        const analytics = dashboardData.analytics || {};

        console.log('MaintenanceSummaryWidget - Analytics data:', analytics);

        // Use the pre-calculated cost values from backend analytics
        const costAnalysis = analytics.cost_analysis || {};
        const performanceMetrics = analytics.performance_metrics || {};

        // Use total_cost_period for the current period cost
        const periodTotalCost = performanceMetrics.total_cost_period || costAnalysis.total_cost || 0;

        const transformedData = {
          total_records: analytics.maintenance_summary?.total_records || 0,
          overdue_count: analytics.maintenance_summary?.overdue_count || 0,
          upcoming_count: analytics.maintenance_summary?.upcoming_count || 0,
          total_cost_this_month: periodTotalCost,
        };

        console.log('MaintenanceSummaryWidget - Transformed data using backend values:', transformedData);

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
      <div className="h-full w-full flex items-center justify-center">
        <div>Maintenance Summary</div>
        <div className="grid grid-cols-2 grid-rows-2 gap-4 w-full h-full p-4">
          {summaryCards.map((card, index) => (
            <div
              key={index}
              className={`flex flex-col items-center justify-center bg-white dark:bg-gray-900 rounded-lg shadow ${card.color} w-full h-full p-2 overflow-hidden`}
              style={{minWidth: 0, minHeight: 0}}
            >
              <p className="text-xs font-medium text-muted-foreground mb-0.5 text-center whitespace-normal truncate w-full">{card.title}</p>
              <p className={`text-base font-bold ${card.textColor} text-center break-words truncate w-full`}>{card.value}</p>
            </div>
          ))}
        </div>
      </div>
    </BaseWidget>
  );
};

// Register the widget
registerWidget(WIDGET_TYPES.MAINTENANCE_SUMMARY, MaintenanceSummaryWidget, {
  title: 'Maintenance Summary',
  description: 'Overview of maintenance records, overdue items, and costs',
  category: WIDGET_CATEGORIES.MAINTENANCE,
  defaultSize: {w: 3, h: 6},
  minSize: {w: 3, h: 4},
  maxSize: {w: 8, h: 8},
  icon: Dock,
  configSchema: {
    title: {type: 'string', default: 'Maintenance Summary'},
    refreshInterval: {type: 'number', default: 30, min: 5},
  },
});

export default MaintenanceSummaryWidget;
