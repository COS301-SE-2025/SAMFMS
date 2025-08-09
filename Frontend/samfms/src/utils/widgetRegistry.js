// Widget Types
export const WIDGET_TYPES = {
  // Maintenance Widgets (similar to maintenance page components)
  MAINTENANCE_SUMMARY: 'maintenance_summary',
  MAINTENANCE_RECORDS: 'maintenance_records',
  MAINTENANCE_ALERTS: 'maintenance_alerts',
  MAINTENANCE_COST_ANALYTICS: 'maintenance_cost_analytics',

  // Vehicle Widgets
  VEHICLE_STATUS: 'vehicle_status',
  VEHICLE_ANALYTICS: 'vehicle_analytics',

  // Plugin Widgets
  PLUGIN_HEALTH: 'plugin_health',
  PLUGIN_COUNT: 'plugin_count',

  // General Stats
  STATS_CARD: 'stats_card',
  METRIC_CARD: 'metric_card',

  // Charts
  LINE_CHART: 'line_chart',
  BAR_CHART: 'bar_chart',
  PIE_CHART: 'pie_chart',
};

export const WIDGET_CATEGORIES = {
  MAINTENANCE: 'Maintenance',
  VEHICLES: 'Vehicles',
  PLUGINS: 'Plugins',
  ANALYTICS: 'Analytics',
  CHARTS: 'Charts',
  GENERAL: 'General',
};

export const widgetRegistry = new Map();

export const registerWidget = (type, component, metadata) => {
  widgetRegistry.set(type, {
    component,
    metadata: {
      title: '',
      description: '',
      category: WIDGET_CATEGORIES.GENERAL,
      defaultSize: { w: 2, h: 2 },
      minSize: { w: 1, h: 1 },
      maxSize: { w: 12, h: 6 },
      configSchema: {},
      icon: null,
      ...metadata,
    },
  });
};

export const getWidget = type => widgetRegistry.get(type);
export const getAllWidgets = () => Array.from(widgetRegistry.entries());

// Helper function to generate unique widget IDs
export const generateWidgetId = () => {
  return `widget_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};
