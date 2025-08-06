import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { generateWidgetId, WIDGET_TYPES } from '../utils/widgetRegistry';

const DashboardContext = createContext();

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
  switch (action.type) {
    case 'SET_LAYOUT':
      return { ...state, layout: action.payload };
    case 'ADD_WIDGET':
      // Find the next available position for the new widget
      const existingLayout = state.layout;
      const widget = action.payload;
      const widgetSize = widget.size || { w: 2, h: 2 };

      // Calculate position for new widget (simple algorithm - place at the end)
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
        w: widgetSize.w || 2,
        h: widgetSize.h || 2,
        minW: 1,
        minH: 1,
        maxW: 12,
        maxH: 6,
      };

      return {
        ...state,
        widgets: [...state.widgets, widget],
        layout: [...existingLayout, newLayoutItem],
      };
    case 'REMOVE_WIDGET':
      return {
        ...state,
        widgets: state.widgets.filter(w => w.id !== action.payload),
        layout: state.layout.filter(l => l.i !== action.payload),
      };
    case 'UPDATE_WIDGET_CONFIG':
      return {
        ...state,
        widgets: state.widgets.map(w =>
          w.id === action.payload.id
            ? { ...w, config: { ...w.config, ...action.payload.config } }
            : w
        ),
      };
    case 'SET_EDITING_MODE':
      return { ...state, isEditing: action.payload };
    case 'SET_WIDGETS':
      return { ...state, widgets: action.payload.widgets, layout: action.payload.layout };
    case 'UPDATE_LAYOUT':
      return { ...state, layout: action.payload };
    case 'RESET_TO_DEFAULT':
      const defaultDashboard = getDefaultDashboard();
      return {
        ...state,
        widgets: defaultDashboard.widgets,
        layout: [],
        isEditing: false,
      };
    default:
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

  // Load dashboard from localStorage on mount
  useEffect(() => {
    const savedDashboard = localStorage.getItem(`dashboard_${dashboardId}`);
    if (savedDashboard) {
      try {
        const { widgets, layout } = JSON.parse(savedDashboard);
        dispatch({ type: 'SET_WIDGETS', payload: { widgets, layout } });
      } catch (error) {
        console.error('Failed to load saved dashboard:', error);
      }
    }
  }, [dashboardId]);

  // Auto-save functionality
  useEffect(() => {
    if (state.widgets.length > 0 || state.layout.length > 0) {
      const saveToStorage = () => {
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
      };

      const timeoutId = setTimeout(saveToStorage, 1000);
      return () => clearTimeout(timeoutId);
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
