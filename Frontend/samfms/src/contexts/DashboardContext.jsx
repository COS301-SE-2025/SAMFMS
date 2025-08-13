import React, {createContext, useContext, useReducer, useEffect} from 'react';
import {generateWidgetId, WIDGET_TYPES} from '../utils/widgetRegistry';

const DashboardContext = createContext();

// Improved default dashboard configuration with better organization
const getDefaultDashboard = () => {
  const widgets = [
    // Top row - Key metrics and status (smaller, at the top for overview)
    {
      id: generateWidgetId(),
      type: WIDGET_TYPES.VEHICLE_STATUS,
      config: {title: 'Fleet Status'},
    },
    {
      id: generateWidgetId(),
      type: WIDGET_TYPES.STATS_CARD,
      config: {title: 'Key Statistics'},
    },
    {
      id: generateWidgetId(),
      type: WIDGET_TYPES.MAINTENANCE_ALERTS,
      config: {title: 'Active Alerts'},
    },

    // Second row - Main operational widgets (medium size)
    {
      id: generateWidgetId(),
      type: WIDGET_TYPES.MAINTENANCE_SUMMARY,
      config: {title: 'Maintenance Overview'},
    },
    {
      id: generateWidgetId(),
      type: WIDGET_TYPES.MAINTENANCE_RECORDS,
      config: {title: 'Recent Maintenance'},
    },

    // Third row - Analytics and costs (larger for data visualization)
    {
      id: generateWidgetId(),
      type: WIDGET_TYPES.MAINTENANCE_COST_ANALYTICS,
      config: {title: 'Cost Analytics'},
    },
    {
      id: generateWidgetId(),
      type: WIDGET_TYPES.LINE_CHART,
      config: {title: 'Performance Trends'},
    },

    // Fourth row - Additional insights
    {
      id: generateWidgetId(),
      type: WIDGET_TYPES.PIE_CHART,
      config: {title: 'Fleet Distribution'},
    },
    {
      id: generateWidgetId(),
      type: WIDGET_TYPES.BAR_CHART,
      config: {title: 'Usage Comparison'},
    },

    // Fifth row - System health
    {
      id: generateWidgetId(),
      type: WIDGET_TYPES.PLUGIN_HEALTH,
      config: {title: 'System Health'},
    },
  ];

  // Improved layout with better organization and visual hierarchy
  const layout = [
    // Top row - 3 small widgets for key metrics (4 units each)
    {i: widgets[0].id, x: 0, y: 0, w: 4, h: 3}, // Fleet Status
    {i: widgets[1].id, x: 4, y: 0, w: 4, h: 3}, // Key Statistics
    {i: widgets[2].id, x: 8, y: 0, w: 4, h: 3}, // Active Alerts

    // Second row - 2 medium widgets for operations (6 units each)
    {i: widgets[3].id, x: 0, y: 3, w: 6, h: 4}, // Maintenance Overview
    {i: widgets[4].id, x: 6, y: 3, w: 6, h: 4}, // Recent Maintenance

    // Third row - 2 large widgets for analytics (6 units each)
    {i: widgets[5].id, x: 0, y: 7, w: 6, h: 5}, // Cost Analytics
    {i: widgets[6].id, x: 6, y: 7, w: 6, h: 5}, // Performance Trends

    // Fourth row - 2 medium widgets for insights (6 units each)
    {i: widgets[7].id, x: 0, y: 12, w: 6, h: 4}, // Fleet Distribution
    {i: widgets[8].id, x: 6, y: 12, w: 6, h: 4}, // Usage Comparison

    // Fifth row - 1 widget centered for system health
    {i: widgets[9].id, x: 3, y: 16, w: 6, h: 3}, // System Health (centered)
  ];

  return {widgets, layout};
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
      console.log('🔧 SET_EDIT_MODE action:', {
        from: state.isEditing,
        to: action.payload,
        stack: new Error().stack
      });
      return {
        ...state,
        isEditing: action.payload,
      };

    case 'UPDATE_WIDGET_CONFIG':
      return {
        ...state,
        widgets: state.widgets.map(widget =>
          widget.id === action.payload.id
            ? {...widget, config: {...widget.config, ...action.payload.config}}
            : widget
        ),
      };

    case 'LOAD_DASHBOARD':
      console.log('📥 LOAD_DASHBOARD action:', {
        from: state.isEditing,
        to: action.payload.isEditing || false,
        stack: new Error().stack
      });
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

export const DashboardProvider = ({children, dashboardId = 'default'}) => {
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
