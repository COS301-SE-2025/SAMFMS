import React from 'react';
import { BaseWidget } from '../dashboard/BaseWidget';
import { registerWidget, WIDGET_TYPES, WIDGET_CATEGORIES } from '../../utils/widgetRegistry';
import { BarChart3, TrendingUp, TrendingDown } from 'lucide-react';

const StatsCardWidget = ({ id, config = {} }) => {
  // This is a configurable stats card that can display any metric
  const {
    primaryValue = '0',
    primaryLabel = 'Total',
    secondaryValue,
    secondaryLabel,
    trend,
    trendLabel,
    showTrend = false,
    valueColor = 'text-blue-600',
    size = 'large', // small, medium, large
  } = config;

  const getSizeClasses = () => {
    switch (size) {
      case 'small':
        return 'text-lg';
      case 'medium':
        return 'text-xl';
      case 'large':
      default:
        return 'text-2xl';
    }
  };

  const getTrendIcon = () => {
    if (!showTrend || trend === undefined) return null;

    const trendValue = parseFloat(trend);
    if (trendValue > 0) {
      return <TrendingUp className="h-4 w-4 text-green-600" />;
    } else if (trendValue < 0) {
      return <TrendingDown className="h-4 w-4 text-red-600" />;
    }
    return null;
  };

  const getTrendColor = () => {
    if (!showTrend || trend === undefined) return '';

    const trendValue = parseFloat(trend);
    if (trendValue > 0) {
      return 'text-green-600';
    } else if (trendValue < 0) {
      return 'text-red-600';
    }
    return 'text-gray-600';
  };

  return (
    <BaseWidget id={id} title={config.title || 'Statistics'} config={config}>
      <div className="h-full flex flex-col justify-center space-y-3">
        {/* Primary Metric */}
        <div className="text-center">
          <p className="text-xs font-medium text-muted-foreground truncate">{primaryLabel}</p>
          <p className={`${getSizeClasses()} font-bold ${valueColor} truncate`}>{primaryValue}</p>
        </div>

        {/* Secondary Metric */}
        {secondaryValue && (
          <div className="text-center border-t border-border pt-2">
            <p className="text-xs text-muted-foreground truncate">{secondaryLabel}</p>
            <p className="text-sm font-semibold truncate">{secondaryValue}</p>
          </div>
        )}

        {/* Trend */}
        {showTrend && trend !== undefined && (
          <div className="flex items-center justify-center gap-2 pt-1">
            {getTrendIcon()}
            <span className={`text-xs font-medium ${getTrendColor()} truncate`}>
              {Math.abs(parseFloat(trend)).toFixed(1)}% {trendLabel || 'vs last period'}
            </span>
          </div>
        )}
      </div>
    </BaseWidget>
  );
};

// Register the widget
registerWidget(WIDGET_TYPES.STATS_CARD, StatsCardWidget, {
  title: 'Statistics Card',
  description: 'Customizable card for displaying key metrics and statistics',
  category: WIDGET_CATEGORIES.GENERAL,
  defaultSize: { w: 2, h: 2 },
  minSize: { w: 1, h: 1 },
  maxSize: { w: 3, h: 3 },
  icon: <BarChart3 size={20} />,
  configSchema: {
    title: { type: 'string', default: 'Statistics' },
    primaryValue: { type: 'string', default: '0' },
    primaryLabel: { type: 'string', default: 'Total' },
    secondaryValue: { type: 'string', default: '' },
    secondaryLabel: { type: 'string', default: '' },
    trend: { type: 'number', default: 0 },
    trendLabel: { type: 'string', default: 'vs last period' },
    showTrend: { type: 'boolean', default: false },
    valueColor: {
      type: 'select',
      default: 'text-blue-600',
      options: [
        { value: 'text-blue-600', label: 'Blue' },
        { value: 'text-green-600', label: 'Green' },
        { value: 'text-red-600', label: 'Red' },
        { value: 'text-yellow-600', label: 'Yellow' },
        { value: 'text-purple-600', label: 'Purple' },
      ],
    },
    size: {
      type: 'select',
      default: 'large',
      options: [
        { value: 'small', label: 'Small' },
        { value: 'medium', label: 'Medium' },
        { value: 'large', label: 'Large' },
      ],
    },
  },
});

export default StatsCardWidget;
