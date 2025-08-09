import React, { useEffect } from 'react';
import { DashboardProvider, useDashboard } from '../contexts/DashboardContext';
import { DashboardToolbar } from '../components/dashboard/DashboardToolbar';
import { DashboardCanvas } from '../components/dashboard/DashboardCanvas';

// Import widgets to ensure they're registered
import '../components/widgets';
import '../components/dashboard/dashboard.css';

const DashboardContent = () => {
  const { state, dispatch, saveDashboardManually } = useDashboard();

  useEffect(() => {
    // Handle automatic save and exit edit mode when leaving the dashboard
    const handleBeforeUnload = () => {
      if (state.isEditing) {
        // Save the dashboard
        saveDashboardManually();
        // Exit edit mode
        dispatch({
          type: 'SET_EDIT_MODE',
          payload: false,
        });
      }
    };

    // Handle navigation away from the dashboard
    const handleUnload = () => {
      handleBeforeUnload();
    };

    // Add event listeners
    window.addEventListener('beforeunload', handleBeforeUnload);
    window.addEventListener('unload', handleUnload);

    // Cleanup function
    return () => {
      // Auto-save and exit edit mode when component unmounts
      handleBeforeUnload();

      // Remove event listeners
      window.removeEventListener('beforeunload', handleBeforeUnload);
      window.removeEventListener('unload', handleUnload);
    };
  }, [state.isEditing, dispatch, saveDashboardManually]);

  return (
    <div className="min-h-screen bg-gray-50">
      <DashboardToolbar />
      <DashboardCanvas />
    </div>
  );
};

const Dashboard = () => {
  return (
    <DashboardProvider dashboardId="main">
      <DashboardContent />
    </DashboardProvider>
  );
};

export default Dashboard;
