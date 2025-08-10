import React, { useState } from 'react';
import { Button } from '../ui/button';

const userTypes = ['admin', 'fleet_manager', 'driver'];

const PluginCard = ({ plugin, onAccessToggle, onEnabledToggle, isLoading }) => {
  const [dropdownOpen, setDropdownOpen] = useState(false);

  // Map status to display values
  const getStatusDisplay = status => {
    switch (status) {
      case 'ACTIVE':
        return { text: 'Active', color: 'text-green-500' };
      case 'INACTIVE':
        return { text: 'Inactive', color: 'text-gray-500' };
      case 'STARTING':
        return { text: 'Starting...', color: 'text-yellow-500' };
      case 'STOPPING':
        return { text: 'Stopping...', color: 'text-orange-500' };
      case 'ERROR':
        return { text: 'Error', color: 'text-red-500' };
      default:
        return { text: 'Unknown', color: 'text-gray-500' };
    }
  };

  const statusDisplay = getStatusDisplay(plugin.status.toUpperCase());
  // const isEnabled = plugin.status === 'ACTIVE'; // Commented out as unused

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
    <div className="bg-card/80 backdrop-blur-sm rounded-xl shadow-lg border border-border/50 p-6 hover:shadow-xl transition-all duration-300 hover:border-primary/20">
      <div className="flex flex-wrap justify-between items-start">
        <div className="flex-1 mr-6">
          <div className="flex items-center mb-3">
            <div className="flex items-center gap-3">
              <div
                className={`w-3 h-3 rounded-full ${
                  plugin.status === 'ACTIVE'
                    ? 'bg-green-500 animate-pulse'
                    : plugin.status === 'ERROR'
                    ? 'bg-red-500'
                    : plugin.status === 'STARTING' || plugin.status === 'STOPPING'
                    ? 'bg-yellow-500 animate-pulse'
                    : 'bg-gray-400'
                }`}
              ></div>
              <h2 className="text-xl font-semibold text-foreground">{plugin.name}</h2>
            </div>
            {plugin.category === 'core' && (
              <span className="ml-3 px-3 py-1 text-xs bg-gradient-to-r from-primary/20 to-primary/10 text-primary rounded-full font-medium border border-primary/20">
                Core Plugin
              </span>
            )}
          </div>

          <p className="text-muted-foreground mb-4 leading-relaxed">{plugin.description}</p>

          <div className="grid grid-cols-2 gap-4 mb-4">
            <div className="bg-muted/30 rounded-lg p-3">
              <p className="text-xs font-medium text-muted-foreground mb-1">Plugin ID</p>
              <p className="text-sm font-mono">{plugin.plugin_id}</p>
            </div>
            <div className="bg-muted/30 rounded-lg p-3">
              <p className="text-xs font-medium text-muted-foreground mb-1">Version</p>
              <p className="text-sm font-medium">{plugin.version}</p>
            </div>
          </div>

          <div className="relative">
            <label className="block font-medium mb-2 text-foreground">
              User Access Permissions
            </label>
            <button
              type="button"
              className="border border-border/50 rounded-lg px-4 py-3 w-full text-left bg-background/50 hover:bg-accent/50 disabled:opacity-50 transition-all duration-200 backdrop-blur-sm"
              onClick={() => setDropdownOpen(open => !open)}
              disabled={isLoading}
            >
              <div className="flex items-center justify-between">
                <span className="text-sm">
                  {plugin.allowed_roles.length === 0
                    ? 'No Access Granted'
                    : `${plugin.allowed_roles.length} Role${
                        plugin.allowed_roles.length === 1 ? '' : 's'
                      }: ${plugin.allowed_roles.map(formatRoleName).join(', ')}`}
                </span>
                <span
                  className={`transform transition-transform duration-200 ${
                    dropdownOpen ? 'rotate-180' : ''
                  }`}
                >
                  ▼
                </span>
              </div>
            </button>
            {dropdownOpen && (
              <div className="absolute z-20 mt-2 w-full bg-card/95 backdrop-blur-md border border-border/50 rounded-lg shadow-xl">
                <div className="p-2">
                  {userTypes.map(type => (
                    <div
                      key={type}
                      className="flex items-center px-3 py-2 cursor-pointer hover:bg-accent/50 rounded-lg transition-colors duration-150"
                      onClick={() => onAccessToggle(plugin.plugin_id, type)}
                    >
                      <input
                        type="checkbox"
                        checked={plugin.allowed_roles.includes(type)}
                        readOnly
                        className="mr-3 accent-primary"
                      />
                      <span className="text-sm font-medium">{formatRoleName(type)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="flex flex-col items-end space-y-4">
          <div className="flex items-center bg-muted/30 rounded-lg px-4 py-2">
            <div
              className={`w-2 h-2 rounded-full mr-3 ${statusDisplay.color.replace('text-', 'bg-')}`}
            ></div>
            <span className={`font-medium ${statusDisplay.color}`}>{statusDisplay.text}</span>
          </div>

          <div className="flex items-center space-x-3">
            {isLoading && (
              <div className="flex items-center bg-primary/10 rounded-lg px-3 py-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary mr-2"></div>
                <span className="text-sm text-primary">Processing...</span>
              </div>
            )}
            <Button
              variant="outline"
              size="sm"
              disabled
              className="bg-background/50 hover:bg-accent/50 transition-all duration-200"
            >
              Settings
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PluginCard;
