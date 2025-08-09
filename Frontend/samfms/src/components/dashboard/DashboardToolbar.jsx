import React, { useState } from 'react';
import { Plus, Edit3, RotateCcw, X } from 'lucide-react';
import { useDashboard } from '../../contexts/DashboardContext';
import { WidgetLibrary } from './WidgetLibrary';
import './dashboard.css';

export const DashboardToolbar = () => {
  const { state, dispatch } = useDashboard();
  const [showWidgetLibrary, setShowWidgetLibrary] = useState(false);

  const toggleEditMode = () => {
    dispatch({
      type: 'SET_EDIT_MODE',
      payload: !state.isEditing,
    });
  };

  const resetLayout = () => {
    // Create a default layout for existing widgets
    const defaultLayout = state.widgets.map((widget, index) => ({
      i: widget.id,
      x: (index % 3) * 4, // 3 widgets per row, each 4 columns wide
      y: Math.floor(index / 3) * 4, // Each row is 4 units tall
      w: 4, // Default width
      h: 4, // Default height
    }));

    dispatch({
      type: 'RESET_LAYOUT',
      payload: defaultLayout,
    });
  };

  return (
    <>
      <div className="border-b border-gray-200 bg-white/80 backdrop-blur-sm shadow-sm relative">
        <div className="flex items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold m-0 text-gray-900 tracking-tight">Fleet Dashboard</h1>
            {state.isEditing && (
              <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 animate-pulse">
                Edit Mode
              </span>
            )}
          </div>

          <div className="flex items-center gap-3">
            <button
              className={`group flex items-center gap-2 px-4 py-2.5 border rounded-lg cursor-pointer text-sm font-medium transition-all duration-200 transform hover:scale-105 focus:ring-2 focus:ring-offset-2 ${
                state.isEditing
                  ? 'bg-red-600 border-red-600 text-white hover:bg-red-700 hover:shadow-lg focus:ring-red-500 shadow-md'
                  : 'bg-white border-gray-300 text-gray-800 hover:bg-gray-50 hover:border-gray-400 hover:shadow-md focus:ring-blue-500'
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
              <div className="flex items-center gap-2 animate-in slide-in-from-right-5 duration-300">
                <button
                  className="group flex items-center gap-2 px-4 py-2.5 bg-blue-600 text-white border-none rounded-lg cursor-pointer text-sm font-medium transition-all duration-200 transform hover:scale-105 hover:bg-blue-700 hover:shadow-lg focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 shadow-md"
                  onClick={() => setShowWidgetLibrary(true)}
                >
                  <Plus
                    size={16}
                    className="transition-transform duration-200 group-hover:rotate-90"
                  />
                  <span className="hidden sm:inline">Add Widget</span>
                </button>
                <button
                  className="group flex items-center gap-2 px-4 py-2.5 bg-gray-600 text-white border-none rounded-lg cursor-pointer text-sm font-medium transition-all duration-200 transform hover:scale-105 hover:bg-gray-700 hover:shadow-lg focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 shadow-md"
                  onClick={resetLayout}
                >
                  <RotateCcw
                    size={16}
                    className="transition-transform duration-200 group-hover:rotate-180"
                  />
                  <span className="hidden sm:inline">Reset</span>
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
