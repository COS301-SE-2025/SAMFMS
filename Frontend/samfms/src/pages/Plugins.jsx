import React, { useState, useEffect } from 'react';
import { Button } from '../components/ui/button';
import {
  getPlugins,
  getAllPlugins,
  startPlugin,
  stopPlugin,
  updatePluginRoles,
  getPluginStatus,
  testCoreService,
  syncPluginStatus,
  debugDockerAccess,
} from '../backend/api/plugins';
import { useAuth, ROLES } from '../components/RBACUtils';

const userTypes = ['admin', 'fleet_manager', 'driver'];

const Plugins = () => {
  const { hasRole } = useAuth();
  const [plugins, setPlugins] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [actionLoading, setActionLoading] = useState({});
  const [refreshing, setRefreshing] = useState(false);

  // Check if user has admin access
  const isAdmin = hasRole(ROLES.ADMIN);
  // Load plugins on component mount
  useEffect(() => {
    const initializePlugins = async () => {
      try {
        setLoading(true);
        setError('');

        // Test Core service connectivity first
        console.log('Testing Core service connectivity...');
        const healthCheck = await testCoreService();
        if (!healthCheck.success) {
          throw new Error(`Core service is not accessible: ${healthCheck.error}`);
        }
        console.log('Core service is accessible, loading plugins...');

        // Load plugins based on user role
        const pluginsData = isAdmin ? await getAllPlugins() : await getPlugins();
        setPlugins(pluginsData);
      } catch (err) {
        setError('Failed to load plugins: ' + err.message);
        console.error('Error loading plugins:', err);
      } finally {
        setLoading(false);
      }
    };

    initializePlugins();
  }, [isAdmin]);

  const refreshPlugins = async () => {
    try {
      setRefreshing(true);
      setError('');

      const pluginsData = isAdmin ? await getAllPlugins() : await getPlugins();
      setPlugins(pluginsData);
    } catch (err) {
      setError('Failed to refresh plugins: ' + err.message);
      console.error('Error refreshing plugins:', err);
    } finally {
      setRefreshing(false);
    }
  };

  const syncPluginsStatus = async () => {
    if (!isAdmin) {
      setError('Only administrators can sync plugin status');
      return;
    }

    try {
      setRefreshing(true);
      setError('');

      // Sync status with containers
      await syncPluginStatus();

      // Refresh plugins to get updated status
      const pluginsData = await getAllPlugins();
      setPlugins(pluginsData);
    } catch (err) {
      setError('Failed to sync plugin status: ' + err.message);
      console.error('Error syncing plugin status:', err);
    } finally {
      setRefreshing(false);
    }
  };

  // Handler for changing access for a plugin
  const handleAccessToggle = async (pluginId, role) => {
    try {
      setActionLoading(prev => ({ ...prev, [pluginId]: true }));

      const plugin = plugins.find(p => p.plugin_id === pluginId);
      if (!plugin) return;

      const newRoles = plugin.allowed_roles.includes(role)
        ? plugin.allowed_roles.filter(r => r !== role)
        : [...plugin.allowed_roles, role];

      await updatePluginRoles(pluginId, newRoles);

      // Update local state
      setPlugins(prev =>
        prev.map(p => (p.plugin_id === pluginId ? { ...p, allowed_roles: newRoles } : p))
      );
    } catch (err) {
      setError('Failed to update plugin access: ' + err.message);
      console.error('Error updating plugin access:', err);
    } finally {
      setActionLoading(prev => ({ ...prev, [pluginId]: false }));
    }
  };
  // Handler for toggling enabled/disabled
  const handleEnabledToggle = async pluginId => {
    if (!isAdmin) {
      setError('Only administrators can start/stop plugins');
      return;
    }

    try {
      setActionLoading(prev => ({ ...prev, [pluginId]: true }));

      const plugin = plugins.find(p => p.plugin_id === pluginId);
      if (!plugin) return;

      let result;
      if (plugin.status === 'ACTIVE') {
        result = await stopPlugin(pluginId);
      } else {
        result = await startPlugin(pluginId);
      }

      // Update local state with the result
      setPlugins(prev =>
        prev.map(p => (p.plugin_id === pluginId ? { ...p, status: result.status } : p))
      );

      // Refresh plugin status after a short delay
      setTimeout(() => refreshPluginStatus(pluginId), 1000);
    } catch (err) {
      setError('Failed to toggle plugin: ' + err.message);
      console.error('Error toggling plugin:', err);
    } finally {
      setActionLoading(prev => ({ ...prev, [pluginId]: false }));
    }
  };

  // Refresh individual plugin status
  const refreshPluginStatus = async pluginId => {
    try {
      const status = await getPluginStatus(pluginId);
      setPlugins(prev =>
        prev.map(p =>
          p.plugin_id === pluginId
            ? { ...p, status: status.status, container_status: status.container_status }
            : p
        )
      );
    } catch (err) {
      console.error('Error refreshing plugin status:', err);
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto py-8">
        <div className="flex justify-center items-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
            <p>Loading plugins...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8">
      <header className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-4xl font-bold">Plugins</h1>
          <p className="text-muted-foreground">Manage system plugins and extensions</p>
        </div>{' '}
        <div className="flex space-x-2">
          <Button onClick={refreshPlugins} variant="outline" disabled={refreshing}>
            {refreshing ? 'Refreshing...' : 'Refresh'}
          </Button>
          <Button onClick={syncPluginsStatus} variant="outline" disabled={refreshing}>
            {refreshing ? 'Syncing...' : 'Sync Status'}
          </Button>
        </div>
      </header>

      {error && (
        <div className="mb-6 p-4 bg-destructive/10 border border-destructive/20 rounded-lg text-destructive">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 gap-6">
        {plugins.map(plugin => (
          <PluginItem
            key={plugin.plugin_id}
            plugin={plugin}
            onAccessToggle={handleAccessToggle}
            onEnabledToggle={handleEnabledToggle}
            isLoading={actionLoading[plugin.plugin_id]}
          />
        ))}
      </div>
    </div>
  );
};

const PluginItem = ({ plugin, onAccessToggle, onEnabledToggle, isLoading }) => {
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

  const statusDisplay = getStatusDisplay(plugin.status);
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
            {plugin.plugin_id === 'security' && (
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
            <span className={`mr-3 ${statusDisplay.color}`}>{statusDisplay.text}</span>
            <button
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
            </button>
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

export default Plugins;
