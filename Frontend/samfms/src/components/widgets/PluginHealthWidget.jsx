import React, { useState, useEffect } from 'react';
import { BaseWidget } from '../dashboard/BaseWidget';
import { getPluginsWithStatus } from '../../backend/api/plugins';
import { registerWidget, WIDGET_TYPES, WIDGET_CATEGORIES } from '../../utils/widgetRegistry';
import { Activity, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';

const PluginHealthWidget = ({ id, config = {} }) => {
  const [pluginData, setPluginData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchPluginHealth = async () => {
      try {
        setLoading(true);
        setError(null);

        const data = await getPluginsWithStatus();

        // Support either the flattened array (preferred) or a raw `{ sblocks: { ... } }` shape
        let items = [];
        if (Array.isArray(data)) {
          items = data;
        } else if (data && typeof data === 'object' && data.sblocks) {
          items = Object.entries(data.sblocks).map(([plugin, value]) => {
            const status = value?.data?.status ?? value?.status ?? 'unknown';
            return { plugin, status };
          });
        }

        setPluginData(items);
      } catch (err) {
        console.error('Failed to fetch plugin health:', err);
        setError('Failed to load plugin health data');
      } finally {
        setLoading(false);
      }
    };

    fetchPluginHealth();

    // Set up refresh interval
    const refreshInterval = (config.refreshInterval || 30) * 1000; // Default 30 seconds
    const interval = setInterval(fetchPluginHealth, refreshInterval);

    return () => clearInterval(interval);
  }, [config.refreshInterval]);

  const getStatusIcon = status => {
    const statusLower = status?.toLowerCase();
    if (statusLower === 'healthy' || statusLower === 'success' || statusLower === 'ok') {
      return <CheckCircle className="h-4 w-4 text-green-500" />;
    }
    if (statusLower === 'unhealthy' || statusLower === 'error' || statusLower === 'down') {
      return <XCircle className="h-4 w-4 text-red-500" />;
    }
    return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
  };

  const getStatusColor = status => {
    const statusLower = status?.toLowerCase();
    if (statusLower === 'healthy' || statusLower === 'success' || statusLower === 'ok') {
      return 'text-green-600 dark:text-green-400';
    }
    if (statusLower === 'unhealthy' || statusLower === 'error' || statusLower === 'down') {
      return 'text-red-600 dark:text-red-400';
    }
    return 'text-yellow-600 dark:text-yellow-400';
  };

  return (
    <BaseWidget
      id={id}
      title={config.title || 'Plugin Health'}
      config={config}
      loading={loading}
      error={error}
    >
      <div className="space-y-2 max-h-64 overflow-y-auto">
        {pluginData.length === 0 ? (
          <div className="text-center py-6">
            <Activity className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
            <p className="text-sm text-muted-foreground">No plugin data available</p>
          </div>
        ) : (
          pluginData.map(({ plugin, status }) => (
            <div
              key={plugin}
              className="flex items-center justify-between p-3 bg-muted/30 rounded-lg hover:bg-muted/50 transition-colors duration-150"
            >
              <div className="flex items-center gap-3">
                {getStatusIcon(status)}
                <div>
                  <p className="font-medium text-sm capitalize">{plugin}</p>
                  <p className="text-xs text-muted-foreground">Plugin Service</p>
                </div>
              </div>
              <div className="text-right">
                <span
                  className={`text-xs font-medium px-2 py-1 rounded-full ${
                    status?.toLowerCase() === 'healthy'
                      ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300'
                      : status?.toLowerCase() === 'unhealthy' || status?.toLowerCase() === 'error'
                      ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300'
                      : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300'
                  }`}
                >
                  {status}
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </BaseWidget>
  );
};

// Register the widget
registerWidget(WIDGET_TYPES.PLUGIN_HEALTH, PluginHealthWidget, {
  title: 'Plugin Health',
  description: 'Monitor the health status of all system plugins',
  category: WIDGET_CATEGORIES.PLUGINS,
  defaultSize: { w: 3, h: 3 },
  minSize: { w: 2, h: 2 },
  maxSize: { w: 4, h: 4 },
  icon: <Activity size={20} />,
  configSchema: {
    title: { type: 'string', default: 'Plugin Health' },
    refreshInterval: { type: 'number', default: 30, min: 10 },
  },
});

export default PluginHealthWidget;
