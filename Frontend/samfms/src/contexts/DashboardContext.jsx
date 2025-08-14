import React, {createContext, useContext, useReducer, useEffect} from 'react';
import {generateWidgetId, WIDGET_TYPES, getWidget} from '../utils/widgetRegistry';

const DashboardContext = createContext();

// Improved default dashboard configuration to match the screenshot layout
const getDefaultDashboard = () => {
  const widgets = [
    // First row - 4 small widgets (Fleet Status, System Health, Recent Maintenance, Alerts)
    {
      id: generateWidgetId(),
      type: WIDGET_TYPES.VEHICLE_STATUS,
      config: {title: 'Fleet Status'},
    },
    {
      id: generateWidgetId(),
      type: WIDGET_TYPES.PLUGIN_HEALTH,
      config: {title: 'System Health'},
    },
    {
      id: generateWidgetId(),
      type: WIDGET_TYPES.MAINTENANCE_RECORDS,
      config: {title: 'Recent Maintenance'},
    },
    {
      id: generateWidgetId(),
      type: WIDGET_TYPES.MAINTENANCE_ALERTS,
      config: {title: 'Maintenance Alerts'},
    },

    // Second row - 2 larger widgets (Maintenance Overview, Cost Analytics)
    {
      id: generateWidgetId(),
      type: WIDGET_TYPES.MAINTENANCE_SUMMARY,
      config: {title: 'Maintenance Overview'},
    },
    {
      id: generateWidgetId(),
      type: WIDGET_TYPES.MAINTENANCE_COST_ANALYTICS,
      config: {title: 'Cost Analytics'},
    },
  ]; return {widgets, layout: getDefaultLayout(widgets)};
};

// Scale a 12-column width to the canvas 40-column grid
const scaleWidthTo40 = w12 => {
  const w = Math.max(1, Math.min(12, Number(w12) || 4));
  return Math.max(1, Math.min(40, Math.round((w / 12) * 40)));
};

// Generate layout using each widget's default size from registry
const getDefaultLayout = widgets => {
  const COLS = 40;
  const layout = [];
  let cursorX = 0;
  let cursorY = 0;
  let rowHeight = 0;

  widgets.forEach(widget => {
    const meta = getWidget(widget.type)?.metadata;
    const defW12 = meta?.defaultSize?.w ?? 4;
    const defH = meta?.defaultSize?.h ?? 4;
    const w = scaleWidthTo40(defW12);
    const h = Math.max(1, Math.min(8, Number(defH) || 4));

    // Wrap to next row if exceeds columns
    if (cursorX + w > COLS) {
      cursorX = 0;
      cursorY += rowHeight || 0;
      rowHeight = 0;
    }

    layout.push({i: widget.id, x: cursorX, y: cursorY, w, h});
    cursorX += w;
    rowHeight = Math.max(rowHeight, h);
  });

  return layout;
};

const dashboardReducer = (state, action) => {
  switch (action.type) {
    case 'ADD_WIDGET':
      const widget = action.payload;
      const newWidgets = [...state.widgets, widget];
      const newY =
        state.layout.length > 0 ? Math.max(...state.layout.map(item => item.y + item.h)) : 0;

      const meta = getWidget(widget.type)?.metadata;
      const w = scaleWidthTo40(meta?.defaultSize?.w ?? 4);
      const h = Math.max(1, Math.min(8, Number(meta?.defaultSize?.h ?? 4)));
      const newLayoutItem = {i: widget.id, x: 0, y: newY, w, h};

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
// const getDefaultLayout = widgets => {
//   return widgets.map((widget, index) => ({
//     i: widget.id,
//     x: (index % 3) * 4,
//     y: Math.floor(index / 3) * 4,
//     w: 4,
//     h: 4,
//   }));
// };

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
            // FORCE REGENERATE LAYOUT with new default sizes - temporary fix
            // Comment out this line to use saved layouts again
            console.log('🔄 Force regenerating layout with new default sizes');
            const newLayout = getDefaultLayout(data.widgets);

            dispatch({
              type: 'LOAD_DASHBOARD',
              payload: {
                widgets: data.widgets,
                layout: newLayout, // Always use new layout
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
