import { getApiHostname, fetchWithTimeout } from './auth';

// Get the API hostname
const API_URL = `${getApiHostname()}/api`;

// Plugin API endpoints
const PLUGIN_ENDPOINTS = {
  list: `${API_URL}/plugins`,
  start: pluginId => `${API_URL}/plugins/${pluginId}/start`,
  stop: pluginId => `${API_URL}/plugins/${pluginId}/stop`,
  updateRoles: pluginId => `${API_URL}/plugins/${pluginId}/roles`,
};

/**
 * Get all available plugins
 */
export const getPlugins = async () => {
  try {
    const token = localStorage.getItem('access_token');
    if (!token) {
      throw new Error('No authentication token found');
    }

    const response = await fetchWithTimeout(PLUGIN_ENDPOINTS.list, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch plugins: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching plugins:', error);
    throw error;
  }
};

/**
 * Start a plugin
 */
export const startPlugin = async pluginId => {
  try {
    const token = localStorage.getItem('access_token');
    if (!token) {
      throw new Error('No authentication token found');
    }

    const response = await fetchWithTimeout(PLUGIN_ENDPOINTS.start(pluginId), {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to start plugin: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`Error starting plugin ${pluginId}:`, error);
    throw error;
  }
};

/**
 * Stop a plugin
 */
export const stopPlugin = async pluginId => {
  try {
    const token = localStorage.getItem('access_token');
    if (!token) {
      throw new Error('No authentication token found');
    }

    const response = await fetchWithTimeout(PLUGIN_ENDPOINTS.stop(pluginId), {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to stop plugin: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`Error stopping plugin ${pluginId}:`, error);
    throw error;
  }
};

/**
 * Update plugin roles
 */
export const updatePluginRoles = async (pluginId, allowedRoles) => {
  try {
    const token = localStorage.getItem('access_token');
    if (!token) {
      throw new Error('No authentication token found');
    }

    const response = await fetchWithTimeout(PLUGIN_ENDPOINTS.updateRoles(pluginId), {
      method: 'PUT',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ allowed_roles: allowedRoles }),
    });

    if (!response.ok) {
      throw new Error(`Failed to update plugin roles: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`Error updating plugin roles ${pluginId}:`, error);
    throw error;
  }
};
