import React from 'react';
import { Button } from '../components/ui/button';

// Mock data for the dashboard
const mockData = {
  fleetOverview: {
    totalVehicles: 42,
    activeTrips: 8,
    availableDrivers: 15,
    maintenanceAlerts: 3,
  },
  recentTrips: [
    {
      id: 'T001',
      driver: 'John Smith',
      vehicle: 'TRK-001',
      route: 'Cape Town → Johannesburg',
      status: 'In Progress',
      progress: 65,
      eta: '14:30',
    },
    {
      id: 'T002',
      driver: 'Sarah Johnson',
      vehicle: 'VAN-012',
      route: 'Durban → Port Elizabeth',
      status: 'Completed',
      progress: 100,
      eta: 'Arrived',
    },
    {
      id: 'T003',
      driver: 'Mike Wilson',
      vehicle: 'TRK-005',
      route: 'Pretoria → Bloemfontein',
      status: 'Starting',
      progress: 5,
      eta: '16:45',
    },
  ],
  maintenanceAlerts: [
    {
      vehicle: 'TRK-003',
      type: 'Oil Change',
      dueDate: '2025-06-20',
      priority: 'Medium',
    },
    {
      vehicle: 'VAN-008',
      type: 'Tire Inspection',
      dueDate: '2025-06-19',
      priority: 'High',
    },
    {
      vehicle: 'TRK-007',
      type: 'Brake Service',
      dueDate: '2025-06-25',
      priority: 'Low',
    },
  ],
  fuelConsumption: {
    thisMonth: 2847,
    lastMonth: 3124,
    savings: 277,
    trend: 'down',
  },
};

const Dashboard = () => {
  return (
    <div className="container mx-auto py-8 space-y-8">
      {/* Header */}
      <header>
        <h1 className="text-4xl font-bold mb-2">Fleet Dashboard</h1>
        <p className="text-muted-foreground">Overview of your fleet operations</p>
      </header>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total Vehicles"
          value={mockData.fleetOverview.totalVehicles}
          subtitle="Fleet size"
          color="blue"
        />
        <MetricCard
          title="Active Trips"
          value={mockData.fleetOverview.activeTrips}
          subtitle="Currently en route"
          color="green"
        />
        <MetricCard
          title="Available Drivers"
          value={mockData.fleetOverview.availableDrivers}
          subtitle="Ready for dispatch"
          color="purple"
        />
        <MetricCard
          title="Maintenance Alerts"
          value={mockData.fleetOverview.maintenanceAlerts}
          subtitle="Requiring attention"
          color="orange"
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Recent Trips */}
        <div className="bg-card rounded-lg border border-border p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">Recent Trips</h2>
            <Button variant="outline" size="sm">
              View All
            </Button>
          </div>
          <div className="space-y-4">
            {mockData.recentTrips.map(trip => (
              <TripCard key={trip.id} trip={trip} />
            ))}
          </div>
        </div>

        {/* Maintenance Alerts */}
        <div className="bg-card rounded-lg border border-border p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">Maintenance Alerts</h2>
            <Button variant="outline" size="sm">
              Manage
            </Button>
          </div>
          <div className="space-y-3">
            {mockData.maintenanceAlerts.map((alert, index) => (
              <MaintenanceAlert key={index} alert={alert} />
            ))}
          </div>
        </div>
      </div>

      {/* Fuel Consumption */}
      <div className="bg-card rounded-lg border border-border p-6">
        <h2 className="text-xl font-semibold mb-4">Fuel Consumption</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-primary">
              {mockData.fuelConsumption.thisMonth}L
            </div>
            <div className="text-sm text-muted-foreground">This Month</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-muted-foreground">
              {mockData.fuelConsumption.lastMonth}L
            </div>
            <div className="text-sm text-muted-foreground">Last Month</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              -{mockData.fuelConsumption.savings}L
            </div>
            <div className="text-sm text-muted-foreground">Savings</div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Component definitions
const MetricCard = ({ title, value, subtitle, color }) => {
  const colorClasses = {
    blue: 'text-blue-600',
    green: 'text-green-600',
    purple: 'text-purple-600',
    orange: 'text-orange-600',
  };

  return (
    <div className="bg-card rounded-lg border border-border p-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-medium text-muted-foreground">{title}</h3>
          <div className={`text-3xl font-bold ${colorClasses[color]}`}>{value}</div>
          <p className="text-xs text-muted-foreground">{subtitle}</p>
        </div>
      </div>
    </div>
  );
};

const TripCard = ({ trip }) => {
  const statusColors = {
    'In Progress': 'bg-blue-100 text-blue-800',
    Completed: 'bg-green-100 text-green-800',
    Starting: 'bg-yellow-100 text-yellow-800',
  };

  return (
    <div className="border border-border rounded-lg p-4">
      <div className="flex items-start justify-between mb-2">
        <div>
          <div className="font-medium">{trip.id}</div>
          <div className="text-sm text-muted-foreground">
            {trip.driver} • {trip.vehicle}
          </div>
        </div>
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[trip.status]}`}>
          {trip.status}
        </span>
      </div>
      <div className="text-sm mb-2">{trip.route}</div>
      {trip.status === 'In Progress' && (
        <div className="mb-2">
          <div className="flex justify-between text-xs text-muted-foreground mb-1">
            <span>Progress</span>
            <span>{trip.progress}%</span>
          </div>
          <div className="w-full bg-secondary rounded-full h-2">
            <div
              className="bg-primary h-2 rounded-full transition-all duration-300"
              style={{ width: `${trip.progress}%` }}
            ></div>
          </div>
        </div>
      )}
      <div className="text-xs text-muted-foreground">ETA: {trip.eta}</div>
    </div>
  );
};

const MaintenanceAlert = ({ alert }) => {
  const priorityColors = {
    High: 'border-red-200 bg-red-50 text-red-800',
    Medium: 'border-yellow-200 bg-yellow-50 text-yellow-800',
    Low: 'border-blue-200 bg-blue-50 text-blue-800',
  };

  return (
    <div className={`border rounded-lg p-3 ${priorityColors[alert.priority]}`}>
      <div className="flex items-center justify-between">
        <div>
          <div className="font-medium text-sm">{alert.vehicle}</div>
          <div className="text-xs opacity-80">{alert.type}</div>
        </div>
        <div className="text-right">
          <div className="text-xs opacity-80">Due: {alert.dueDate}</div>
          <div className="text-xs font-medium">{alert.priority}</div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
