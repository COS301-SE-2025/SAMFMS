import React, { useState } from 'react';
import { Edit3, Plus, Save, RotateCcw } from 'lucide-react';
import { useDashboard } from '../../contexts/DashboardContext';
import { WidgetLibrary } from './WidgetLibrary';

export const DashboardToolbar = () => {
  const { state, dispatch } = useDashboard();
  const [showWidgetLibrary, setShowWidgetLibrary] = useState(false);

  const toggleEditMode = () => {
    dispatch({ type: 'SET_EDITING_MODE', payload: !state.isEditing });
  };

  const handleResetToDefault = () => {
    if (
      window.confirm(
        'Are you sure you want to reset the dashboard to default layout? This will remove all current widgets and restore the default dashboard.'
      )
    ) {
      dispatch({ type: 'RESET_TO_DEFAULT' });
    }
  };

  return (
    <>
      <div className="flex items-center justify-between p-4 border-b border-border">
        <div>
          <h1 className="text-2xl font-bold">Fleet Dashboard</h1>
          {state.isEditing && (
            <p className="text-sm text-muted-foreground">
              Editing mode - Drag, resize, and configure widgets
            </p>
          )}
        </div>

        <div className="flex items-center gap-2">
          {state.isEditing && (
            <>
              <button
                onClick={() => setShowWidgetLibrary(true)}
                className="flex items-center gap-2 px-3 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
              >
                <Plus size={16} />
                Add Widget
              </button>

              <button
                onClick={handleResetToDefault}
                className="flex items-center gap-2 px-3 py-2 border border-input rounded-md hover:bg-accent hover:text-accent-foreground"
                disabled={state.widgets.length === 0}
              >
                <RotateCcw size={16} />
                Reset to Default
              </button>
            </>
          )}

          <button
            onClick={toggleEditMode}
            className={`flex items-center gap-2 px-3 py-2 rounded-md transition-colors ${
              state.isEditing
                ? 'bg-green-600 text-white hover:bg-green-700'
                : 'border border-input hover:bg-accent hover:text-accent-foreground'
            }`}
          >
            {state.isEditing ? (
              <>
                <Save size={16} />
                Save & Exit
              </>
            ) : (
              <>
                <Edit3 size={16} />
                Edit Dashboard
              </>
            )}
          </button>
        </div>
      </div>

      <WidgetLibrary isOpen={showWidgetLibrary} onClose={() => setShowWidgetLibrary(false)} />
    </>
  );
};
