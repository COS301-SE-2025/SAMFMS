import React, { createContext, useContext, useReducer, useEffect, useCallback } from 'react';
import { generateWidgetId, WIDGET_TYPES } from '../utils/widgetRegistry';

const DashboardContext = createContext();

// State validation utility
const validateWidget = widget => {
  if (!widget || typeof widget !== 'object') return false;
  if (!widget.id || typeof widget.id !== 'string') return false;
  if (!widget.type || typeof widget.type !== 'string') return false;
  if (widget.config && typeof widget.config !== 'object') return false;
  return true;
};

const validateLayout = layout => {
  if (!Array.isArray(layout)) return false;
  return layout.every(
    item =>
      item &&
      typeof item === 'object' &&
      typeof item.i === 'string' &&
      typeof item.x === 'number' &&
      item.x >= 0 &&
      typeof item.y === 'number' &&
      item.y >= 0 &&
      typeof item.w === 'number' &&
      item.w > 0 &&
      typeof item.h === 'number' &&
      item.h > 0
  );
};

// Normalize state to ensure consistency
const normalizeState = state => {
  const normalizedWidgets = (state.widgets || []).filter(validateWidget);
  const normalizedLayout = validateLayout(state.layout) ? state.layout : [];

  // Remove layout items that don't have corresponding widgets
  const widgetIds = new Set(normalizedWidgets.map(w => w.id));
  const filteredLayout = normalizedLayout.filter(item => widgetIds.has(item.i));

  return {
    ...state,
    widgets: normalizedWidgets,
    layout: filteredLayout,
    isEditing: Boolean(state.isEditing),
    dashboardId: state.dashboardId || 'default',
  };
};

// Default dashboard configuration
const getDefaultDashboard = () => ({
  widgets: [
    {
      id: generateWidgetId(),
      type: WIDGET_TYPES.MAINTENANCE_SUMMARY,
      title: 'Maintenance Overview',
      config: { title: 'Maintenance Overview', refreshInterval: 30 },
      size: { w: 4, h: 3 },
    },
    {
      id: generateWidgetId(),
      type: WIDGET_TYPES.VEHICLE_STATUS,
      title: 'Fleet Status',
      config: { title: 'Fleet Status', refreshInterval: 60 },
      size: { w: 4, h: 2 },
    },
    {
      id: generateWidgetId(),
      type: WIDGET_TYPES.MAINTENANCE_ALERTS,
      title: 'Maintenance Alerts',
      config: { title: 'Maintenance Alerts', refreshInterval: 30 },
      size: { w: 4, h: 2 },
    },
    {
      id: generateWidgetId(),
      type: WIDGET_TYPES.MAINTENANCE_RECORDS,
      title: 'Recent Maintenance',
      config: { title: 'Recent Maintenance', refreshInterval: 120 },
      size: { w: 6, h: 2 },
    },
    {
      id: generateWidgetId(),
      type: WIDGET_TYPES.MAINTENANCE_COST_ANALYTICS,
      title: 'Cost Analytics',
      config: { title: 'Cost Analytics', refreshInterval: 300 },
      size: { w: 6, h: 2 },
    },
  ],
  layout: [],
});

const dashboardReducer = (state, action) => {
  try {
    let newState;

    switch (action.type) {
      case 'SET_LAYOUT':
        if (!validateLayout(action.payload)) {
          console.warn('Invalid layout provided, ignoring update');
          return state;
        }
        newState = { ...state, layout: action.payload };
        break;

      case 'ADD_WIDGET':
        const widget = action.payload;

        if (!validateWidget(widget)) {
          console.warn('Invalid widget provided, ignoring add operation');
          return state;
        }

        // Check for duplicate widget IDs
        if (state.widgets.some(w => w.id === widget.id)) {
          console.warn(`Widget with ID ${widget.id} already exists`);
          return state;
        }

        // Find the next available position for the new widget
        const existingLayout = state.layout;
        const widgetSize = widget.size || { w: 2, h: 2 };

        // Calculate position for new widget (improved algorithm)
        let newY = 0;
        if (existingLayout.length > 0) {
          const maxYItem = existingLayout.reduce((max, item) =>
            (item.y || 0) + (item.h || 2) > (max.y || 0) + (max.h || 2) ? item : max
          );
          newY = (maxYItem.y || 0) + (maxYItem.h || 2);
        }

        const newLayoutItem = {
          i: widget.id,
          x: 0,
          y: newY,
          w: Math.max(Math.min(widgetSize.w || 2, 12), 2),
          h: Math.max(Math.min(widgetSize.h || 2, 8), 2),
          minW: Math.max(widgetSize.minW || 2, 1),
          minH: Math.max(widgetSize.minH || 2, 1),
          maxW: Math.min(widgetSize.maxW || 12, 12),
          maxH: Math.min(widgetSize.maxH || 8, 8),
        };

        newState = {
          ...state,
          widgets: [...state.widgets, widget],
          layout: [...existingLayout, newLayoutItem],
        };
        break;

      case 'REMOVE_WIDGET':
        const widgetId = action.payload;
        if (!widgetId || typeof widgetId !== 'string') {
          console.warn('Invalid widget ID provided for removal');
          return state;
        }

        newState = {
          ...state,
          widgets: state.widgets.filter(w => w.id !== widgetId),
          layout: state.layout.filter(l => l.i !== widgetId),
        };
        break;

      case 'UPDATE_WIDGET_CONFIG':
        const { id, config } = action.payload || {};
        if (!id || !config || typeof config !== 'object') {
          console.warn('Invalid widget config update payload');
          return state;
        }

        newState = {
          ...state,
          widgets: state.widgets.map(w =>
            w.id === id ? { ...w, config: { ...w.config, ...config } } : w
          ),
        };
        break;

      case 'SET_EDITING_MODE':
        newState = { ...state, isEditing: Boolean(action.payload) };
        break;

      case 'SET_WIDGETS':
        const { widgets, layout } = action.payload || {};
        if (!Array.isArray(widgets)) {
          console.warn('Invalid widgets array provided');
          return state;
        }

        const validWidgets = widgets.filter(validateWidget);
        const validLayout = validateLayout(layout) ? layout : [];

        newState = {
          ...state,
          widgets: validWidgets,
          layout: validLayout,
        };
        break;

      case 'UPDATE_LAYOUT':
        if (!validateLayout(action.payload)) {
          console.warn('Invalid layout provided for update');
          return state;
        }
        newState = { ...state, layout: action.payload };
        break;

      case 'RESET_TO_DEFAULT':
        const defaultDashboard = getDefaultDashboard();
        newState = {
          ...state,
          widgets: defaultDashboard.widgets,
          layout: [],
          isEditing: false,
        };
        break;

      default:
        return state;
    }

    // Normalize and validate the new state before returning
    return normalizeState(newState);
  } catch (error) {
    console.error('Dashboard reducer error:', error);
    // Return current state on error to prevent crashes
    return state;
  }
};

export const DashboardProvider = ({ children, dashboardId = 'default' }) => {
  const [state, dispatch] = useReducer(dashboardReducer, {
    widgets: [],
    layout: [],
    isEditing: false,
    dashboardId,
  });

  // Debounced save function to prevent excessive localStorage writes
  const debouncedSave = useCallback(
    data => {
      const timeoutId = setTimeout(() => {
        try {
          localStorage.setItem(`dashboard_${dashboardId}`, JSON.stringify(data));
        } catch (error) {
          console.error('Failed to save dashboard to localStorage:', error);
        }
      }, 1000);

      return () => clearTimeout(timeoutId);
    },
    [dashboardId]
  );

  // Load dashboard from localStorage on mount
  useEffect(() => {
    const loadDashboard = () => {
      try {
        const savedDashboard = localStorage.getItem(`dashboard_${dashboardId}`);
        if (savedDashboard) {
          const { widgets, layout } = JSON.parse(savedDashboard);
          // Validate loaded data before dispatching
          if (Array.isArray(widgets) && Array.isArray(layout)) {
            dispatch({ type: 'SET_WIDGETS', payload: { widgets, layout } });
          }
        }
      } catch (error) {
        console.error('Failed to load saved dashboard:', error);
        // Could dispatch a default dashboard here if needed
      }
    };

    loadDashboard();
  }, [dashboardId]);

  // Auto-save functionality with debouncing
  useEffect(() => {
    if (state.widgets.length > 0 || state.layout.length > 0) {
      const cleanup = debouncedSave({
        widgets: state.widgets,
        layout: state.layout,
      });

      return cleanup;
    }
  }, [state.widgets, state.layout, debouncedSave]);

  return (
    <DashboardContext.Provider value={{ state, dispatch }}>{children}</DashboardContext.Provider>
  );
};

export const useDashboard = () => {
  const context = useContext(DashboardContext);
  if (!context) {
    throw new Error('useDashboard must be used within DashboardProvider');
  }
  return context;
};
