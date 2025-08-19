import React, {useState, useCallback} from 'react';
import {X, GripVertical} from 'lucide-react';
import {useDashboard} from '../../contexts/DashboardContext';

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
  const {state, dispatch} = useDashboard();
  const [isConfigOpen, setIsConfigOpen] = useState(false);

  const handleRemove = useCallback(() => {
    dispatch({type: 'REMOVE_WIDGET', payload: id});
  }, [dispatch, id]);

  const handleConfigSave = useCallback(
    newConfig => {
      dispatch({
        type: 'UPDATE_WIDGET_CONFIG',
        payload: {id, config: newConfig},
      });
      if (onConfigChange) onConfigChange(newConfig);
      setIsConfigOpen(false);
    },
    [dispatch, id, onConfigChange]
  );

  // Keyboard event handlers for accessibility
  const handleKeyDown = useCallback(
    e => {
      if (!state.isEditing) return;

      switch (e.key) {
        case 'Delete':
        case 'Backspace':
          if (allowRemove && e.target === e.currentTarget) {
            handleRemove();
          }
          break;
        case 'Enter':
        case ' ':
          if (e.target.classList.contains('widget-config-button')) {
            setIsConfigOpen(true);
          }
          break;
        default:
          break;
      }
    },
    [state.isEditing, allowRemove, handleRemove]
  );

  if (loading) {
    return (
      <div
        className={`bg-card shadow-sm overflow-hidden h-full flex flex-col ${className}`}
        role="region"
        aria-label={`${title} - Loading`}
        aria-busy="true"
      >
        <div className="flex items-center justify-between p-3 border-b border-border bg-gradient-to-r from-slate-100/50 to-slate-50/50 dark:from-slate-900/50 dark:to-slate-950/50 flex-shrink-0">
          <h3 className="font-medium text-card-foreground truncate" id={`widget-title-${id}`}>
            {title}
          </h3>
          {state.isEditing && (
            <div
              className="widget-drag-handle cursor-move p-1 hover:bg-muted rounded"
              tabIndex={0}
              role="button"
              aria-label={`Drag ${title} widget`}
            >
              <GripVertical size={16} aria-hidden="true" />
            </div>
          )}
        </div>
        <div className="p-4 flex items-center justify-center flex-grow" role="status">
          <div
            className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"
            aria-hidden="true"
          ></div>
          <span className="ml-3 text-muted-foreground">Loading...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div
        className={`bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 border-slate-100 dark:border-slate-900 border rounded-xl shadow-lg overflow-hidden h-full flex flex-col ${className}`}
        role="region"
        aria-label={`${title} - Error`}
        aria-describedby={`error-desc-${id}`}
      >
        <div className="flex items-center justify-between border-b border-border bg-gradient-to-r from-slate-100/50 to-slate-50/50 dark:from-slate-900/50 dark:to-slate-950/50 flex-shrink-0">
          <h3 className="font-medium text-card-foreground truncate" id={`widget-title-${id}`}>
            {title}
          </h3>
          {state.isEditing && (
            <div className="flex items-center gap-1">
              <div
                className="widget-drag-handle cursor-move p-1 hover:bg-muted rounded"
                tabIndex={0}
                role="button"
                aria-label={`Drag ${title} widget`}
              >
                <GripVertical size={16} aria-hidden="true" />
              </div>
              {allowRemove && (
                <button
                  onClick={handleRemove}
                  className="p-1 hover:bg-destructive hover:text-destructive-foreground rounded"
                  title={`Remove ${title} widget`}
                  aria-label={`Remove ${title} widget`}
                >
                  <X size={16} aria-hidden="true" />
                </button>
              )}
            </div>
          )}
        </div>
        <div className="p-4 flex-grow flex items-center justify-center">
          <div
            className="bg-destructive/10 border border-destructive text-destructive rounded-md p-3 w-full"
            role="alert"
          >
            <p className="font-medium">Error</p>
            <p className="text-sm mt-1" id={`error-desc-${id}`}>
              {error}
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 border-slate-100 dark:border-slate-900 border rounded-xl shadow-lg overflow-hidden h-full flex flex-col ${className}`}
      role="region"
      aria-labelledby={`widget-title-${id}`}
      tabIndex={state.isEditing ? 0 : -1}
      onKeyDown={handleKeyDown}
    >
      {/* Widget Content */}
      <div className="p-3 flex-grow overflow-hidden min-h-[100px]" role="main">
        {children}
      </div>

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

// Enhanced configuration modal component with validation
const WidgetConfigModal = ({config, onSave, onClose}) => {
  const [localConfig, setLocalConfig] = useState(config);
  const [validationErrors, setValidationErrors] = useState({});

  // Validate configuration
  const validateConfig = configData => {
    const errors = {};

    if (configData.title && configData.title.trim().length === 0) {
      errors.title = 'Title cannot be empty';
    }

    if (configData.title && configData.title.length > 50) {
      errors.title = 'Title cannot exceed 50 characters';
    }

    const refreshInterval = parseInt(configData.refreshInterval);
    if (isNaN(refreshInterval) || refreshInterval < 5) {
      errors.refreshInterval = 'Refresh interval must be at least 5 seconds';
    }

    if (refreshInterval > 3600) {
      errors.refreshInterval = 'Refresh interval cannot exceed 1 hour';
    }

    return errors;
  };

  const handleSave = () => {
    const errors = validateConfig(localConfig);
    setValidationErrors(errors);

    if (Object.keys(errors).length === 0) {
      onSave(localConfig);
    }
  };

  const handleInputChange = (field, value) => {
    setLocalConfig(prev => ({...prev, [field]: value}));

    // Clear validation error when user starts typing
    if (validationErrors[field]) {
      setValidationErrors(prev => {
        const newErrors = {...prev};
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-background shadow-xl w-full max-w-md">
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
                className={`w-full px-3 py-2 border rounded-md ${validationErrors.title ? 'border-destructive' : 'border-input'
                  }`}
                value={localConfig.title || ''}
                onChange={e => handleInputChange('title', e.target.value)}
                placeholder="Enter widget title"
              />
              {validationErrors.title && (
                <p className="text-destructive text-sm mt-1">{validationErrors.title}</p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Refresh Interval (seconds)</label>
              <input
                type="number"
                className={`w-full px-3 py-2 border rounded-md ${validationErrors.refreshInterval ? 'border-destructive' : 'border-input'
                  }`}
                value={localConfig.refreshInterval || 30}
                onChange={e => handleInputChange('refreshInterval', parseInt(e.target.value))}
                min="5"
                max="3600"
              />
              {validationErrors.refreshInterval && (
                <p className="text-destructive text-sm mt-1">{validationErrors.refreshInterval}</p>
              )}
              <p className="text-muted-foreground text-xs mt-1">
                How often the widget should refresh its data (5-3600 seconds)
              </p>
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
            disabled={Object.keys(validationErrors).length > 0}
          >
            Save Changes
          </button>
        </div>
      </div>
    </div>
  );
};
