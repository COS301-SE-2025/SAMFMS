import React, {useEffect} from 'react';
import {DashboardProvider, useDashboard} from '../contexts/DashboardContext';
import {DashboardToolbar} from '../components/dashboard/DashboardToolbar';
import {DashboardCanvas} from '../components/dashboard/DashboardCanvas';

// Import widgets to ensure they're registered
import '../components/widgets';
import '../components/dashboard/dashboard.css';

const DashboardContent = () => {
  const {state, dispatch, saveDashboardManually} = useDashboard();

  useEffect(() => {
    // Handle automatic save when leaving the dashboard (but don't exit edit mode)
    const handleBeforeUnload = (event) => {
      // Only save, don't exit edit mode automatically to prevent issues during drag operations
      if (state.isEditing) {
        saveDashboardManually();
      }
    };

    // Add event listeners
    window.addEventListener('beforeunload', handleBeforeUnload);

    // Cleanup function
    return () => {
      // Auto-save when component unmounts
      if (state.isEditing) {
        saveDashboardManually();
      }

      // Remove event listeners
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [state.isEditing, saveDashboardManually]);

  return (
    <div className="min-h-screen">
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
