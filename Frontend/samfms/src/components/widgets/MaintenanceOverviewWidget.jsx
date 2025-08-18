import React, { useState, useEffect } from 'react';
import { BaseWidget } from '../dashboard/BaseWidget';
import { maintenanceAPI } from '../../backend/api/maintenance';
import { registerWidget, WIDGET_TYPES, WIDGET_CATEGORIES } from '../../utils/widgetRegistry';
import Chart from 'react-apexcharts';
import { PieChart } from 'lucide-react';

const MaintenanceOverviewWidget = ({ id, config = {} }) => {
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

        // Extract the data from the double-nested ResponseBuilder format
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

    // Set up refresh interval
    const refreshInterval = (config.refreshInterval || 300) * 1000; // Default 5 minutes
    const interval = setInterval(fetchAnalyticsData, refreshInterval);

    return () => clearInterval(interval);
  }, [config.refreshInterval, config.vehicleId, config.startDate, config.endDate]);

  const renderChart = () => {
    const upcomingCount = rawAnalyticsData?.maintenance_summary?.upcoming_count || 0;
    const overdueCount = rawAnalyticsData?.maintenance_summary?.overdue_count || 0;
    const totalCount = upcomingCount + overdueCount;

    if (totalCount === 0) {
      return (
        <div className="flex items-center justify-center h-64 text-gray-500">
          <div className="text-center">
            <PieChart className="mx-auto h-12 w-12 mb-2 opacity-50" />
            <p>No maintenance data available</p>
          </div>
        </div>
      );
    }

    return (
      <div className="flex flex-col items-center">
        {/* Apex Donut Chart */}
        <div className="w-64 h-64 mb-4">
          <Chart
            options={{
              chart: {
                type: 'donut',
                height: 256,
                width: 256,
                toolbar: {
                  show: false,
                },
              },
              colors: ['#3B82F6', '#EF4444'], // Blue for upcoming, Red for overdue
              labels: ['Upcoming', 'Overdue'],
              legend: {
                show: false, // We'll create custom legend below
              },
              dataLabels: {
                enabled: true,
                formatter: function (val) {
                  return Math.round(val) + '%';
                },
                style: {
                  fontSize: '14px',
                  fontWeight: '600',
                },
              },
              plotOptions: {
                pie: {
                  donut: {
                    size: '60%',
                    labels: {
                      show: true,
                      total: {
                        show: true,
                        label: 'Total Scheduled',
                        fontSize: '14px',
                        fontWeight: '500',
                        color: '#6B7280',
                        formatter: function () {
                          return totalCount.toString();
                        },
                      },
                    },
                  },
                },
              },
              responsive: [
                {
                  breakpoint: 480,
                  options: {
                    chart: {
                      width: 200,
                      height: 200,
                    },
                  },
                },
              ],
            }}
            series={[upcomingCount, overdueCount]}
            type="donut"
            height={256}
            width={256}
          />
        </div>

        {/* Legend and Statistics */}
        <div className="w-full grid grid-cols-1 md:grid-cols-2 gap-4 text-center">
          <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
            <div className="flex items-center justify-center mb-1">
              <div className="w-3 h-3 bg-blue-500 rounded-full mr-2"></div>
              <div className="text-sm text-blue-600 dark:text-blue-400">Upcoming</div>
            </div>
            <div className="text-xl font-bold text-blue-800 dark:text-blue-200">
              {upcomingCount}
            </div>
          </div>

          <div className="p-3 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
            <div className="flex items-center justify-center mb-1">
              <div className="w-3 h-3 bg-red-500 rounded-full mr-2"></div>
              <div className="text-sm text-red-600 dark:text-red-400">Overdue</div>
            </div>
            <div className="text-xl font-bold text-red-800 dark:text-red-200">{overdueCount}</div>
          </div>
        </div>

        {/* Total Maintenance Scheduled */}
        <div className="mt-4 text-center">
          <div className="text-sm text-gray-600 dark:text-gray-400">
            Total Maintenance Scheduled
          </div>
          <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">{totalCount}</div>
        </div>

        {/* Completion Rate */}
        {totalCount > 0 && (
          <div className="mt-2 text-center">
            <div className="text-sm text-gray-600 dark:text-gray-400">On-time Performance</div>
            <div
              className={`text-lg font-semibold ${
                overdueCount === 0
                  ? 'text-green-600 dark:text-green-400'
                  : overdueCount > upcomingCount
                  ? 'text-red-600 dark:text-red-400'
                  : 'text-yellow-600 dark:text-yellow-400'
              }`}
            >
              {Math.round((upcomingCount / totalCount) * 100)}%
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <BaseWidget
      id={id}
      title={config.title || 'Maintenance Overview'}
      loading={loading}
      error={error}
      className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900"
    >
      {renderChart()}
    </BaseWidget>
  );
};

// Register the widget
registerWidget(WIDGET_TYPES.MAINTENANCE_OVERVIEW, MaintenanceOverviewWidget, {
  title: 'Maintenance Overview',
  description: 'Donut chart showing upcoming vs overdue maintenance',
  category: WIDGET_CATEGORIES.MAINTENANCE,
  icon: PieChart,
  defaultConfig: {
    refreshInterval: 300, // 5 minutes
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
  defaultSize: { w: 6, h: 4 },
  minSize: { w: 4, h: 3 },
  maxSize: { w: 8, h: 6 },
});

export default MaintenanceOverviewWidget;
