import React, { useState, useEffect } from 'react';
import { Button } from '../components/ui/button';

const PluginManagement = () => {
  const [plugins, setPlugins] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [operationLoading, setOperationLoading] = useState({});

  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  const getAuthToken = () => {
    return localStorage.getItem('auth_token') || '';
  };

  const fetchPlugins = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/plugins/`, {
        headers: {
          Authorization: `Bearer ${getAuthToken()}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setPlugins(data);
    } catch (err) {
      console.error('Error fetching plugins:', err);
      setError(`Failed to load plugins: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handlePluginToggle = async (pluginId, currentStatus) => {
    try {
      setOperationLoading(prev => ({ ...prev, [pluginId]: true }));
      setError('');
      setSuccess('');

      const action = currentStatus === 'active' ? 'stop' : 'start';
      const response = await fetch(`${API_URL}/plugins/${pluginId}/${action}`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${getAuthToken()}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      setSuccess(`Plugin ${action}ed successfully: ${result.message}`);

      // Refresh plugins list
      await fetchPlugins();
    } catch (err) {
      console.error(`Error toggling plugin:`, err);
      setError(`Failed to toggle plugin: ${err.message}`);
    } finally {
      setOperationLoading(prev => ({ ...prev, [pluginId]: false }));
    }
  };

  const updatePluginRoles = async (pluginId, newRoles) => {
    try {
      setError('');
      setSuccess('');

      const response = await fetch(`${API_URL}/plugins/${pluginId}/roles`, {
        method: 'PUT',
        headers: {
          Authorization: `Bearer ${getAuthToken()}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          plugin_id: pluginId,
          allowed_roles: newRoles,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      setSuccess(`Plugin roles updated successfully: ${result.message}`);

      // Refresh plugins list
      await fetchPlugins();
    } catch (err) {
      console.error('Error updating plugin roles:', err);
      setError(`Failed to update plugin roles: ${err.message}`);
    }
  };

  useEffect(() => {
    fetchPlugins();
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="text-lg">Loading plugins...</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Plugin Management</h1>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
            <div className="text-red-800">{error}</div>
          </div>
        )}

        {success && (
          <div className="bg-green-50 border border-green-200 rounded-md p-4 mb-6">
            <div className="text-green-800">{success}</div>
          </div>
        )}

        <div className="grid gap-6">
          {plugins.map(plugin => (
            <div
              key={plugin.plugin_id}
              className="bg-white shadow-sm border border-gray-200 rounded-lg p-6"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center">
                  <h3 className="text-xl font-semibold text-gray-900">{plugin.name}</h3>
                  <span
                    className={`ml-3 px-2 py-1 text-xs font-medium rounded-full ${
                      plugin.status === 'active'
                        ? 'bg-green-100 text-green-800'
                        : plugin.status === 'inactive'
                        ? 'bg-gray-100 text-gray-800'
                        : plugin.status === 'starting'
                        ? 'bg-yellow-100 text-yellow-800'
                        : plugin.status === 'stopping'
                        ? 'bg-orange-100 text-orange-800'
                        : 'bg-red-100 text-red-800'
                    }`}
                  >
                    {plugin.status.toUpperCase()}
                  </span>
                </div>
                <Button
                  onClick={() => handlePluginToggle(plugin.plugin_id, plugin.status)}
                  disabled={
                    operationLoading[plugin.plugin_id] ||
                    plugin.status === 'starting' ||
                    plugin.status === 'stopping'
                  }
                  className={`${
                    plugin.status === 'active'
                      ? 'bg-red-600 hover:bg-red-700'
                      : 'bg-green-600 hover:bg-green-700'
                  } text-white`}
                >
                  {operationLoading[plugin.plugin_id]
                    ? 'Processing...'
                    : plugin.status === 'active'
                    ? 'Deactivate'
                    : 'Activate'}
                </Button>
              </div>

              <p className="text-gray-600 mb-4">{plugin.description}</p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="font-medium text-gray-700">Version:</span>
                  <span className="ml-2 text-gray-600">{plugin.version}</span>
                </div>
                <div>
                  <span className="font-medium text-gray-700">Container:</span>
                  <span className="ml-2 text-gray-600">{plugin.docker_service_name}</span>
                </div>
                {plugin.port && (
                  <div>
                    <span className="font-medium text-gray-700">Port:</span>
                    <span className="ml-2 text-gray-600">{plugin.port}</span>
                  </div>
                )}
              </div>

              <div className="mt-4">
                <span className="font-medium text-gray-700">Allowed Roles:</span>
                <div className="flex flex-wrap gap-2 mt-2">
                  {plugin.allowed_roles.map(role => (
                    <span
                      key={role}
                      className="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded"
                    >
                      {role}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>

        {plugins.length === 0 && (
          <div className="text-center py-12">
            <div className="text-gray-500 text-lg">No plugins available</div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PluginManagement;
