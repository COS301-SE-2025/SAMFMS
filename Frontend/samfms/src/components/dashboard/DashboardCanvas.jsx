import React, { useCallback, useState } from 'react';
import { Responsive, WidthProvider } from 'react-grid-layout';
import { useDashboard } from '../../contexts/DashboardContext';
import { getWidget } from '../../utils/widgetRegistry';
import WidgetErrorBoundary from './WidgetErrorBoundary';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';

const ResponsiveGridLayout = WidthProvider(Responsive);

export const DashboardCanvas = () => {
  const { state, dispatch } = useDashboard();
  const [widgetRetryKeys, setWidgetRetryKeys] = useState({});

  // Helper to force widget re-render on retry
  const handleWidgetRetry = useCallback(widgetId => {
    setWidgetRetryKeys(prev => ({
      ...prev,
      [widgetId]: (prev[widgetId] || 0) + 1,
    }));
  }, []);

  // Improved default layout configuration with better collision detection
  const getDefaultLayout = useCallback(widgets => {
    if (!widgets || widgets.length === 0) return [];

    const occupiedPositions = new Set();
    let maxY = 0;
    const gridCols = 12;
    const maxWidgetHeight = 8;

    // Helper function to check if a position is occupied with bounds checking
    const isPositionOccupied = (x, y, w, h) => {
      // Check bounds
      if (x < 0 || y < 0 || x + w > gridCols || w <= 0 || h <= 0) {
        return true;
      }

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

    // Improved position finding with more efficient scanning
    const findNextPosition = (w, h) => {
      // Ensure minimum and maximum constraints
      w = Math.max(Math.min(w, gridCols), 2);
      h = Math.max(Math.min(h, maxWidgetHeight), 2);

      // Try to place from top-left, scanning row by row more efficiently
      for (let y = 0; y <= maxY + 5; y++) {
        for (let x = 0; x <= gridCols - w; x++) {
          if (!isPositionOccupied(x, y, w, h)) {
            return { x, y, w, h };
          }
        }
      }
      // If no space found, place at bottom
      return { x: 0, y: maxY + 1, w, h };
    };

    return widgets.map((widget, index) => {
      const widgetSize = widget.size || { w: 4, h: 3 };
      const { x, y, w, h } = findNextPosition(widgetSize.w || 4, widgetSize.h || 3);

      markPositionsOccupied(x, y, w, h);

      return {
        i: widget.id,
        x,
        y,
        w,
        h,
        minW: Math.max(widgetSize.minW || 2, 2),
        minH: Math.max(widgetSize.minH || 2, 2),
        maxW: Math.min(widgetSize.maxW || 12, 12),
        maxH: Math.min(widgetSize.maxH || 8, 8),
        isDraggable: true,
        isResizable: true,
      };
    });
  }, []);

  // Improved responsive layout generation with better breakpoint handling
  const generateResponsiveLayouts = useCallback(baseLayout => {
    if (!baseLayout || baseLayout.length === 0) return {};

    const breakpoints = {
      lg: { cols: 12, minW: 2, maxW: 12 },
      md: { cols: 10, minW: 2, maxW: 8 },
      sm: { cols: 6, minW: 2, maxW: 6 },
      xs: { cols: 4, minW: 2, maxW: 4 },
      xxs: { cols: 2, minW: 2, maxW: 2 },
    };

    const layouts = { lg: baseLayout };

    // Generate layouts for other breakpoints
    Object.keys(breakpoints).forEach(breakpoint => {
      if (breakpoint === 'lg') return;

      const { cols, minW, maxW } = breakpoints[breakpoint];

      layouts[breakpoint] = baseLayout.map(item => {
        // Calculate responsive width while maintaining aspect ratio
        const aspectRatio = item.h / item.w;
        let newW = Math.max(Math.min(Math.floor(item.w * (cols / 12)), maxW), minW);
        let newH = Math.max(Math.floor(newW * aspectRatio), 2);

        // For very small screens, stack widgets vertically
        if (breakpoint === 'xxs') {
          newW = 2;
          newH = Math.max(item.h, 2);
        }

        return {
          ...item,
          w: newW,
          h: newH,
          minW: minW,
          minH: 2,
          maxW: maxW,
          maxH: breakpoint === 'xxs' ? 6 : 8,
        };
      });
    });

    return layouts;
  }, []);

  // Convert widget sizes to grid layout format
  const defaultLayout = getDefaultLayout(state.widgets);

  // Use existing layout only if it's valid and matches current widgets
  const isLayoutValid =
    state.layout &&
    state.layout.length > 0 &&
    state.layout.length === state.widgets.length &&
    state.widgets.every(widget => state.layout.some(layoutItem => layoutItem.i === widget.id));

  const layouts = {
    lg: isLayoutValid ? state.layout : defaultLayout,
  };

  // Generate layouts for all breakpoints with improved responsive behavior
  const allLayouts = generateResponsiveLayouts(layouts.lg);

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
        rowHeight={120}
        margin={[20, 20]}
        containerPadding={[20, 20]}
        isDraggable={state.isEditing}
        isResizable={state.isEditing}
        onLayoutChange={handleLayoutChange}
        onDragStop={handleDragStop}
        onResizeStop={handleResizeStop}
        onBreakpointChange={handleBreakpointChange}
        draggableHandle=".widget-drag-handle"
        resizeHandles={['se', 'sw', 'ne', 'nw', 's', 'n', 'e', 'w']}
        compactType="vertical"
        preventCollision={true}
        useCSSTransforms={true}
        autoSize={true}
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
          const animationStyle = {
            animation: `fadeIn 0.6s ease-out ${index * 0.1}s both`,
          };
          const retryKey = widgetRetryKeys[widget.id] || 0;

          return (
            <div key={widget.id} className="dashboard-widget" style={animationStyle}>
              <WidgetErrorBoundary
                key={`${widget.id}-${retryKey}`}
                widgetTitle={widget.title}
                onRetry={() => handleWidgetRetry(widget.id)}
              >
                <WidgetComponent
                  id={widget.id}
                  title={widget.title}
                  config={widget.config}
                  key={`${widget.id}-content-${retryKey}`}
                />
              </WidgetErrorBoundary>
            </div>
          );
        })}
      </ResponsiveGridLayout>
    </div>
  );
};
