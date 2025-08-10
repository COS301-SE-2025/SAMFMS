import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { generateWidgetId, WIDGET_TYPES } from '../utils/widgetRegistry';

const DashboardContext = createContext();

// Rich default dashboard configuration with all available widgets
const getDefaultDashboard = () => {
  const widgets = [
    {
      id: generateWidgetId(),
      type: WIDGET_TYPES.MAINTENANCE_SUMMARY,
      config: { title: 'Maintenance Overview' },
    },
    {
      id: generateWidgetId(),
      type: WIDGET_TYPES.VEHICLE_STATUS,
      config: { title: 'Fleet Status' },
    },
    {
      id: generateWidgetId(),
      type: WIDGET_TYPES.MAINTENANCE_ALERTS,
      config: { title: 'Maintenance Alerts' },
    },
    {
      id: generateWidgetId(),
      type: WIDGET_TYPES.MAINTENANCE_RECORDS,
      config: { title: 'Maintenance Records' },
    },
    {
      id: generateWidgetId(),
      type: WIDGET_TYPES.MAINTENANCE_COST_ANALYTICS,
      config: { title: 'Cost Analytics' },
    },
    {
      id: generateWidgetId(),
      type: WIDGET_TYPES.PLUGIN_HEALTH,
      config: { title: 'Plugin Health' },
    },
    {
      id: generateWidgetId(),
      type: WIDGET_TYPES.PLUGIN_COUNT,
      config: { title: 'Plugin Count' },
    },
    {
      id: generateWidgetId(),
      type: WIDGET_TYPES.STATS_CARD,
      config: { title: 'Statistics' },
    },
    {
      id: generateWidgetId(),
      type: WIDGET_TYPES.VEHICLE_ANALYTICS,
      config: { title: 'Vehicle Analytics' },
    },
    {
      id: generateWidgetId(),
      type: WIDGET_TYPES.METRIC_CARD,
      config: { title: 'Key Metrics' },
    },
    {
      id: generateWidgetId(),
      type: WIDGET_TYPES.LINE_CHART,
      config: { title: 'Performance Trends' },
    },
    {
      id: generateWidgetId(),
      type: WIDGET_TYPES.BAR_CHART,
      config: { title: 'Fleet Comparison' },
    },
    {
      id: generateWidgetId(),
      type: WIDGET_TYPES.PIE_CHART,
      config: { title: 'Distribution Analysis' },
    },
  ];

  const layout = widgets.map((widget, index) => ({
    i: widget.id,
    x: (index % 4) * 3, // 4 widgets per row, each 3 columns wide for more density
    y: Math.floor(index / 4) * 3, // Each row is 3 units tall for more compact layout
    w: 3, // Slightly narrower width for more widgets per row
    h: 3, // Slightly shorter height for more compact layout
  }));

  return { widgets, layout };
};

const dashboardReducer = (state, action) => {
  switch (action.type) {
    case 'ADD_WIDGET':
      const widget = action.payload;
      const newWidgets = [...state.widgets, widget];
      const newY =
        state.layout.length > 0 ? Math.max(...state.layout.map(item => item.y + item.h)) : 0;

      const newLayoutItem = {
        i: widget.id,
        x: 0,
        y: newY,
        w: 4,
        h: 4,
      };

      return {
        ...state,
        widgets: newWidgets,
        layout: [...state.layout, newLayoutItem],
      };

    case 'REMOVE_WIDGET':
      const widgetId = action.payload;
      return {
        ...state,
        widgets: state.widgets.filter(w => w.id !== widgetId),
        layout: state.layout.filter(l => l.i !== widgetId),
      };

    case 'UPDATE_LAYOUT':
      return {
        ...state,
        layout: action.payload,
      };

    case 'RESET_LAYOUT':
      const defaultLayout = action.payload || getDefaultLayout(state.widgets);
      return {
        ...state,
        layout: defaultLayout,
      };

    case 'SET_EDIT_MODE':
      return {
        ...state,
        isEditing: action.payload,
      };

    case 'UPDATE_WIDGET_CONFIG':
      return {
        ...state,
        widgets: state.widgets.map(widget =>
          widget.id === action.payload.id
            ? { ...widget, config: { ...widget.config, ...action.payload.config } }
            : widget
        ),
      };

    case 'LOAD_DASHBOARD':
      return {
        ...state,
        widgets: action.payload.widgets || [],
        layout: action.payload.layout || [],
        isEditing: action.payload.isEditing || false,
      };

    default:
      return state;
  }
};

// Simple default layout generator
const getDefaultLayout = widgets => {
  return widgets.map((widget, index) => ({
    i: widget.id,
    x: (index % 3) * 4,
    y: Math.floor(index / 3) * 4,
    w: 4,
    h: 4,
  }));
};

export const DashboardProvider = ({ children, dashboardId = 'default' }) => {
  const defaultDashboard = getDefaultDashboard();
  const [state, dispatch] = useReducer(dashboardReducer, {
    widgets: defaultDashboard.widgets,
    layout: getDefaultLayout(defaultDashboard.widgets),
    isEditing: false,
  });

  // Load dashboard from localStorage on mount
  useEffect(() => {
    const loadSavedDashboard = () => {
      try {
        const savedDashboard = localStorage.getItem(`dashboard_${dashboardId}`);
        if (savedDashboard) {
          const data = JSON.parse(savedDashboard);

          // Validate saved data structure
          if (data && Array.isArray(data.widgets) && Array.isArray(data.layout)) {
            // Ensure widget IDs match layout IDs
            const validatedLayout = data.layout.filter(layoutItem =>
              data.widgets.some(widget => widget.id === layoutItem.i)
            );

            dispatch({
              type: 'LOAD_DASHBOARD',
              payload: {
                widgets: data.widgets,
                layout:
                  validatedLayout.length > 0 ? validatedLayout : getDefaultLayout(data.widgets),
                isEditing: data.isEditing || false,
              },
            });
          }
        }
      } catch (error) {
        console.error('Failed to load saved dashboard:', error);
        // If loading fails, keep the default dashboard
      }
    };

    loadSavedDashboard();
  }, [dashboardId]);

  // Enhanced auto-save functionality with debouncing
  useEffect(() => {
    const saveDashboard = () => {
      try {
        const dashboardData = {
          widgets: state.widgets,
          layout: state.layout,
          isEditing: state.isEditing,
          lastSaved: new Date().toISOString(),
        };

        localStorage.setItem(`dashboard_${dashboardId}`, JSON.stringify(dashboardData));

        // Also save a backup with timestamp
        const backupKey = `dashboard_${dashboardId}_backup_${Date.now()}`;
        localStorage.setItem(backupKey, JSON.stringify(dashboardData));

        // Clean up old backups (keep only the last 3)
        const backupKeys = Object.keys(localStorage)
          .filter(key => key.startsWith(`dashboard_${dashboardId}_backup_`))
          .sort()
          .reverse();

        if (backupKeys.length > 3) {
          backupKeys.slice(3).forEach(key => localStorage.removeItem(key));
        }
      } catch (error) {
        console.error('Failed to save dashboard:', error);
        // Handle localStorage quota exceeded
        if (error.name === 'QuotaExceededError') {
          console.warn('localStorage quota exceeded, clearing old backups');
          const backupKeys = Object.keys(localStorage).filter(key =>
            key.startsWith(`dashboard_${dashboardId}_backup_`)
          );
          backupKeys.forEach(key => localStorage.removeItem(key));

          // Try saving again without backups
          try {
            const dashboardData = {
              widgets: state.widgets,
              layout: state.layout,
              isEditing: state.isEditing,
              lastSaved: new Date().toISOString(),
            };
            localStorage.setItem(`dashboard_${dashboardId}`, JSON.stringify(dashboardData));
          } catch (retryError) {
            console.error('Failed to save dashboard even after cleanup:', retryError);
          }
        }
      }
    };

    // Debounce saves to avoid excessive localStorage writes
    const timeoutId = setTimeout(saveDashboard, 500);
    return () => clearTimeout(timeoutId);
  }, [state.widgets, state.layout, state.isEditing, dashboardId]);

  // Manual save/load utilities
  const saveDashboardManually = () => {
    try {
      const dashboardData = {
        widgets: state.widgets,
        layout: state.layout,
        isEditing: state.isEditing,
        lastSaved: new Date().toISOString(),
      };
      localStorage.setItem(`dashboard_${dashboardId}`, JSON.stringify(dashboardData));
      return true;
    } catch (error) {
      console.error('Manual save failed:', error);
      return false;
    }
  };

  const resetDashboard = () => {
    try {
      localStorage.removeItem(`dashboard_${dashboardId}`);
      const defaultDashboard = getDefaultDashboard();
      dispatch({
        type: 'LOAD_DASHBOARD',
        payload: {
          widgets: defaultDashboard.widgets,
          layout: getDefaultLayout(defaultDashboard.widgets),
          isEditing: false,
        },
      });
      return true;
    } catch (error) {
      console.error('Reset dashboard failed:', error);
      return false;
    }
  };

  const exportDashboard = () => {
    try {
      const dashboardData = {
        widgets: state.widgets,
        layout: state.layout,
        isEditing: state.isEditing,
        exportedAt: new Date().toISOString(),
      };
      return JSON.stringify(dashboardData, null, 2);
    } catch (error) {
      console.error('Export dashboard failed:', error);
      return null;
    }
  };

  const importDashboard = dashboardJson => {
    try {
      const data = JSON.parse(dashboardJson);
      if (data && Array.isArray(data.widgets) && Array.isArray(data.layout)) {
        dispatch({
          type: 'LOAD_DASHBOARD',
          payload: {
            widgets: data.widgets,
            layout: data.layout,
            isEditing: data.isEditing || false,
          },
        });
        return true;
      }
      return false;
    } catch (error) {
      console.error('Import dashboard failed:', error);
      return false;
    }
  };

  const contextValue = {
    state,
    dispatch,
    saveDashboardManually,
    resetDashboard,
    exportDashboard,
    importDashboard,
  };

  return <DashboardContext.Provider value={contextValue}>{children}</DashboardContext.Provider>;
};

export const useDashboard = () => {
  const context = useContext(DashboardContext);
  if (!context) {
    throw new Error('useDashboard must be used within DashboardProvider');
  }
  return context;
};
