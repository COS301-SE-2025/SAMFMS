import React, { useState } from 'react';
import { Responsive, WidthProvider } from 'react-grid-layout';
import { Trash2 } from 'lucide-react';
import { useDashboard } from '../../contexts/DashboardContext';
import { getWidget } from '../../utils/widgetRegistry';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';
import './dashboard.css';

const ResponsiveGridLayout = WidthProvider(Responsive);

export const DashboardCanvas = () => {
  const { state, dispatch } = useDashboard();
  const [isDraggingWidget, setIsDraggingWidget] = useState(false);
  const [dragOverTrash, setDragOverTrash] = useState(false);
  const [draggingWidgetId, setDraggingWidgetId] = useState(null);
  const [newWidgetIds, setNewWidgetIds] = useState(new Set());
  const prevWidgetIds = React.useRef([]);

  // Clear new widget IDs after animation
  React.useEffect(() => {
    if (newWidgetIds.size > 0) {
      const timer = setTimeout(() => {
        setNewWidgetIds(new Set());
      }, 500); // Match animation duration
      return () => clearTimeout(timer);
    }
  }, [newWidgetIds]);

  // Track new widgets
  React.useEffect(() => {
    const currentWidgetIds = state.widgets.map(w => w.id);

    const addedWidgets = currentWidgetIds.filter(id => !prevWidgetIds.current.includes(id));
    if (addedWidgets.length > 0) {
      setNewWidgetIds(new Set(addedWidgets));
    }

    prevWidgetIds.current = currentWidgetIds;
  }, [state.widgets]);

  // Simple default layout - no overlapping
  const getDefaultLayout = widgets => {
    return widgets.map((widget, index) => ({
      i: widget.id,
      x: (index % 5) * 8, // 5 widgets per row, each 8 columns wide
      y: Math.floor(index / 5) * 6, // Each row is 6 units tall for more spacing
      w: 8, // Default width (increased for better proportion with 40 columns)
      h: 6, // Default height (increased for better visibility)
    }));
  };

  const handleLayoutChange = layouts => {
    if (state.isEditing) {
      dispatch({
        type: 'UPDATE_LAYOUT',
        payload: layouts,
      });
    }
  };

  const handleDragStart = (layout, oldItem) => {
    if (state.isEditing) {
      setIsDraggingWidget(true);
      setDraggingWidgetId(oldItem.i);
    }
  };

  const handleDragStop = (layout, oldItem, newItem) => {
    // Check if the widget was dropped over the trash zone
    if (dragOverTrash && draggingWidgetId) {
      // Remove the widget instead of updating layout
      dispatch({ type: 'REMOVE_WIDGET', payload: draggingWidgetId });
    } else {
      // Normal drag - update layout
      if (state.isEditing) {
        dispatch({
          type: 'UPDATE_LAYOUT',
          payload: layout,
        });
      }
    }

    // Reset drag states
    setIsDraggingWidget(false);
    setDraggingWidgetId(null);
    setDragOverTrash(false);
  };

  const handleResizeStart = (layout, oldItem, newItem, placeholder) => {
    // Optional: Add any resize start logic here
  };

  const handleResizeStop = (layout, oldItem, newItem, placeholder) => {
    // Update layout after resize to ensure accommodation
    if (state.isEditing) {
      dispatch({
        type: 'UPDATE_LAYOUT',
        payload: layout,
      });
    }
  };

  const handleTrashMouseEnter = () => {
    if (isDraggingWidget && draggingWidgetId) {
      setDragOverTrash(true);
    }
  };

  const handleTrashMouseLeave = () => {
    setDragOverTrash(false);
  }; // Simple layouts object for responsive grid
  const layouts = {
    lg: state.layout || getDefaultLayout(state.widgets),
  };

  return (
    <div className={`w-full min-h-screen overflow-auto transition-all duration-300 ease-out`}>
      <ResponsiveGridLayout
        className={`min-h-[300vh] bg-none transition-all duration-300 ease-out ${
          state.isEditing ? 'edit-mode' : ''
        }`}
        layouts={layouts}
        breakpoints={{ lg: 1200 }}
        cols={{ lg: 40 }}
        rowHeight={30}
        onLayoutChange={layout => handleLayoutChange(layout)}
        onDragStart={handleDragStart}
        onDragStop={handleDragStop}
        onResizeStart={handleResizeStart}
        onResizeStop={handleResizeStop}
        isDraggable={state.isEditing}
        isResizable={state.isEditing}
        preventCollision={false} // Allow widgets to push others around
        compactType="vertical" // Enable vertical compaction for better accommodation
        margin={[8, 8]} // Reduced margin for tighter spacing
        resizeHandles={['se', 'sw', 'ne', 'nw', 's', 'n', 'e', 'w']}
        useCSSTransforms={true} // Enable smooth CSS transforms for better drag experience
        transformScale={1} // Ensure proper scaling
        verticalCompact={true} // Enable vertical compaction
        autoSize={true} // Auto-resize container
        isBounded={false} // Allow widgets to be dragged outside bounds temporarily
        allowOverlap={false} // Prevent overlapping
        draggableHandle="" // Allow dragging from anywhere on the widget
        draggableCancel=".no-drag" // Prevent dragging from elements with this class
        droppingItem={{ i: '__dropping-elem__', h: 2, w: 2 }} // Configure dropping item
        isDroppable={true} // Enable dropping
      >
        {state.widgets.map(widget => {
          const widgetDefinition = getWidget(widget.type);
          if (!widgetDefinition || !widgetDefinition.component) return null;

          const WidgetComponent = widgetDefinition.component;
          const isDragging = draggingWidgetId === widget.id;
          const isNewWidget = newWidgetIds.has(widget.id);

          return (
            <div
              key={widget.id}
              className={`bg-white/90 backdrop-blur-sm rounded-md shadow-sm h-full transition-all duration-200 ease-out ${
                state.isEditing
                  ? 'cursor-grab active:cursor-grabbing hover:shadow-md hover:-translate-y-0.5 hover:bg-white/95 hover:scale-[1.02]'
                  : 'hover:shadow-md hover:-translate-y-1 hover:scale-[1.01]'
              } ${
                isDragging
                  ? 'shadow-2xl scale-105 rotate-1 z-50 bg-white/95 ring-2 ring-blue-500/30'
                  : ''
              } ${isNewWidget ? 'new-widget' : ''}`}
            >
              <div
                className={`h-full overflow-auto transition-all duration-200 ${
                  isDragging ? 'pointer-events-none' : ''
                }`}
              >
                <WidgetComponent {...widget.config} />
              </div>
            </div>
          );
        })}
      </ResponsiveGridLayout>

      {/* Trash Drop Zone - only visible in edit mode */}
      {state.isEditing && (
        <div
          className={`fixed bottom-7 right-7 border-2 border-dashed rounded-xl flex flex-col items-center justify-center text-sm font-medium z-[9999] pointer-events-none transition-all duration-300 ease-out transform backdrop-blur-sm ${
            isDraggingWidget
              ? 'opacity-90 scale-100 pointer-events-auto translate-y-0 shadow-2xl'
              : 'opacity-0 scale-75 translate-y-4'
          } ${
            dragOverTrash
              ? 'border-red-400 bg-red-500/90 text-white scale-110 shadow-2xl shadow-red-500/40 animate-pulse ring-4 ring-red-500/30'
              : 'border-red-300 bg-red-50/80 text-red-700 hover:bg-red-100/90'
          }`}
          style={{ width: '140px', height: '100px' }}
          onMouseEnter={handleTrashMouseEnter}
          onMouseLeave={handleTrashMouseLeave}
        >
          <Trash2
            size={28}
            className={`transition-transform duration-200 ${
              dragOverTrash ? 'scale-110 animate-bounce' : 'scale-100'
            }`}
          />
          <span
            className={`mt-2 text-center px-2 transition-all duration-200 ${
              dragOverTrash ? 'font-bold text-xs' : 'text-xs'
            }`}
          >
            {dragOverTrash ? 'Release to Delete!' : 'Drop here to delete'}
          </span>
        </div>
      )}
    </div>
  );
};
