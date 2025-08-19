// Widget Types - Using secure constants to prevent injection
export const WIDGET_TYPES = Object.freeze({
  // Maintenance Widgets (similar to maintenance page components)
  MAINTENANCE_SUMMARY: 'maintenance_summary',
  MAINTENANCE_RECORDS: 'maintenance_records',
  MAINTENANCE_ALERTS: 'maintenance_alerts',
  MAINTENANCE_COST_ANALYTICS: 'maintenance_cost_analytics',
  MAINTENANCE_TYPE_DISTRIBUTION: 'maintenance_type_distribution',
  MAINTENANCE_OVERVIEW: 'maintenance_overview',

  // Split Maintenance Overview Widgets
  MAINTENANCE_DONUT_CHART: 'maintenance_donut_chart',
  MAINTENANCE_UPCOMING_COUNT: 'maintenance_upcoming_count',
  MAINTENANCE_OVERDUE_COUNT: 'maintenance_overdue_count',
  MAINTENANCE_TOTAL_COUNT: 'maintenance_total_count',

  // Vehicle Widgets
  VEHICLE_STATUS: 'vehicle_status',
  VEHICLE_ANALYTICS: 'vehicle_analytics',

  // Split Vehicle Status Widgets
  VEHICLE_TOTAL_COUNT: 'vehicle_total_count',
  VEHICLE_ACTIVE_COUNT: 'vehicle_active_count',
  VEHICLE_MAINTENANCE_COUNT: 'vehicle_maintenance_count',
  VEHICLE_IDLE_COUNT: 'vehicle_idle_count',

  // Tracking Widgets
  TRACKING_MAP: 'tracking_map',

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
  DRIVER_TOTAL_COUNT: 'driver_total_count',
  MY_NOTIFICATIONS: 'my_notifications',
  DRIVER_GROWTH_LINE_GRAPH: 'driver_growth_line_graph',
  VEHICLE_STATUS_BAR_CHART: 'vehicle_status_bar_chart',
});

export const WIDGET_CATEGORIES = Object.freeze({
  MAINTENANCE: 'Maintenance',
  VEHICLES: 'Vehicles',
  TRACKING: 'Tracking',
  PLUGINS: 'Plugins',
  ANALYTICS: 'Analytics',
  CHARTS: 'Charts',
  GENERAL: 'General',
  DRIVERS: 'Drivers',
  NOTIFICATIONS: 'Notifications',
});

// Security validation for widget metadata
const validateWidgetMetadata = metadata => {
  const errors = [];

  if (!metadata || typeof metadata !== 'object') {
    errors.push('Metadata must be an object');
    return errors;
  }

  // Validate title
  if (!metadata.title || typeof metadata.title !== 'string') {
    errors.push('Widget must have a valid title');
  } else if (metadata.title.length > 100) {
    errors.push('Widget title cannot exceed 100 characters');
  }

  // Validate description
  if (metadata.description && typeof metadata.description !== 'string') {
    errors.push('Widget description must be a string');
  } else if (metadata.description && metadata.description.length > 500) {
    errors.push('Widget description cannot exceed 500 characters');
  }

  // Validate category
  if (metadata.category && !Object.values(WIDGET_CATEGORIES).includes(metadata.category)) {
    errors.push('Invalid widget category');
  }

  // Validate size constraints
  if (metadata.defaultSize) {
    const {w, h} = metadata.defaultSize;
    if (typeof w !== 'number' || typeof h !== 'number' || w <= 0 || h <= 0 || w > 12 || h > 12) {
      errors.push('Invalid default size - width must be 1-12, height must be 1-12');
    }
  }

  if (metadata.minSize) {
    const {w, h} = metadata.minSize;
    if (typeof w !== 'number' || typeof h !== 'number' || w <= 0 || h <= 0 || w > 12 || h > 12) {
      errors.push('Invalid minimum size - width must be 1-12, height must be 1-12');
    }
  }

  if (metadata.maxSize) {
    const {w, h} = metadata.maxSize;
    if (typeof w !== 'number' || typeof h !== 'number' || w <= 0 || h <= 0 || w > 12 || h > 12) {
      errors.push('Invalid maximum size - width must be 1-12, height must be 1-12');
    }
  }

  return errors;
};

// Secure widget registry
const widgetRegistry = new Map();
const registeredTypes = new Set();

export const registerWidget = (type, component, metadata) => {
  // Validate widget type
  if (!type || typeof type !== 'string') {
    throw new Error('Widget type must be a non-empty string');
  }

  // Sanitize widget type (prevent injection attacks)
  const sanitizedType = type.replace(/[^a-zA-Z0-9_-]/g, '');
  if (sanitizedType !== type) {
    throw new Error(
      'Widget type contains invalid characters. Only alphanumeric, underscore, and hyphen allowed.'
    );
  }

  // Check if type is in allowed list (whitelist approach)
  if (!Object.values(WIDGET_TYPES).includes(type)) {
    throw new Error(`Widget type '${type}' is not in the allowed list of widget types`);
  }

  // Validate component
  if (!component || typeof component !== 'function') {
    throw new Error('Widget component must be a valid React component function');
  }

  // Validate metadata
  const metadataErrors = validateWidgetMetadata(metadata);
  if (metadataErrors.length > 0) {
    throw new Error(`Widget metadata validation failed: ${metadataErrors.join(', ')}`);
  }

  // Check for duplicate registration
  if (registeredTypes.has(type)) {
    console.warn(
      `Widget type '${type}' is being re-registered. Previous registration will be overwritten.`
    );
  }

  // Create secure metadata object with defaults
  const secureMetadata = Object.freeze({
    title: metadata?.title || 'Untitled Widget',
    description: metadata?.description || '',
    category: metadata?.category || WIDGET_CATEGORIES.GENERAL,
    defaultSize: metadata?.defaultSize || {w: 4, h: 3},
    minSize: metadata?.minSize || {w: 2, h: 2},
    maxSize: metadata?.maxSize || {w: 12, h: 8},
    configSchema: metadata?.configSchema || {},
    icon: metadata?.icon || null,
    version: metadata?.version || '1.0.0',
    author: metadata?.author || 'Unknown',
    // Add security flag
    isSecure: true,
    registeredAt: new Date().toISOString(),
  });

  // Register the widget with frozen metadata to prevent tampering
  widgetRegistry.set(
    type,
    Object.freeze({
      component,
      metadata: secureMetadata,
    })
  );

  registeredTypes.add(type);

  console.log(`Widget '${type}' registered successfully`);
};

export const getWidget = type => {
  // Validate and sanitize input
  if (!type || typeof type !== 'string') {
    console.warn('Invalid widget type requested:', type);
    return null;
  }

  const sanitizedType = type.replace(/[^a-zA-Z0-9_-]/g, '');
  if (sanitizedType !== type) {
    console.warn('Widget type contains invalid characters:', type);
    return null;
  }

  return widgetRegistry.get(type) || null;
};

export const getAllWidgets = () => {
  // Return array of [type, definition] pairs with additional security info
  return Array.from(widgetRegistry.entries()).map(([type, definition]) => [
    type,
    {
      ...definition,
      // Add runtime security check
      isValid: registeredTypes.has(type) && definition.metadata?.isSecure === true,
    },
  ]);
};

export const getWidgetsByCategory = category => {
  // Validate category
  if (!Object.values(WIDGET_CATEGORIES).includes(category)) {
    console.warn('Invalid widget category requested:', category);
    return [];
  }

  return Array.from(widgetRegistry.entries())
    .filter(([, definition]) => definition.metadata.category === category)
    .map(([type, definition]) => [type, definition]);
};

// Security function to validate widget instance data
export const validateWidgetInstance = widgetData => {
  const errors = [];

  if (!widgetData || typeof widgetData !== 'object') {
    errors.push('Widget data must be an object');
    return errors;
  }

  // Validate required fields
  if (!widgetData.id || typeof widgetData.id !== 'string') {
    errors.push('Widget must have a valid string ID');
  } else if (widgetData.id.length > 50) {
    errors.push('Widget ID cannot exceed 50 characters');
  }

  if (!widgetData.type || !registeredTypes.has(widgetData.type)) {
    errors.push('Widget must have a valid, registered type');
  }

  if (!widgetData.title || typeof widgetData.title !== 'string') {
    errors.push('Widget must have a valid title');
  } else if (widgetData.title.length > 100) {
    errors.push('Widget title cannot exceed 100 characters');
  }

  // Validate config if present
  if (widgetData.config && typeof widgetData.config !== 'object') {
    errors.push('Widget config must be an object');
  }

  // Validate size constraints if present
  if (widgetData.size) {
    const {w, h} = widgetData.size;
    if (typeof w !== 'number' || typeof h !== 'number' || w <= 0 || h <= 0 || w > 12 || h > 12) {
      errors.push('Invalid widget size - width must be 1-12, height must be 1-12');
    }
  }

  return errors;
};

// Sanitize widget configuration to prevent XSS
export const sanitizeWidgetConfig = config => {
  if (!config || typeof config !== 'object') {
    return {};
  }

  const sanitized = {};

  Object.keys(config).forEach(key => {
    const value = config[key];

    // Only allow safe data types and sanitize strings
    if (typeof value === 'string') {
      // Remove potential HTML/JS content
      sanitized[key] = value
        .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
        .replace(/javascript:/gi, '')
        .replace(/on\w+\s*=/gi, '')
        .substring(0, 1000); // Limit string length
    } else if (typeof value === 'number' && !isNaN(value)) {
      sanitized[key] = value;
    } else if (typeof value === 'boolean') {
      sanitized[key] = value;
    } else if (Array.isArray(value)) {
      // Recursively sanitize array items (limit array size)
      sanitized[key] = value
        .slice(0, 100)
        .map(item => (typeof item === 'string' ? item.substring(0, 100) : item));
    }
    // Ignore other data types for security
  });

  return sanitized;
};

// Helper function to generate secure widget IDs
export const generateWidgetId = () => {
  // Use crypto API if available, fallback to Math.random
  if (typeof crypto !== 'undefined' && crypto.getRandomValues) {
    const array = new Uint8Array(16);
    crypto.getRandomValues(array);
    return `widget_${Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('')}`;
  }

  // Fallback for older browsers
  return `widget_${Date.now()}_${Math.random().toString(36).substr(2, 16)}`;
};
