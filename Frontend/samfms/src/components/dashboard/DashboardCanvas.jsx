import React, { useCallback } from 'react';
import { Responsive, WidthProvider } from 'react-grid-layout';
import { useDashboard } from '../../contexts/DashboardContext';
import { getWidget } from '../../utils/widgetRegistry';
import FadeIn from '../ui/FadeIn';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';

const ResponsiveGridLayout = WidthProvider(Responsive);

export const DashboardCanvas = () => {
  const { state, dispatch } = useDashboard();

  // Default layout configuration for common dashboard layouts
  const getDefaultLayout = widgets => {
    const occupiedPositions = new Set();
    let maxY = 0;

    // Helper function to check if a position is occupied
    const isPositionOccupied = (x, y, w, h) => {
      for (let px = x; px < x + w; px++) {
        for (let py = y; py < y + h; py++) {
          if (occupiedPositions.has(`${px},${py}`)) {
            return true;
          }
        }
      }
      return false;
    };

    // Helper function to mark positions as occupied
    const markPositionsOccupied = (x, y, w, h) => {
      for (let px = x; px < x + w; px++) {
        for (let py = y; py < y + h; py++) {
          occupiedPositions.add(`${px},${py}`);
        }
      }
      maxY = Math.max(maxY, y + h);
    };

    // Find next available position that fits the widget
    const findNextPosition = (w, h) => {
      // Try to place from top-left, scanning row by row
      for (let y = 0; y <= maxY + 5; y++) {
        for (let x = 0; x <= 12 - w; x++) {
          if (!isPositionOccupied(x, y, w, h)) {
            return { x, y };
          }
        }
      }
      // If no space found, place at bottom
      return { x: 0, y: maxY + 1 };
    };

    return widgets.map(widget => {
      const widgetSize = widget.size || { w: 2, h: 2 };
      const w = Math.max(Math.min(widgetSize.w || 2, 12), 2);
      const h = Math.max(Math.min(widgetSize.h || 2, 8), 2);

      const { x, y } = findNextPosition(w, h);
      markPositionsOccupied(x, y, w, h);

      return {
        i: widget.id,
        x,
        y,
        w,
        h,
        minW: 2,
        minH: 2,
        maxW: 12,
        maxH: 8,
      };
    });
  };

  // Convert widget sizes to grid layout format
  const layouts = {
    lg: state.layout && state.layout.length > 0 ? state.layout : getDefaultLayout(state.widgets),
  };

  // Generate layouts for all breakpoints with proper error handling
  const allLayouts = {
    lg: layouts.lg,
    md: layouts.lg.map(item => ({
      ...item,
      w: Math.max(Math.min(item?.w || 2, 10), 2),
      minW: 2,
      minH: 2,
    })),
    sm: layouts.lg.map(item => ({
      ...item,
      w: Math.max(Math.min(item?.w || 2, 6), 2),
      minW: 2,
      minH: 2,
    })),
    xs: layouts.lg.map(item => ({
      ...item,
      w: Math.max(Math.min(item?.w || 2, 4), 2),
      minW: 2,
      minH: 2,
    })),
    xxs: layouts.lg.map(item => ({
      ...item,
      w: Math.max(Math.min(item?.w || 2, 2), 2),
      minW: 2,
      minH: 2,
    })),
  };

  const handleLayoutChange = useCallback(
    (layout, allLayouts) => {
      if (state.isEditing) {
        dispatch({ type: 'UPDATE_LAYOUT', payload: layout });
      }
    },
    [dispatch, state.isEditing]
  );

  const handleResizeStop = useCallback(
    (layout, oldItem, newItem, placeholder, e, element) => {
      if (state.isEditing) {
        dispatch({ type: 'UPDATE_LAYOUT', payload: layout });
      }
    },
    [dispatch, state.isEditing]
  );

  const handleDragStop = useCallback(
    (layout, oldItem, newItem, placeholder, e, element) => {
      if (state.isEditing) {
        dispatch({ type: 'UPDATE_LAYOUT', payload: layout });
      }
    },
    [dispatch, state.isEditing]
  );

  const handleBreakpointChange = useCallback((newBreakpoint, newCols) => {
    // Handle breakpoint changes if needed
  }, []);

  if (state.widgets.length === 0) {
    return (
      <div className="dashboard-canvas p-4">
        <div className="flex items-center justify-center h-64 border-2 border-dashed border-border rounded-lg">
          <div className="text-center">
            <h3 className="text-lg font-medium text-muted-foreground mb-2">
              Your dashboard is empty
            </h3>
            <p className="text-sm text-muted-foreground">
              {state.isEditing
                ? "Click 'Add Widget' to get started"
                : 'Enable edit mode to customize your dashboard'}
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-canvas p-4">
      <ResponsiveGridLayout
        className={`layout ${state.isEditing ? 'edit-mode' : ''}`}
        layouts={allLayouts}
        breakpoints={{ lg: 1200, md: 996, sm: 768, xs: 480, xxs: 0 }}
        cols={{ lg: 12, md: 10, sm: 6, xs: 4, xxs: 2 }}
        rowHeight={100}
        margin={[16, 16]}
        containerPadding={[0, 0]}
        isDraggable={state.isEditing}
        isResizable={state.isEditing}
        onLayoutChange={handleLayoutChange}
        onDragStop={handleDragStop}
        onResizeStop={handleResizeStop}
        onBreakpointChange={handleBreakpointChange}
        draggableHandle=".widget-drag-handle"
        resizeHandles={['se', 'sw', 'ne', 'nw', 's', 'n', 'e', 'w']}
        compactType="vertical"
        preventCollision={false}
        useCSSTransforms={true}
      >
        {state.widgets.map((widget, index) => {
          const widgetDefinition = getWidget(widget.type);
          if (!widgetDefinition) {
            return (
              <div key={widget.id} className="bg-card border border-border rounded-lg p-4">
                <p className="text-destructive">Unknown widget type: {widget.type}</p>
              </div>
            );
          }

          const WidgetComponent = widgetDefinition.component;
          return (
            <FadeIn key={widget.id} delay={index * 0.1} className="dashboard-widget">
              <WidgetComponent id={widget.id} title={widget.title} config={widget.config} />
            </FadeIn>
          );
        })}
      </ResponsiveGridLayout>
    </div>
  );
};
