import React, { useState, useCallback } from 'react';
import { Settings, X, Maximize2, Minimize2, GripVertical } from 'lucide-react';
import { useDashboard } from '../../contexts/DashboardContext';

export const BaseWidget = ({
  id,
  title,
  children,
  config = {},
  onConfigChange,
  allowResize = true,
  allowRemove = true,
  className = '',
  loading = false,
  error = null,
}) => {
  const { state, dispatch } = useDashboard();
  const [isConfigOpen, setIsConfigOpen] = useState(false);
  const [isMaximized, setIsMaximized] = useState(false);

  const handleRemove = useCallback(() => {
    dispatch({ type: 'REMOVE_WIDGET', payload: id });
  }, [dispatch, id]);

  const handleConfigSave = useCallback(
    newConfig => {
      dispatch({
        type: 'UPDATE_WIDGET_CONFIG',
        payload: { id, config: newConfig },
      });
      if (onConfigChange) onConfigChange(newConfig);
      setIsConfigOpen(false);
    },
    [dispatch, id, onConfigChange]
  );

  if (loading) {
    return (
      <div
        className={`bg-card border border-border rounded-lg shadow-sm overflow-hidden h-full flex flex-col ${className}`}
      >
        <div className="flex items-center justify-between p-3 border-b border-border bg-card/50 flex-shrink-0">
          <h3 className="font-medium text-card-foreground truncate">{title}</h3>
          {state.isEditing && (
            <div className="widget-drag-handle cursor-move p-1 hover:bg-muted rounded">
              <GripVertical size={16} />
            </div>
          )}
        </div>
        <div className="p-4 flex items-center justify-center flex-grow">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          <span className="ml-3 text-muted-foreground">Loading...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div
        className={`bg-card border border-border rounded-lg shadow-sm overflow-hidden h-full flex flex-col ${className}`}
      >
        <div className="flex items-center justify-between p-3 border-b border-border bg-card/50 flex-shrink-0">
          <h3 className="font-medium text-card-foreground truncate">{title}</h3>
          {state.isEditing && (
            <div className="flex items-center gap-1">
              <div className="widget-drag-handle cursor-move p-1 hover:bg-muted rounded">
                <GripVertical size={16} />
              </div>
              {allowRemove && (
                <button
                  onClick={handleRemove}
                  className="p-1 hover:bg-destructive hover:text-destructive-foreground rounded"
                  title="Remove Widget"
                >
                  <X size={16} />
                </button>
              )}
            </div>
          )}
        </div>
        <div className="p-4 flex-grow flex items-center justify-center">
          <div className="bg-destructive/10 border border-destructive text-destructive rounded-md p-3 w-full">
            <p className="font-medium">Error</p>
            <p className="text-sm mt-1">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`bg-card border border-border rounded-lg shadow-sm overflow-hidden h-full flex flex-col ${className}`}
    >
      {/* Widget Header */}
      <div className="flex items-center justify-between p-3 border-b border-border bg-card/50 flex-shrink-0">
        <h3 className="font-medium text-card-foreground truncate">{title}</h3>

        {state.isEditing && (
          <div className="flex items-center gap-1">
            <button
              onClick={() => setIsConfigOpen(true)}
              className="p-1 hover:bg-muted rounded"
              title="Widget Settings"
            >
              <Settings size={16} />
            </button>

            <button
              onClick={() => setIsMaximized(!isMaximized)}
              className="p-1 hover:bg-muted rounded"
              title={isMaximized ? 'Minimize' : 'Maximize'}
            >
              {isMaximized ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
            </button>

            {allowRemove && (
              <button
                onClick={handleRemove}
                className="p-1 hover:bg-destructive hover:text-destructive-foreground rounded"
                title="Remove Widget"
              >
                <X size={16} />
              </button>
            )}

            <div className="widget-drag-handle cursor-move p-1 hover:bg-muted rounded">
              <GripVertical size={16} />
            </div>
          </div>
        )}
      </div>

      {/* Widget Content */}
      <div className="p-4 flex-grow overflow-hidden min-h-[100px]">{children}</div>

      {/* Configuration Modal */}
      {isConfigOpen && (
        <WidgetConfigModal
          config={config}
          onSave={handleConfigSave}
          onClose={() => setIsConfigOpen(false)}
        />
      )}
    </div>
  );
};

// Simple configuration modal component
const WidgetConfigModal = ({ config, onSave, onClose }) => {
  const [localConfig, setLocalConfig] = useState(config);

  const handleSave = () => {
    onSave(localConfig);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-background rounded-lg shadow-xl w-full max-w-md">
        <div className="p-4 border-b border-border">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">Widget Settings</h3>
            <button onClick={onClose} className="hover:bg-muted rounded p-1">
              <X size={20} />
            </button>
          </div>
        </div>
        <div className="p-4">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Widget Title</label>
              <input
                type="text"
                className="w-full px-3 py-2 border border-input rounded-md"
                value={localConfig.title || ''}
                onChange={e => setLocalConfig(prev => ({ ...prev, title: e.target.value }))}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Refresh Interval (seconds)</label>
              <input
                type="number"
                className="w-full px-3 py-2 border border-input rounded-md"
                value={localConfig.refreshInterval || 30}
                onChange={e =>
                  setLocalConfig(prev => ({ ...prev, refreshInterval: parseInt(e.target.value) }))
                }
                min="5"
              />
            </div>
          </div>
        </div>
        <div className="p-4 border-t border-border flex justify-end gap-2">
          <button
            onClick={onClose}
            className="px-4 py-2 border border-input rounded-md hover:bg-accent hover:text-accent-foreground"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );
};
