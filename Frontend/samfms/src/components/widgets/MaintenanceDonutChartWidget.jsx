import React, { useState, useEffect } from 'react';
import { BaseWidget } from '../dashboard/BaseWidget';
import { maintenanceAPI } from '../../backend/api/maintenance';
import { registerWidget, WIDGET_TYPES, WIDGET_CATEGORIES } from '../../utils/widgetRegistry';
import Chart from 'react-apexcharts';
import { PieChart } from 'lucide-react';

const MaintenanceDonutChartWidget = ({ id, config = {} }) => {
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

  const renderChart = () => {
    const upcomingCount = rawAnalyticsData?.maintenance_summary?.upcoming_count || 0;
    const overdueCount = rawAnalyticsData?.maintenance_summary?.overdue_count || 0;
    const totalCount = upcomingCount + overdueCount;

    if (totalCount === 0) {
      return (
        <div className="flex items-center justify-center h-full text-gray-500">
          <div className="text-center">
            <PieChart className="mx-auto h-8 w-8 mb-2 opacity-50" />
            <p className="text-sm">No maintenance data</p>
          </div>
        </div>
      );
    }

    return (
      <div className="flex justify-center items-center h-full">
        <Chart
          options={{
            chart: {
              type: 'donut',
              toolbar: { show: false },
            },
            colors: ['#3B82F6', '#EF4444'],
            labels: ['Upcoming', 'Overdue'],
            legend: { show: false },
            dataLabels: {
              enabled: true,
              formatter: function (val) {
                return Math.round(val) + '%';
              },
              style: {
                fontSize: '12px',
                fontWeight: '600',
              },
            },
            plotOptions: {
              pie: {
                donut: {
                  size: '70%',
                  labels: {
                    show: true,
                    total: {
                      show: true,
                      label: 'Total',
                      fontSize: '12px',
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
          }}
          series={[upcomingCount, overdueCount]}
          type="donut"
          height="100%"
          width="100%"
        />
      </div>
    );
  };

  return (
    <BaseWidget
      id={id}
      title={config.title || 'Maintenance Status'}
      loading={loading}
      error={error}
    >
      {renderChart()}
    </BaseWidget>
  );
};

registerWidget(WIDGET_TYPES.MAINTENANCE_DONUT_CHART, MaintenanceDonutChartWidget, {
  title: 'Maintenance Donut Chart',
  description: 'Donut chart showing upcoming vs overdue maintenance',
  category: WIDGET_CATEGORIES.MAINTENANCE,
  icon: PieChart,
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
  defaultSize: { w: 4, h: 3 },
  minSize: { w: 3, h: 2 },
  maxSize: { w: 6, h: 4 },
});

export default MaintenanceDonutChartWidget;
