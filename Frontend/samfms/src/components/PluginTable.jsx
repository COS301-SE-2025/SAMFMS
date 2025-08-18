// components/PluginTable.jsx
import React, { useEffect, useState } from 'react';
import { getPluginsWithStatus } from '../backend/api/plugins';

const statusClass = s => {
  const v = String(s || '').toLowerCase();
  if (v === 'healthy' || v === 'success' || v === 'ok') return 'text-green-600';
  if (v === 'unavailable' || v === 'unhealthy' || v === 'error' || v === 'down')
    return 'text-red-600';
  return 'text-yellow-600';
};

const PluginTable = () => {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const data = await getPluginsWithStatus();

        // Support either the flattened array (preferred) or a raw `{ sblocks: { ... } }` shape
        let items = [];
        if (Array.isArray(data)) {
          items = data;
        } else if (data && typeof data === 'object' && data.sblocks) {
          items = Object.entries(data.sblocks).map(([plugin, value]) => {
            const status = value?.data?.status ?? value?.status ?? 'unknown';
            return { plugin, status };
          });
        }

        if (mounted) setRows(items);
      } catch (e) {
        if (mounted) setError(e?.message || 'Failed to load plugin status');
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <div className="space-y-4">
      <div className="mb-6">
        <h2 className="text-2xl font-semibold text-foreground">Health Monitoring</h2>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-8">
          <div className="flex items-center gap-3">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
            <span className="text-muted-foreground">Loading plugin status...</span>
          </div>
        </div>
      ) : error ? (
        <div className="bg-destructive/10 border border-destructive/20 rounded-xl p-4">
          <div className="flex items-center gap-2 text-destructive">
            <div className="w-4 h-4 bg-destructive rounded-full flex-shrink-0"></div>
            <span className="font-medium">Health Check Failed:</span>
            {error}
          </div>
        </div>
      ) : (
        <div className="bg-background/50 backdrop-blur-sm rounded-xl border border-border/50 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="border-b border-border/50 bg-muted/30">
                  <th className="text-left p-4 font-semibold text-foreground">Plugin Name</th>
                  <th className="text-left p-4 font-semibold text-foreground">Health Status</th>
                  <th className="text-left p-4 font-semibold text-foreground">Last Checked</th>
                </tr>
              </thead>
              <tbody>
                {rows.map(({ plugin, status }, index) => (
                  <tr
                    key={plugin}
                    className={`border-b border-border/30 hover:bg-accent/30 transition-colors duration-150 ${
                      index % 2 === 0 ? 'bg-background/20' : 'bg-transparent'
                    }`}
                  >
                    <td className="p-4">
                      <div className="flex items-center gap-3">
                        <div
                          className={`w-3 h-3 rounded-full ${statusClass(status).replace(
                            'text-',
                            'bg-'
                          )} ${status?.toLowerCase() === 'healthy' ? 'animate-pulse' : ''}`}
                        ></div>
                        <span className="font-medium capitalize text-foreground">{plugin}</span>
                      </div>
                    </td>
                    <td className="p-4">
                      <span
                        className={`font-semibold px-3 py-1 rounded-full text-xs uppercase tracking-wider ${
                          status?.toLowerCase() === 'healthy'
                            ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300'
                            : status?.toLowerCase() === 'unhealthy' ||
                              status?.toLowerCase() === 'error'
                            ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300'
                            : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300'
                        }`}
                      >
                        {status}
                      </span>
                    </td>
                    <td className="p-4">
                      <span className="text-sm text-muted-foreground">
                        {new Date().toLocaleTimeString()}
                      </span>
                    </td>
                  </tr>
                ))}
                {rows.length === 0 && (
                  <tr>
                    <td className="p-8 text-center text-muted-foreground" colSpan={3}>
                      <div className="flex flex-col items-center gap-2">
                        <div className="w-12 h-12 bg-muted/50 rounded-full flex items-center justify-center">
                          <div className="w-6 h-6 bg-muted-foreground/30 rounded-full"></div>
                        </div>
                        <span>No plugin health data available</span>
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default PluginTable;
