import React, { useEffect } from 'react';
import { DashboardProvider, useDashboard } from '../contexts/DashboardContext';
import { DashboardToolbar } from '../components/dashboard/DashboardToolbar';
import { DashboardCanvas } from '../components/dashboard/DashboardCanvas';

// Import widgets to ensure they're registered
import '../components/widgets';
import '../components/dashboard/dashboard.css';

// Dashboard component that initializes with defaults if empty
const DashboardContent = () => {
  const { state, dispatch } = useDashboard();

  useEffect(() => {
    // Initialize with default dashboard if empty and no saved data
    if (state.widgets.length === 0) {
      const savedDashboard = localStorage.getItem('dashboard_main');
      if (!savedDashboard) {
        dispatch({ type: 'RESET_TO_DEFAULT' });
      }
    }
  }, [state.widgets.length, dispatch]);

  return (
    <div className="min-h-screen bg-background">
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
