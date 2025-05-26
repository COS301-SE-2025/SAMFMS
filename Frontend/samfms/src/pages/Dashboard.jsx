import React from 'react';
import { Button } from '../components/ui/button';
import ColorPalette from '../components/ColorPalette';

const Dashboard = () => {
  return (
    <div className="container mx-auto py-8">
      <header className="mb-8">
        <h1 className="text-4xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground">Welcome to your SAMFMS dashboard</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <DashboardCard
          title="Vehicle Status"
          content="All vehicles operational"
          footer="Last updated: Today at 10:00 AM"
        />
        <DashboardCard title="Active Trips" content="3 trips in progress" footer="View all trips" />
        <DashboardCard
          title="Maintenance"
          content="2 vehicles due for service"
          footer="Schedule maintenance"
        />
        <DashboardCard
          title="Fuel Usage"
          content="Average: 7.2L/100km"
          footer="View detailed reports"
        />
        <DashboardCard
          title="Driver Status"
          content="12 drivers available"
          footer="Manage drivers"
        />{' '}
        <DashboardCard title="Analytics" content="Fleet efficiency up 3%" footer="View analytics" />
      </div>

      <div className="mt-12 border-t border-border pt-8">
        <ColorPalette />
      </div>
    </div>
  );
};

// A simple card component for the dashboard
const DashboardCard = ({ title, content, footer }) => {
  return (
    <div className="bg-card rounded-lg shadow-md p-6 border border-border">
      <h2 className="text-xl font-semibold mb-4">{title}</h2>
      <p className="text-foreground mb-6">{content}</p>
      <div className="border-t border-border pt-4">
        <Button
          variant="ghost"
          className="p-0 h-auto text-sm text-muted-foreground hover:text-foreground"
        >
          {footer}
        </Button>
      </div>
    </div>
  );
};

export default Dashboard;
