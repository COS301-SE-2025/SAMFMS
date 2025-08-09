import React from 'react';
import { DashboardProvider } from '../contexts/DashboardContext';
import { DashboardToolbar } from '../components/dashboard/DashboardToolbar';
import { DashboardCanvas } from '../components/dashboard/DashboardCanvas';

// Import widgets to ensure they're registered
import '../components/widgets';
import '../components/dashboard/dashboard.css';

const Dashboard = () => {
  return (
    <DashboardProvider dashboardId="main">
      <div className="min-h-screen bg-gray-50">
        <DashboardToolbar />
        <DashboardCanvas />
      </div>
    </DashboardProvider>
  );
};

export default Dashboard;
