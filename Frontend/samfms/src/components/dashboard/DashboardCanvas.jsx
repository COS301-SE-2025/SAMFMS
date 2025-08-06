import React, { useCallback } from 'react';
import { Responsive, WidthProvider } from 'react-grid-layout';
import { useDashboard } from '../../contexts/DashboardContext';
import { getWidget } from '../../utils/widgetRegistry';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';

const ResponsiveGridLayout = WidthProvider(Responsive);

export const DashboardCanvas = () => {
  const { state, dispatch } = useDashboard();

  // Default layout configuration for common dashboard layouts
  const getDefaultLayout = widgets => {
    const defaultPositions = [
      { x: 0, y: 0, w: 4, h: 3 }, // Top left - larger widget
      { x: 4, y: 0, w: 4, h: 2 }, // Top middle
      { x: 8, y: 0, w: 4, h: 2 }, // Top right
      { x: 0, y: 3, w: 3, h: 2 }, // Second row left
      { x: 3, y: 3, w: 3, h: 2 }, // Second row middle-left
      { x: 6, y: 3, w: 3, h: 2 }, // Second row middle-right
      { x: 9, y: 3, w: 3, h: 2 }, // Second row right
      { x: 0, y: 5, w: 6, h: 2 }, // Third row left (wide)
      { x: 6, y: 5, w: 6, h: 2 }, // Third row right (wide)
    ];

    return widgets.map((widget, index) => {
      const defaultPos = defaultPositions[index] || {
        x: (index * 2) % 12,
        y: Math.floor(index / 6) * 2,
        w: 2,
        h: 2,
      };
      const widgetSize = widget.size || { w: 2, h: 2 };

      return {
        i: widget.id,
        x: defaultPos.x,
        y: defaultPos.y,
        w: widgetSize.w || defaultPos.w,
        h: widgetSize.h || defaultPos.h,
        minW: 1,
        minH: 1,
        maxW: 12,
        maxH: 6,
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
    md: layouts.lg.map(item => ({ ...item, w: Math.min(item?.w || 2, 10) })),
    sm: layouts.lg.map(item => ({ ...item, w: Math.min(item?.w || 2, 6) })),
    xs: layouts.lg.map(item => ({ ...item, w: Math.min(item?.w || 2, 4) })),
    xxs: layouts.lg.map(item => ({ ...item, w: Math.min(item?.w || 2, 2) })),
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
        {state.widgets.map(widget => {
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
            <div key={widget.id} className="dashboard-widget">
              <WidgetComponent id={widget.id} title={widget.title} config={widget.config} />
            </div>
          );
        })}
      </ResponsiveGridLayout>
    </div>
  );
};
