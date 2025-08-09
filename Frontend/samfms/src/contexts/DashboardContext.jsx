import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { generateWidgetId, WIDGET_TYPES } from '../utils/widgetRegistry';

const DashboardContext = createContext();

// Simple default dashboard configuration
const getDefaultDashboard = () => ({
  widgets: [
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
  ],
  layout: [
    { i: '', x: 0, y: 0, w: 4, h: 4 },
    { i: '', x: 4, y: 0, w: 4, h: 4 },
    { i: '', x: 8, y: 0, w: 4, h: 4 },
  ],
});

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

    case 'LOAD_DASHBOARD':
      return {
        ...state,
        widgets: action.payload.widgets || [],
        layout: action.payload.layout || [],
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
    try {
      const savedDashboard = localStorage.getItem(`dashboard_${dashboardId}`);
      if (savedDashboard) {
        const data = JSON.parse(savedDashboard);
        dispatch({ type: 'LOAD_DASHBOARD', payload: data });
      }
    } catch (error) {
      console.error('Failed to load saved dashboard:', error);
    }
  }, [dashboardId]);

  // Auto-save functionality
  useEffect(() => {
    try {
      localStorage.setItem(
        `dashboard_${dashboardId}`,
        JSON.stringify({
          widgets: state.widgets,
          layout: state.layout,
        })
      );
    } catch (error) {
      console.error('Failed to save dashboard:', error);
    }
  }, [state.widgets, state.layout, dashboardId]);

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
