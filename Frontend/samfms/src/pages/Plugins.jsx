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
  removeSblock,
  addSblock,
} from '../backend/api/plugins';
import { useAuth, ROLES } from '../components/auth/RBACUtils';
import PluginCard from '../components/plugins/PluginCard';
import PluginTable from '../components/PluginTable';

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
        // console.log(pluginsData);
        setPlugins(pluginsData);
      } catch (err) {
       // setError('Failed to load plugins: ' + err.message);
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
   //   setError('Failed to refresh plugins: ' + err.message);
      console.error('Error refreshing plugins:', err);
    } finally {
      setRefreshing(false);
    }
  };

  const syncPluginsStatus = async () => {
    if (!isAdmin) {
    //  setError('Only administrators can sync plugin status');
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
    // setError('Failed to sync plugin status: ' + err.message);
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
    //  setError('Failed to update plugin access: ' + err.message);
      console.error('Error updating plugin access:', err);
    } finally {
      setActionLoading(prev => ({ ...prev, [pluginId]: false }));
    }
  };
  // Handler for toggling enabled/disabled
  const handleEnabledToggle = async pluginId => {
    if (!isAdmin) {
    //  setError('Only administrators can start/stop plugins');
      return;
    }

    try {
      setActionLoading(prev => ({ ...prev, [pluginId]: true }));

      const plugin = plugins.find(p => p.plugin_id === pluginId);
      if (!plugin) return;

      let result;
      if (plugin.status === 'ACTIVE') {
        removeSblock(pluginId.label);
        result = await stopPlugin(pluginId);
      } else {
        addSblock(pluginId.label);
        result = await startPlugin(pluginId);
      }

      // Update local state with the result
      setPlugins(prev =>
        prev.map(p => (p.plugin_id === pluginId ? { ...p, status: result.status } : p))
      );

      // Refresh plugin status after a short delay
      setTimeout(() => refreshPluginStatus(pluginId), 1000);
    } catch (err) {
    //  setError('Failed to toggle plugin: ' + err.message);
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
    <div className="relative container mx-auto py-8">
      {/* Background pattern */}
      <div
        className="absolute inset-0 z-0 opacity-10 pointer-events-none"
        style={{
          backgroundImage: 'url("/logo/logo_icon_dark.svg")',
          backgroundSize: '200px',
          backgroundRepeat: 'repeat',
          filter: 'blur(1px)',
        }}
        aria-hidden="true"
      />
      {/* Content */}
      <div className="relative z-10">
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


        <PluginTable />

        {error && (
          <div className="mb-6 p-4 bg-destructive/10 border border-destructive/20 rounded-lg text-destructive">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 gap-6">
          {plugins.map(plugin => (
            <PluginCard
              key={plugin.plugin_id}
              plugin={plugin}
              onAccessToggle={handleAccessToggle}
              onEnabledToggle={handleEnabledToggle}
              isLoading={actionLoading[plugin.plugin_id]}
            />
          ))}
        </div>
      </div>
    </div>
  );
};

export default Plugins;
