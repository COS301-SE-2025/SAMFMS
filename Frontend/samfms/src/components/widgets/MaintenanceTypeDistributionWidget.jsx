import React, { useState, useEffect } from 'react';
import { BaseWidget } from '../dashboard/BaseWidget';
import { maintenanceAPI } from '../../backend/api/maintenance';
import { registerWidget, WIDGET_TYPES, WIDGET_CATEGORIES } from '../../utils/widgetRegistry';
import Chart from 'react-apexcharts';
import { BarChart3 } from 'lucide-react';

const MaintenanceTypeDistributionWidget = ({ id, config = {} }) => {
  const [analyticsData, setAnalyticsData] = useState(null);
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

        setAnalyticsData(analyticsData);
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

  const formatCurrency = amount => {
    return `R${(amount || 0).toLocaleString('en-ZA', { minimumFractionDigits: 2 })}`;
  };

  const renderChart = () => {
    if (!analyticsData?.maintenance_types || analyticsData.maintenance_types.length === 0) {
      return (
        <div className="flex items-center justify-center h-64 text-gray-500">
          <div className="text-center">
            <BarChart3 className="mx-auto h-12 w-12 mb-2 opacity-50" />
            <p>No maintenance type data available</p>
          </div>
        </div>
      );
    }

    // Prepare data for ApexCharts
    const sortedTypes = analyticsData.maintenance_types
      .sort((a, b) => (b.total_cost || 0) - (a.total_cost || 0))
      .slice(0, 10); // Show top 10 types to avoid overcrowding

    const categories = sortedTypes.map(
      type =>
        type.maintenance_type?.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) ||
        'Unknown'
    );
    const costs = sortedTypes.map(type => type.total_cost || 0);

    const chartOptions = {
      chart: {
        type: 'bar',
        height: 350,
        toolbar: {
          show: true,
          tools: {
            download: true,
            selection: false,
            zoom: false,
            zoomin: false,
            zoomout: false,
            pan: false,
            reset: false,
          },
        },
        background: 'transparent',
      },
      plotOptions: {
        bar: {
          horizontal: true,
          distributed: true,
          barHeight: '70%',
          dataLabels: {
            position: 'center',
          },
        },
      },
      dataLabels: {
        enabled: true,
        textAnchor: 'middle',
        distributed: false,
        offsetX: 0,
        offsetY: 0,
        style: {
          fontSize: '12px',
          fontWeight: 'bold',
          colors: ['#fff'],
        },
        formatter: function (val) {
          return formatCurrency(val);
        },
      },
      colors: sortedTypes.map((_, index) => `hsl(${(index * 360) / sortedTypes.length}, 70%, 50%)`),
      xaxis: {
        categories: categories,
        labels: {
          formatter: function (val) {
            return formatCurrency(val);
          },
          style: {
            colors: '#64748b',
            fontSize: '12px',
          },
        },
      },
      yaxis: {
        labels: {
          style: {
            colors: '#64748b',
            fontSize: '11px',
          },
          maxWidth: 120,
        },
      },
      grid: {
        show: true,
        borderColor: '#e2e8f0',
        strokeDashArray: 3,
        position: 'back',
        xaxis: {
          lines: {
            show: true,
          },
        },
        yaxis: {
          lines: {
            show: false,
          },
        },
      },
      tooltip: {
        enabled: true,
        theme: 'dark',
        y: {
          formatter: function (val) {
            return formatCurrency(val);
          },
        },
      },
      legend: {
        show: false,
      },
      responsive: [
        {
          breakpoint: 640,
          options: {
            chart: {
              height: 300,
            },
            plotOptions: {
              bar: {
                barHeight: '60%',
              },
            },
            yaxis: {
              labels: {
                maxWidth: 80,
              },
            },
          },
        },
      ],
    };

    const series = [
      {
        name: 'Cost',
        data: costs,
      },
    ];

    return (
      <div>
        <Chart options={chartOptions} series={series} type="bar" height={350} />

        {/* Total summary */}
        <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
              Total Cost Across All Types:
            </span>
            <span className="text-lg font-bold text-gray-900 dark:text-gray-100">
              {formatCurrency(
                analyticsData.maintenance_types.reduce(
                  (sum, type) => sum + (type.total_cost || 0),
                  0
                )
              )}
            </span>
          </div>
        </div>
      </div>
    );
  };

  return (
    <BaseWidget
      id={id}
      title={config.title || 'Maintenance Type Distribution'}
      loading={loading}
      error={error}
      className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900"
    >
      {renderChart()}
    </BaseWidget>
  );
};

// Register the widget
registerWidget(WIDGET_TYPES.MAINTENANCE_TYPE_DISTRIBUTION, MaintenanceTypeDistributionWidget, {
  title: 'Maintenance Type Distribution',
  description: 'Bar chart showing maintenance costs by type',
  category: WIDGET_CATEGORIES.MAINTENANCE,
  icon: BarChart3,
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
  defaultSize: { w: 8, h: 6 },
  minSize: { w: 4, h: 4 },
  maxSize: { w: 12, h: 8 },
});
export default MaintenanceTypeDistributionWidget;
