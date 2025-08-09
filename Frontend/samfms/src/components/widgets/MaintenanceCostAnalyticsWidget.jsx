import React, { useState, useEffect } from 'react';
import { BaseWidget } from '../dashboard/BaseWidget';
import { maintenanceAPI } from '../../backend/api/maintenance';
import { registerWidget, WIDGET_TYPES, WIDGET_CATEGORIES } from '../../utils/widgetRegistry';
import { BarChart3, TrendingUp, TrendingDown } from 'lucide-react';

const MaintenanceCostAnalyticsWidget = ({ id, config = {} }) => {
  const [costData, setCostData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchCostAnalytics = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await maintenanceAPI.getCostAnalytics(
          config.period || 'monthly',
          null // vehicle filter
        );

        const costData = response.data?.data || response.data || {};
        setCostData(costData.cost_analytics || costData.analytics || costData);
      } catch (err) {
        console.error('Failed to fetch cost analytics:', err);
        setError('Failed to load cost analytics');
      } finally {
        setLoading(false);
      }
    };

    fetchCostAnalytics();

    // Set up refresh interval
    const refreshInterval = (config.refreshInterval || 120) * 1000; // Default 2 minutes
    const interval = setInterval(fetchCostAnalytics, refreshInterval);

    return () => clearInterval(interval);
  }, [config.refreshInterval, config.period]);

  const formatCurrency = amount => {
    return `R${(amount || 0).toLocaleString()}`;
  };

  const calculateTrend = () => {
    if (!costData || !costData.total_cost || !costData.previous_period_cost) {
      return { trend: 0, isPositive: true };
    }

    const current = costData.total_cost;
    const previous = costData.previous_period_cost;
    const trend = ((current - previous) / previous) * 100;

    return {
      trend: Math.abs(trend).toFixed(1),
      isPositive: trend >= 0,
    };
  };

  const trendData = calculateTrend();

  const analyticsCards = [
    {
      title: 'Total Cost',
      value: formatCurrency(costData?.total_cost),
      subtitle: `${config.period || 'Monthly'} total`,
      color: 'text-blue-600',
    },
    {
      title: 'Average Cost',
      value: formatCurrency(costData?.average_cost),
      subtitle: 'Per maintenance',
      color: 'text-green-600',
    },
    {
      title: 'Trend',
      value: `${trendData.trend}%`,
      subtitle: trendData.isPositive ? 'Increase' : 'Decrease',
      color: trendData.isPositive ? 'text-red-600' : 'text-green-600',
      icon: trendData.isPositive ? <TrendingUp size={16} /> : <TrendingDown size={16} />,
    },
  ];

  return (
    <BaseWidget
      id={id}
      title={config.title || 'Maintenance Cost Analytics'}
      config={config}
      loading={loading}
      error={error}
    >
      <div className="space-y-3">
        {/* Cost Overview Cards */}
        <div className="grid grid-cols-3 gap-2">
          {analyticsCards.map((card, index) => (
            <div key={index} className="bg-background p-2 rounded-md border border-border">
              <div className="text-center">
                <div className="flex items-center justify-center mb-1">
                  {card.icon && <div className={`${card.color} mr-1`}>{card.icon}</div>}
                  <p className="text-xs text-muted-foreground truncate">{card.title}</p>
                </div>
                <p className={`text-sm font-bold ${card.color} truncate`}>{card.value}</p>
                <p className="text-xs text-muted-foreground truncate">{card.subtitle}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Cost Breakdown */}
        {costData?.cost_breakdown && (
          <div className="bg-background p-2 rounded-md border border-border">
            <h4 className="font-medium mb-2 text-xs">Cost Breakdown</h4>
            <div className="space-y-1">
              {Object.entries(costData.cost_breakdown).map(([category, amount]) => (
                <div key={category} className="flex justify-between text-xs">
                  <span className="capitalize text-muted-foreground truncate">
                    {category.replace('_', ' ')}
                  </span>
                  <span className="font-medium">{formatCurrency(amount)}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </BaseWidget>
  );
};

// Register the widget
registerWidget(WIDGET_TYPES.MAINTENANCE_COST_ANALYTICS, MaintenanceCostAnalyticsWidget, {
  title: 'Maintenance Cost Analytics',
  description: 'Detailed breakdown of maintenance costs and trends',
  category: WIDGET_CATEGORIES.MAINTENANCE,
  defaultSize: { w: 3, h: 3 },
  minSize: { w: 3, h: 2 },
  maxSize: { w: 4, h: 4 },
  icon: <BarChart3 size={20} />,
  configSchema: {
    title: { type: 'string', default: 'Maintenance Cost Analytics' },
    refreshInterval: { type: 'number', default: 120, min: 60 },
    period: {
      type: 'select',
      default: 'monthly',
      options: [
        { value: 'weekly', label: 'Weekly' },
        { value: 'monthly', label: 'Monthly' },
        { value: 'quarterly', label: 'Quarterly' },
      ],
    },
  },
});

export default MaintenanceCostAnalyticsWidget;
