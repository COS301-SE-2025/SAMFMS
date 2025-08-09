import React, { useEffect } from 'react';
import { DashboardProvider, useDashboard } from '../contexts/DashboardContext';
import { DashboardToolbar } from '../components/dashboard/DashboardToolbar';
import { DashboardCanvas } from '../components/dashboard/DashboardCanvas';
import { preloadWidgetBatch } from '../utils/lazyWidgetLoader';
import { preloadWidgetData } from '../utils/widgetDataManager';

// Import widgets to ensure they're registered
import '../components/widgets';
import '../components/dashboard/dashboard.css';

// Widget import functions for lazy loading
const widgetImports = [
  () => import('../components/widgets/MaintenanceSummaryWidget'),
  () => import('../components/widgets/VehicleStatusWidget'),
  () => import('../components/widgets/MaintenanceAlertsWidget'),
  () => import('../components/widgets/MaintenanceRecordsWidget'),
  () => import('../components/widgets/MaintenanceCostAnalyticsWidget'),
];

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

  // Preload widgets for better performance
  useEffect(() => {
    const preloadWidgets = async () => {
      try {
        // Preload widget components
        await preloadWidgetBatch(widgetImports, 2, 500);

        // Preload widget data for better perceived performance
        if (state.widgets.length > 0) {
          const fetchers = {}; // Add your widget data fetchers here
          await preloadWidgetData(state.widgets, fetchers);
        }
      } catch (error) {
        console.warn('Widget preloading failed:', error);
      }
    };

    // Delay preloading to not interfere with initial render
    const timeoutId = setTimeout(preloadWidgets, 1000);
    return () => clearTimeout(timeoutId);
  }, [state.widgets]);

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
