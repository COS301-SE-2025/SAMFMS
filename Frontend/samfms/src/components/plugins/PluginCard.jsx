import React, {useState} from 'react';
import {Button} from './ui/button';

const userTypes = ['admin', 'fleet_manager', 'driver'];

const PluginCard = ({
  plugin,
  onAccessToggle,
  onEnabledToggle,
  isLoading
}) => {
  const [dropdownOpen, setDropdownOpen] = useState(false);

  // Map status to display values
  const getStatusDisplay = status => {
    switch (status) {
      case 'ACTIVE':
        return {text: 'Active', color: 'text-green-500'};
      case 'INACTIVE':
        return {text: 'Inactive', color: 'text-gray-500'};
      case 'STARTING':
        return {text: 'Starting...', color: 'text-yellow-500'};
      case 'STOPPING':
        return {text: 'Stopping...', color: 'text-orange-500'};
      case 'ERROR':
        return {text: 'Error', color: 'text-red-500'};
      default:
        return {text: 'Unknown', color: 'text-gray-500'};
    }
  };

  const statusDisplay = getStatusDisplay(plugin.status.toUpperCase());
  const isEnabled = plugin.status === 'ACTIVE';

  // Convert role names for display
  const formatRoleName = role => {
    switch (role) {
      case 'admin':
        return 'Admin';
      case 'fleet_manager':
        return 'Fleet Manager';
      case 'driver':
        return 'Driver';
      default:
        return role;
    }
  };

  return (
    <div className="bg-card rounded-lg shadow-md p-6 border border-border">
      <div className="flex flex-wrap justify-between items-start">
        <div className="flex-1 mr-6">
          <div className="flex items-center mb-2">
            <h2 className="text-xl font-semibold">{plugin.name}</h2>
            {plugin.category === 'core' && (
              <span className="ml-3 px-2 py-1 text-xs bg-primary/20 text-primary rounded-full">
                Core
              </span>
            )}
          </div>
          <p className="text-muted-foreground mb-4">{plugin.description}</p>
          <div className="text-sm text-muted-foreground">
            <p>Plugin ID: {plugin.plugin_id}</p>
            <p>Version: {plugin.version}</p>
          </div>
          <div className="mt-4 relative">
            <label className="block font-medium mb-1">User Access</label>
            <button
              type="button"
              className="border rounded px-2 py-1 w-full text-left bg-background disabled:opacity-50"
              onClick={() => setDropdownOpen(open => !open)}
              disabled={isLoading}
            >
              {plugin.allowed_roles.length === 0
                ? 'No Access'
                : plugin.allowed_roles.map(formatRoleName).join(', ')}
              <span className="float-right">{dropdownOpen ? '▲' : '▼'}</span>
            </button>
            {dropdownOpen && (
              <div className="absolute z-10 mt-1 w-full bg-white dark:bg-gray-900 border rounded shadow">
                {userTypes.map(type => (
                  <div
                    key={type}
                    className="flex items-center px-3 py-2 cursor-pointer hover:bg-accent"
                    onClick={() => onAccessToggle(plugin.plugin_id, type)}
                  >
                    <input
                      type="checkbox"
                      checked={plugin.allowed_roles.includes(type)}
                      readOnly
                      className="mr-2"
                    />
                    <span>{formatRoleName(type)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
        <div className="flex flex-col items-end space-y-4">
          <div className="flex items-center">
            <span className={`mr-3 ${statusDisplay.color}`}>{plugin.status}</span>
            {/* <button
              className="relative inline-block w-12 h-6 rounded-full bg-secondary focus:outline-none disabled:opacity-50"
              onClick={() => onEnabledToggle(plugin.plugin_id)}
              disabled={isLoading || plugin.status === 'STARTING' || plugin.status === 'STOPPING'}
              aria-label={isEnabled ? 'Disable plugin' : 'Enable plugin'}
              type="button"
            >
              <span
                className={`absolute left-1 top-1 w-4 h-4 rounded-full transition-all duration-200 ${
                  isEnabled ? 'bg-primary translate-x-6' : 'bg-foreground'
                }`}
                style={{
                  transform: isEnabled ? 'translateX(1.5rem)' : 'translateX(0)',
                }}
              ></span>
              <input
                type="checkbox"
                checked={isEnabled}
                readOnly
                className="sr-only"
                tabIndex={-1}
              />
            </button> */}
          </div>
          <div className="flex space-x-2">
            <Button variant="outline" size="sm" disabled>
              Settings
            </Button>
            {isLoading && (
              <div className="flex items-center">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default PluginCard;
