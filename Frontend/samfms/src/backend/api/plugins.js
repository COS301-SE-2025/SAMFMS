import { httpClient } from '../services/httpClient';
import { buildApiUrl } from '../../config/apiConfig';
import { getToken, fetchWithTimeout } from './auth';
import { API_ENDPOINTS } from '../../config/apiConfig';

// Plugin API endpoints using centralized configuration
const PLUGIN_ENDPOINTS = {
  list: buildApiUrl('/plugins/available'),
  all: buildApiUrl('/plugins/'),
  start: pluginId => buildApiUrl(`/plugins/${pluginId}/start`),
  stop: pluginId => buildApiUrl(`/plugins/${pluginId}/stop`),
  updateRoles: pluginId => buildApiUrl(`/plugins/${pluginId}/roles`),
  status: pluginId => buildApiUrl(`/plugins/${pluginId}/status`),
  health_status: API_ENDPOINTS.PLUGINSTATUS.STATUS,
};

/**
 * Get all available plugins
 */
export const getPlugins = async () => {
  try {
    return await httpClient.get('/plugins/available');
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

/**
 * Get all plugins (admin only)
 */
export const getAllPlugins = async () => {
  try {
    const token = getToken();
    if (!token) {
      throw new Error('No authentication token found');
    }

    const response = await fetchWithTimeout(PLUGIN_ENDPOINTS.all, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch all plugins: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching all plugins:', error);
    throw error;
  }
};

/**
 * Get plugins with health status
 */
export const getPluginsWithStatus = async () => {
  try {
    const res = await fetch("http://capstone-samfms.dns.net.za:21004/health/healthy-services", {
      headers: { Accept: "application/json" },
    });

    if (!res.ok) {
      throw new Error(`Health endpoint failed: ${res.status} ${res.statusText}`);
    }

    const body = await res.json();
    const sblocks = body?.sblocks ?? {};

    return Object.entries(sblocks).map(([plugin, value]) => {
      const statusRaw =
        value?.data?.data?.status ??
        value?.data?.status ??
        value?.status ??
        "unknown";

      const status = String(statusRaw); 

      return { plugin, status };
    });
  } catch (err) {
    console.error("getPluginsWithStatus:", err);
    throw err; 
  }
};

/**
 * Get plugin runtime status
 */
export const getPluginStatus = async pluginId => {
  try {
    const token = getToken();
    if (!token) {
      throw new Error('No authentication token found');
    }

    const response = await fetchWithTimeout(PLUGIN_ENDPOINTS.status(pluginId), {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to get plugin status: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`Error getting plugin status ${pluginId}:`, error);
    throw error;
  }
};

// Test function to check Core service connectivity
export const testCoreService = async () => {
  try {
    const healthUrl = buildApiUrl('/health');
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

/**
 * Sync plugin status with container status
 */
export const syncPluginStatus = async () => {
  try {
    const token = getToken();
    if (!token) {
      throw new Error('No authentication token found');
    }

    const response = await fetchWithTimeout(buildApiUrl('/plugins/sync-status'), {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to sync plugin status: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error syncing plugin status:', error);
    throw error;
  }
};

/**
 * Debug Docker access (admin only)
 */
export const debugDockerAccess = async () => {
  try {
    const token = getToken();
    if (!token) {
      throw new Error('No authentication token found');
    }

    const response = await fetchWithTimeout(buildApiUrl('/plugins/debug/docker'), {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to get Docker debug info: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error getting Docker debug info:', error);
    throw error;
  }
};

export const addSblock = async username => {
  try {
    const token = getToken();
    if (!token) {
      throw new Error('No authentication token found');
    }

    const response = await fetchWithTimeout(buildApiUrl(`/sblock/add/${username}`), {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to add SBlock: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error adding SBlock:', error);
    throw error;
  }
};

export const removeSblock = async username => {
  try {
    const token = getToken();
    if (!token) {
      throw new Error('No authentication token found');
    }

    const response = await fetchWithTimeout(buildApiUrl(`/sblock/remove/${username}`), {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to remove SBlock: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error removing SBlock:', error);
    throw error;
  }
};
