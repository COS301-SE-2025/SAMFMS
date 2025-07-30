// components/PluginTable.jsx
import React, { useEffect, useState } from 'react';
import { getPluginsWithStatus } from '../backend/api/plugins';

const statusClass = (s) => {
  const v = String(s || '').toLowerCase();
  if (v === 'healthy' || v === 'success' || v === 'ok') return 'text-green-600';
  if (v === 'unavailable' || v === 'unhealthy' || v === 'error' || v === 'down') return 'text-red-600';
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
    return () => { mounted = false; };
  }, []);

  return (
    <div className="mt-6">
      <h2 className="text-xl font-semibold mb-3">Plugin Health</h2>

      {loading ? (
        <div className="p-3">Loading…</div>
      ) : error ? (
        <div className="p-3 text-red-600">{error}</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full border rounded-md">
            <thead>
              <tr className="border-b">
                <th className="text-left p-2">Plugin</th>
                <th className="text-left p-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {rows.map(({ plugin, status }) => (
                <tr key={plugin} className="border-b last:border-0">
                  <td className="p-2 capitalize">{plugin}</td>
                  <td className="p-2">
                    <span className={`font-medium ${statusClass(status)}`}>
                      {status}
                    </span>
                  </td>
                </tr>
              ))}
              {rows.length === 0 && (
                <tr>
                  <td className="p-2" colSpan={2}>No plugins returned.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default PluginTable;