import React, { useState, useEffect } from 'react';
import { BarChart3, Wrench } from 'lucide-react';
import { maintenanceAPI } from '../../../backend/api/maintenance';

const MaintenanceTypeAnalytics = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    startDate: '',
    endDate: ''
  });

  const fetchMaintenanceByType = async () => {
    try {
      setLoading(true);
      setError(null);

      const startDateTime = filters.startDate ? new Date(filters.startDate).toISOString() : null;
      const endDateTime = filters.endDate ? new Date(filters.endDate + 'T23:59:59').toISOString() : null;

      console.log('Fetching maintenance by type:', { startDateTime, endDateTime });

      const response = await maintenanceAPI.getMaintenanceByType(startDateTime, endDateTime);
      console.log('Maintenance by type response:', response);

      const records = response.data?.records_by_type || [];
      setData(records.sort((a, b) => b.count - a.count)); // Sort by count descending
    } catch (err) {
      console.error('Error fetching maintenance by type:', err);
      setError('Failed to load maintenance type analytics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMaintenanceByType();
  }, [filters]);

  const formatCurrency = (amount) => {
    return `R${(amount || 0).toLocaleString('en-ZA', { minimumFractionDigits: 2 })}`;
  };

  const formatMaintenanceType = (type) => {
    if (!type) return 'Unknown';
    return type.replace(/_/g, ' ')
              .replace(/\b\w/g, letter => letter.toUpperCase());
  };

  const getTypeColor = (index) => {
    const colors = [
      'bg-blue-500', 'bg-green-500', 'bg-yellow-500', 'bg-purple-500',
      'bg-red-500', 'bg-indigo-500', 'bg-pink-500', 'bg-orange-500',
      'bg-teal-500', 'bg-cyan-500', 'bg-lime-500', 'bg-amber-500'
    ];
    return colors[index % colors.length];
  };

  const getTypeBadgeColor = (index) => {
    const colors = [
      'bg-blue-100 text-blue-800 border-blue-200 dark:bg-blue-900 dark:text-blue-200 dark:border-blue-700',
      'bg-green-100 text-green-800 border-green-200 dark:bg-green-900 dark:text-green-200 dark:border-green-700',
      'bg-yellow-100 text-yellow-800 border-yellow-200 dark:bg-yellow-900 dark:text-yellow-200 dark:border-yellow-700',
      'bg-purple-100 text-purple-800 border-purple-200 dark:bg-purple-900 dark:text-purple-200 dark:border-purple-700',
      'bg-red-100 text-red-800 border-red-200 dark:bg-red-900 dark:text-red-200 dark:border-red-700',
      'bg-indigo-100 text-indigo-800 border-indigo-200 dark:bg-indigo-900 dark:text-indigo-200 dark:border-indigo-700',
    ];
    return colors[index % colors.length];
  };

  const maxCount = data.length > 0 ? Math.max(...data.map(item => item.count)) : 1;

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <BarChart3 className="w-5 h-5" />
          Maintenance by Type
        </h3>
        
        <div className="flex flex-col sm:flex-row gap-2">
          <input
            type="date"
            value={filters.startDate}
            onChange={(e) => setFilters(prev => ({ ...prev, startDate: e.target.value }))}
            className="border border-border rounded-md px-3 py-2 text-sm"
            placeholder="Start date (optional)"
          />
          <input
            type="date"
            value={filters.endDate}
            onChange={(e) => setFilters(prev => ({ ...prev, endDate: e.target.value }))}
            className="border border-border rounded-md px-3 py-2 text-sm"
            placeholder="End date (optional)"
          />
        </div>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <p className="text-red-600 dark:text-red-400 text-sm">{error}</p>
          <button
            onClick={fetchMaintenanceByType}
            className="mt-2 text-red-800 dark:text-red-200 hover:underline text-xs"
          >
            Retry
          </button>
        </div>
      )}

      <div className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 rounded-lg p-6 border border-border">
        {loading ? (
          <div className="space-y-4">
            {[1, 2, 3, 4, 5].map(i => (
              <div key={i} className="animate-pulse">
                <div className="flex items-center justify-between mb-2">
                  <div className="bg-muted h-4 w-32 rounded"></div>
                  <div className="bg-muted h-4 w-20 rounded"></div>
                </div>
                <div className="bg-muted h-3 rounded w-full"></div>
              </div>
            ))}
          </div>
        ) : data.length > 0 ? (
          <div className="space-y-4">
            {data.map((item, index) => (
              <div key={item.maintenance_type} className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className={`px-3 py-1 rounded-full text-sm font-medium border ${getTypeBadgeColor(index)}`}>
                      <Wrench className="w-4 h-4 inline mr-1" />
                      {formatMaintenanceType(item.maintenance_type)}
                    </span>
                    <span className="text-sm text-muted-foreground">
                      {item.count} record{item.count !== 1 ? 's' : ''}
                    </span>
                  </div>
                  <div className="text-right">
                    <div className="font-semibold">{formatCurrency(item.total_cost)}</div>
                    <div className="text-sm text-muted-foreground">
                      Avg: {formatCurrency(item.average_cost)}
                    </div>
                  </div>
                </div>
                
                {/* Progress bar for count visualization */}
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                  <div
                    className={`h-3 rounded-full transition-all duration-500 ${getTypeColor(index)}`}
                    style={{ width: `${(item.count / maxCount) * 100}%` }}
                  ></div>
                </div>
                
                {/* Additional metrics */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs text-muted-foreground pl-4">
                  <div>
                    <span className="font-medium">Records:</span> {item.count}
                  </div>
                  <div>
                    <span className="font-medium">Total:</span> {formatCurrency(item.total_cost)}
                  </div>
                  <div>
                    <span className="font-medium">Average:</span> {formatCurrency(item.average_cost)}
                  </div>
                  <div>
                    <span className="font-medium">Share:</span> {((item.count / data.reduce((sum, d) => sum + d.count, 0)) * 100).toFixed(1)}%
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <Wrench className="w-12 h-12 text-muted-foreground mx-auto mb-3" />
            <p className="text-muted-foreground">No maintenance type data available</p>
            <p className="text-sm text-muted-foreground mt-1">
              {filters.startDate || filters.endDate ? 'Try adjusting the date filters' : 'Create some maintenance records to see analytics'}
            </p>
          </div>
        )}
      </div>

      {/* Summary Statistics */}
      {!loading && data.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 rounded-lg p-4 text-center border border-border">
            <div className="text-2xl font-bold text-primary">
              {data.length}
            </div>
            <div className="text-sm text-muted-foreground">Maintenance Types</div>
          </div>
          
          <div className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 rounded-lg p-4 text-center border border-border">
            <div className="text-2xl font-bold text-blue-600">
              {data.reduce((sum, item) => sum + item.count, 0)}
            </div>
            <div className="text-sm text-muted-foreground">Total Records</div>
          </div>
          
          <div className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 rounded-lg p-4 text-center border border-border">
            <div className="text-2xl font-bold text-green-600">
              {formatCurrency(data.reduce((sum, item) => sum + item.total_cost, 0))}
            </div>
            <div className="text-sm text-muted-foreground">Total Cost</div>
          </div>
          
          <div className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 rounded-lg p-4 text-center border border-border">
            <div className="text-2xl font-bold text-purple-600">
              {formatCurrency(
                data.reduce((sum, item) => sum + item.total_cost, 0) / 
                data.reduce((sum, item) => sum + item.count, 0) || 0
              )}
            </div>
            <div className="text-sm text-muted-foreground">Overall Avg Cost</div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MaintenanceTypeAnalytics;
