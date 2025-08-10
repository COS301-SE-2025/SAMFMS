import React, { useState, useEffect } from 'react';
import { Plus, Edit3, X, Save, RefreshCw } from 'lucide-react';
import { useDashboard } from '../../contexts/DashboardContext';
import { WidgetLibrary } from './WidgetLibrary';
import './dashboard.css';

export const DashboardToolbar = () => {
  const { state, dispatch, saveDashboardManually, resetDashboard } = useDashboard();
  const [showWidgetLibrary, setShowWidgetLibrary] = useState(false);
  const [saveStatus, setSaveStatus] = useState(''); // '', 'saved', 'saving', 'error'

  const toggleEditMode = () => {
    dispatch({
      type: 'SET_EDIT_MODE',
      payload: !state.isEditing,
    });
  };

  const handleManualSave = async () => {
    setSaveStatus('saving');
    const success = saveDashboardManually();
    setSaveStatus(success ? 'saved' : 'error');

    if (success) {
      // Hide saved indicator after 5 seconds
      setTimeout(() => setSaveStatus(''), 5000);
    }
  };

  const handleResetDashboard = () => {
    if (
      window.confirm(
        'Are you sure you want to reset the dashboard to default? This will remove all customizations.'
      )
    ) {
      setSaveStatus('saving');
      const success = resetDashboard();
      setSaveStatus(success ? 'saved' : 'error');

      if (success) {
        // Hide saved indicator after 5 seconds
        setTimeout(() => setSaveStatus(''), 5000);
      }
    }
  };

  // Show save status indicator
  useEffect(() => {
    if (saveStatus === 'error') {
      const timer = setTimeout(() => setSaveStatus(''), 5000);
      return () => clearTimeout(timer);
    }
  }, [saveStatus]);

  return (
    <>
      <div className="relative">
        <div className="flex items-center justify-between px-4 md:px-6 py-4 gap-4">
          <div className="flex items-center gap-3 min-w-0 flex-1">
            <h1 className="text-xl md:text-2xl font-bold m-0 text-foreground tracking-tight truncate">
              Fleet Dashboard
            </h1>
            <div className="flex items-center gap-2">
              {state.isEditing && (
                <span className="inline-flex items-center px-2 md:px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 animate-pulse whitespace-nowrap">
                  Edit Mode
                </span>
              )}
              {/* Save Status Indicator */}
              {saveStatus && (
                <span
                  className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium transition-all duration-200 whitespace-nowrap ${
                    saveStatus === 'saved'
                      ? 'bg-green-100 text-green-800'
                      : saveStatus === 'saving'
                      ? 'bg-yellow-100 text-yellow-800'
                      : 'bg-red-100 text-red-800'
                  }`}
                >
                  {saveStatus === 'saved' && '✓ Saved'}
                  {saveStatus === 'saving' && (
                    <>
                      <RefreshCw size={12} className="mr-1 animate-spin" />
                      Saving...
                    </>
                  )}
                  {saveStatus === 'error' && '⚠ Save Failed'}
                </span>
              )}
            </div>
          </div>

          <div className="flex items-center gap-2 md:gap-3 flex-shrink-0">
            <button
              className={`group flex items-center gap-2 px-3 py-2 md:px-4 md:py-2.5 border rounded-lg cursor-pointer text-sm font-medium transition-all duration-200 transform hover:scale-105 focus:ring-2 focus:ring-offset-2 ${
                state.isEditing
                  ? 'bg-red-600 border-red-600 text-white hover:bg-red-700 hover:shadow-lg focus:ring-red-500 shadow-md'
                  : 'bg-background border-border text-foreground hover:bg-accent hover:border-accent-foreground hover:shadow-md focus:ring-primary'
              }`}
              onClick={toggleEditMode}
              title={state.isEditing ? 'Exit Edit Mode' : 'Edit Dashboard'}
            >
              {state.isEditing ? (
                <X size={16} className="transition-transform duration-200 group-hover:rotate-90" />
              ) : (
                <Edit3
                  size={16}
                  className="transition-transform duration-200 group-hover:scale-110"
                />
              )}
              <span className="hidden sm:inline">{state.isEditing ? 'Done' : 'Edit'}</span>
            </button>

            {state.isEditing && (
              <div className="flex items-center gap-1 md:gap-2 animate-in slide-in-from-right-5 duration-300">
                <button
                  className="group flex items-center gap-2 px-3 py-2 md:px-4 md:py-2.5 bg-blue-600 text-white border-none rounded-lg cursor-pointer text-sm font-medium transition-all duration-200 transform hover:scale-105 hover:bg-blue-700 hover:shadow-lg focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 shadow-md"
                  onClick={() => setShowWidgetLibrary(true)}
                >
                  <Plus
                    size={16}
                    className="transition-transform duration-200 group-hover:rotate-90"
                  />
                  <span className="hidden sm:inline">Add Widget</span>
                </button>
                <button
                  className="group flex items-center gap-2 px-3 py-2 md:px-4 md:py-2.5 bg-green-600 text-white border-none rounded-lg cursor-pointer text-sm font-medium transition-all duration-200 transform hover:scale-105 hover:bg-green-700 hover:shadow-lg focus:ring-2 focus:ring-green-500 focus:ring-offset-2 shadow-md"
                  onClick={handleManualSave}
                  disabled={saveStatus === 'saving'}
                >
                  <Save
                    size={16}
                    className="transition-transform duration-200 group-hover:scale-110"
                  />
                  <span className="hidden sm:inline">Save</span>
                </button>
                <button
                  className="group flex items-center gap-2 px-3 py-2 md:px-4 md:py-2.5 bg-orange-600 text-white border-none rounded-lg cursor-pointer text-sm font-medium transition-all duration-200 transform hover:scale-105 hover:bg-orange-700 hover:shadow-lg focus:ring-2 focus:ring-orange-500 focus:ring-offset-2 shadow-md"
                  onClick={handleResetDashboard}
                >
                  <RefreshCw
                    size={16}
                    className="transition-transform duration-200 group-hover:rotate-180"
                  />
                  <span className="hidden sm:inline">Reset All</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>{' '}
      <WidgetLibrary isOpen={showWidgetLibrary} onClose={() => setShowWidgetLibrary(false)} />
    </>
  );
};
