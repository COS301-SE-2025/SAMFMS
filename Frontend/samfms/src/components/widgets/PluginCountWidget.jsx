import React, { useState, useEffect } from 'react';
import { BaseWidget } from '../dashboard/BaseWidget';
import { getAllPlugins } from '../../backend/api/plugins';
import { registerWidget, WIDGET_TYPES, WIDGET_CATEGORIES } from '../../utils/widgetRegistry';
import { Package, TrendingUp } from 'lucide-react';

const PluginCountWidget = ({ id, config = {} }) => {
  const [pluginStats, setPluginStats] = useState({
    total: 0,
    active: 0,
    inactive: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchPluginCount = async () => {
      try {
        setLoading(true);
        setError(null);

        const pluginsData = await getAllPlugins();

        const stats = {
          total: pluginsData.length,
          active: pluginsData.filter(p => p.status === 'ACTIVE').length,
          inactive: pluginsData.filter(p => p.status !== 'ACTIVE').length,
        };

        setPluginStats(stats);
      } catch (err) {
        console.error('Failed to fetch plugin count:', err);
        setError('Failed to load plugin data');
      } finally {
        setLoading(false);
      }
    };

    fetchPluginCount();

    // Set up refresh interval
    const refreshInterval = (config.refreshInterval || 60) * 1000; // Default 1 minute
    const interval = setInterval(fetchPluginCount, refreshInterval);

    return () => clearInterval(interval);
  }, [config.refreshInterval]);

  const activePercentage =
    pluginStats.total > 0 ? Math.round((pluginStats.active / pluginStats.total) * 100) : 0;

  return (
    <BaseWidget
      id={id}
      title={config.title || 'Plugin Overview'}
      config={config}
      loading={loading}
      error={error}
    >
      <div className="space-y-4 h-full flex flex-col justify-center">
        {/* Main Count Display */}
        <div className="text-center">
          <div className="flex items-center justify-center mb-3">
            <div className="bg-primary/10 rounded-full p-3">
              <Package className="h-8 w-8 text-primary" />
            </div>
          </div>
          <div className="space-y-1">
            <p className="text-3xl font-bold text-foreground">{pluginStats.total}</p>
            <p className="text-sm text-muted-foreground">Total Plugins</p>
          </div>
        </div>

        {/* Status Breakdown */}
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-3 text-center border border-green-200 dark:border-green-800">
            <div className="flex items-center justify-center gap-1 mb-1">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <p className="text-xs font-medium text-green-700 dark:text-green-300">Active</p>
            </div>
            <p className="text-lg font-bold text-green-700 dark:text-green-300">
              {pluginStats.active}
            </p>
          </div>

          <div className="bg-gray-50 dark:bg-gray-900/20 rounded-lg p-3 text-center border border-gray-200 dark:border-gray-800">
            <div className="flex items-center justify-center gap-1 mb-1">
              <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
              <p className="text-xs font-medium text-gray-700 dark:text-gray-300">Inactive</p>
            </div>
            <p className="text-lg font-bold text-gray-700 dark:text-gray-300">
              {pluginStats.inactive}
            </p>
          </div>
        </div>

        {/* Health Indicator */}
        <div className="bg-muted/30 rounded-lg p-3 text-center">
          <div className="flex items-center justify-center gap-2 mb-1">
            <TrendingUp className="h-4 w-4 text-primary" />
            <p className="text-xs font-medium text-muted-foreground">Health Score</p>
          </div>
          <p
            className={`text-lg font-bold ${
              activePercentage >= 80
                ? 'text-green-600 dark:text-green-400'
                : activePercentage >= 50
                ? 'text-yellow-600 dark:text-yellow-400'
                : 'text-red-600 dark:text-red-400'
            }`}
          >
            {activePercentage}%
          </p>
        </div>
      </div>
    </BaseWidget>
  );
};

// Register the widget
registerWidget(WIDGET_TYPES.PLUGIN_COUNT, PluginCountWidget, {
  title: 'Plugin Overview',
  description: 'Quick overview of plugin count and status distribution',
  category: WIDGET_CATEGORIES.PLUGINS,
  defaultSize: { w: 2, h: 3 },
  minSize: { w: 2, h: 2 },
  maxSize: { w: 3, h: 4 },
  icon: <Package size={20} />,
  configSchema: {
    title: { type: 'string', default: 'Plugin Overview' },
    refreshInterval: { type: 'number', default: 60, min: 30 },
  },
});

export default PluginCountWidget;
