import { getApiHostname, fetchWithTimeout, getToken } from './auth';

// Get the API hostname
const API_URL = `${getApiHostname()}`;

// Plugin API endpoints
const PLUGIN_ENDPOINTS = {
  list: `${API_URL}/plugins/available`,
  start: pluginId => `${API_URL}/plugins/${pluginId}/start`,
  stop: pluginId => `${API_URL}/plugins/${pluginId}/stop`,
  updateRoles: pluginId => `${API_URL}/plugins/${pluginId}/roles`,
};

/**
 * Get all available plugins
 */
export const getPlugins = async () => {
  try {
    const token = getToken();
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
    const token = getToken();
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
    const token = getToken();
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
    const token = getToken();
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

// Test function to check Core service connectivity
export const testCoreService = async () => {
  try {
    const healthUrl = `${getApiHostname()}/health`;
    console.log('Testing Core service at:', healthUrl);

    const response = await fetchWithTimeout(
      healthUrl,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      },
      5000
    );

    if (response.ok) {
      const data = await response.json();
      console.log('Core service health check successful:', data);
      return { success: true, data };
    } else {
      console.error('Core service health check failed:', response.status, response.statusText);
      return { success: false, error: `HTTP ${response.status}: ${response.statusText}` };
    }
  } catch (error) {
    console.error('Core service connectivity test failed:', error);
    return { success: false, error: error.message };
  }
};
