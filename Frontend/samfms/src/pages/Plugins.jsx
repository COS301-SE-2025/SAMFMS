import React from 'react';
import { Button } from '../components/ui/button';

const Plugins = () => {
  // Sample plugins data
  const plugins = [
    {
      id: 'gps-tracking',
      name: 'GPS Tracking',
      description: 'Real-time GPS tracking and location history for fleet vehicles',
      author: 'SAMFMS Core',
      version: '1.2.0',
      isEnabled: true,
      isCore: true,
    },
    {
      id: 'maintenance-scheduler',
      name: 'Maintenance Scheduler',
      description: 'Schedule and track maintenance activities for all vehicles',
      author: 'SAMFMS Core',
      version: '1.0.3',
      isEnabled: true,
      isCore: true,
    },
    {
      id: 'fuel-management',
      name: 'Fuel Management',
      description: 'Track fuel consumption, costs, and efficiency metrics',
      author: 'SAMFMS Core',
      version: '1.1.5',
      isEnabled: true,
      isCore: true,
    },
    {
      id: 'driver-management',
      name: 'Driver Management',
      description: 'Manage driver information, licenses, and performance',
      author: 'SAMFMS Core',
      version: '1.2.1',
      isEnabled: false,
      isCore: false,
    },
    {
      id: 'route-optimization',
      name: 'Route Optimization',
      description: 'Optimize travel routes for improved efficiency and reduced costs',
      author: 'FleetTech Solutions',
      version: '2.0.1',
      isEnabled: true,
      isCore: false,
    },
    {
      id: 'expense-tracker',
      name: 'Expense Tracker',
      description: 'Track all fleet-related expenses and generate financial reports',
      author: 'Finance Integrations Ltd',
      version: '1.3.4',
      isEnabled: false,
      isCore: false,
    },
  ];

  return (
    <div className="container mx-auto py-8">
      <header className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-4xl font-bold">Plugins</h1>
          <p className="text-muted-foreground">Manage system plugins and extensions</p>
        </div>
        <Button>Add New Plugin</Button>
      </header>

      <div className="grid grid-cols-1 gap-6">
        {plugins.map(plugin => (
          <PluginItem key={plugin.id} plugin={plugin} />
        ))}
      </div>
    </div>
  );
};

const PluginItem = ({ plugin }) => {
  return (
    <div className="bg-card rounded-lg shadow-md p-6 border border-border">
      <div className="flex flex-wrap justify-between items-start">
        <div className="flex-1 mr-6">
          <div className="flex items-center mb-2">
            <h2 className="text-xl font-semibold">{plugin.name}</h2>
            {plugin.isCore && (
              <span className="ml-3 px-2 py-1 text-xs bg-primary/20 text-primary rounded-full">
                Core
              </span>
            )}
          </div>
          <p className="text-muted-foreground mb-4">{plugin.description}</p>
          <div className="text-sm text-muted-foreground">
            <p>Author: {plugin.author}</p>
            <p>Version: {plugin.version}</p>
          </div>
        </div>
        <div className="flex flex-col items-end space-y-4">
          <div className="flex items-center">
            <span
              className={`mr-3 ${plugin.isEnabled ? 'text-green-500' : 'text-muted-foreground'}`}
            >
              {plugin.isEnabled ? 'Enabled' : 'Disabled'}
            </span>
            <div className="relative inline-block w-12 h-6 rounded-full bg-secondary">
              <input
                type="checkbox"
                id={`toggle-${plugin.id}`}
                defaultChecked={plugin.isEnabled}
                className="sr-only peer"
              />
              <span
                className={`absolute left-1 top-1 w-4 h-4 rounded-full transition-all duration-200 ${
                  plugin.isEnabled ? 'bg-primary translate-x-6' : 'bg-foreground'
                }`}
              ></span>
            </div>
          </div>
          <div className="flex space-x-2">
            <Button variant="outline" size="sm">
              Settings
            </Button>
            <Button variant="outline" size="sm">
              Update
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Plugins;
