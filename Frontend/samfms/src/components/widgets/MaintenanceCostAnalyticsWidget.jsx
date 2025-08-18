import React, { useState, useEffect, useLayoutEffect, useRef } from 'react';
import { BaseWidget } from '../dashboard/BaseWidget';
import { maintenanceAPI } from '../../backend/api/maintenance';
import { registerWidget, WIDGET_TYPES, WIDGET_CATEGORIES } from '../../utils/widgetRegistry';
import { BarChart3, TrendingUp, TrendingDown } from 'lucide-react';

const MaintenanceCostAnalyticsWidget = ({ id, config = {} }) => {
  const [costData, setCostData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const cardsContainerRef = useRef(null);
  const cardRefs = useRef([]);
  const [cardHeight, setCardHeight] = useState(null);

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

  // Ensure all three cards have equal height based on the tallest content
  useLayoutEffect(() => {
    const measure = () => {
      const heights = (cardRefs.current || []).filter(Boolean).map(el => el.scrollHeight || 0);
      const max = heights.length ? Math.max(...heights) : null;
      setCardHeight(max);
    };

    // Measure on mount/update
    measure();

    // Re-measure on container resize
    let ro;
    if (window.ResizeObserver) {
      ro = new ResizeObserver(() => measure());
      if (cardsContainerRef.current) ro.observe(cardsContainerRef.current);
    }

    // Re-measure on window resize (fallback)
    window.addEventListener('resize', measure);

    return () => {
      window.removeEventListener('resize', measure);
      if (ro) ro.disconnect();
    };
  }, [costData]);

  return (
    <BaseWidget
      id={id}
      title={config.title || 'Maintenance Cost Analytics'}
      config={config}
      loading={loading}
      error={error}
    >
      {/* Make the widget content scroll vertically only when necessary */}
      <div className="h-full flex flex-col px-2 pt-1 pb-2">
        {/* Cards area: evenly distributed with flex spacing */}
        <div ref={cardsContainerRef} className="flex-1 flex flex-col justify-evenly gap-2">
          {analyticsCards.map((card, index) => (
            <div
              key={index}
              ref={el => (cardRefs.current[index] = el)}
              className="bg-background p-2 rounded-md border border-border flex-1"
              style={
                cardHeight ? { minHeight: `${Math.max(cardHeight, 60)}px` } : { minHeight: '60px' }
              }
            >
              <div className="flex items-center justify-between h-full">
                <div className="flex items-center gap-2 flex-1 min-w-0">
                  {card.icon && <div className={`${card.color} flex-shrink-0`}>{card.icon}</div>}
                  <div className="min-w-0">
                    <p className="text-sm text-muted-foreground font-medium truncate">
                      {card.title}
                    </p>
                    <p className="text-xs text-muted-foreground truncate">{card.subtitle}</p>
                  </div>
                </div>
                <div className="text-right flex-shrink-0 ml-3">
                  <p className={`text-lg font-bold ${card.color}`}>{card.value}</p>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Cost Breakdown - only show if there's space */}
        {costData?.cost_breakdown && (
          <div className="bg-background p-2 rounded-md border border-border mt-2 flex-shrink-0">
            <h4 className="font-semibold mb-2 text-xs">Breakdown</h4>
            <div className="space-y-1 max-h-18 overflow-y-auto">
              {Object.entries(costData.cost_breakdown)
                .slice(0, 3)
                .map(([category, amount]) => (
                  <div key={category} className="flex justify-between items-center py-0.5">
                    <span className="capitalize text-muted-foreground text-xs flex-1 mr-2 truncate">
                      {category.replace(/_/g, ' ')}
                    </span>
                    <span className="font-medium text-xs text-right flex-shrink-0">
                      {formatCurrency(amount)}
                    </span>
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
  defaultSize: { w: 3, h: 6 },
  minSize: { w: 3, h: 3 },
  maxSize: { w: 12, h: 8 },
  icon: BarChart3,
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
