import React, { useState, useEffect } from 'react';
import { maintenanceAPI } from '../backend/api/maintenance';

const MaintenanceAnalytics = ({ vehicles }) => {
  const [analyticsData, setAnalyticsData] = useState(null);
  const [costAnalytics, setCostAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    vehicleId: '',
    period: 'monthly',
    startDate: '',
    endDate: '',
  });

  useEffect(() => {
    loadAnalytics();
  }, [filters]);

  const loadAnalytics = async () => {
    try {
      setLoading(true);

      const [analyticsResponse, costResponse] = await Promise.all([
        maintenanceAPI.getMaintenanceAnalytics(
          filters.vehicleId || null,
          filters.startDate || null,
          filters.endDate || null
        ),
        maintenanceAPI.getCostAnalytics(filters.period, filters.vehicleId || null),
      ]);

      setAnalyticsData(analyticsResponse);
      setCostAnalytics(costResponse);
    } catch (err) {
      console.error('Error loading analytics:', err);
      setError('Failed to load analytics data');
    } finally {
      setLoading(false);
    }
  };

  const getVehicleName = vehicleId => {
    const vehicle = vehicles.find(v => v.id === vehicleId);
    return vehicle ? `${vehicle.make} ${vehicle.model} (${vehicle.license_plate})` : vehicleId;
  };

  const formatCurrency = amount => {
    return `R${(amount || 0).toLocaleString('en-ZA', { minimumFractionDigits: 2 })}`;
  };

  const getMaintenanceTypeColor = index => {
    const colors = [
      'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
      'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
      'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
      'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
      'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
      'bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200',
    ];
    return colors[index % colors.length];
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        <span className="ml-3">Loading analytics...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
        <h3 className="text-red-800 dark:text-red-200 font-semibold">Error</h3>
        <p className="text-red-600 dark:text-red-400 mt-2">{error}</p>
        <button
          onClick={loadAnalytics}
          className="mt-4 bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 transition"
        >
          Retry
        </button>
      </div>
    );
  }

  const analytics = analyticsData || {};
  const costs = costAnalytics || {};

  return (
    <div className="space-y-6">
      {/* Header and Filters */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <h2 className="text-xl font-semibold">Maintenance Analytics</h2>

        <div className="flex flex-wrap gap-4">
          <select
            value={filters.vehicleId}
            onChange={e => setFilters(prev => ({ ...prev, vehicleId: e.target.value }))}
            className="border border-border rounded-md px-3 py-2"
          >
            <option value="">All Vehicles</option>
            {vehicles.map(vehicle => (
              <option key={vehicle.id} value={vehicle.id}>
                {getVehicleName(vehicle.id)}
              </option>
            ))}
          </select>

          <select
            value={filters.period}
            onChange={e => setFilters(prev => ({ ...prev, period: e.target.value }))}
            className="border border-border rounded-md px-3 py-2"
          >
            <option value="monthly">Monthly</option>
            <option value="quarterly">Quarterly</option>
            <option value="yearly">Yearly</option>
          </select>

          <input
            type="date"
            value={filters.startDate}
            onChange={e => setFilters(prev => ({ ...prev, startDate: e.target.value }))}
            className="border border-border rounded-md px-3 py-2"
            placeholder="Start Date"
          />

          <input
            type="date"
            value={filters.endDate}
            onChange={e => setFilters(prev => ({ ...prev, endDate: e.target.value }))}
            className="border border-border rounded-md px-3 py-2"
            placeholder="End Date"
          />
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-card rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Total Maintenance Records</p>
              <p className="text-2xl font-bold">{analytics.total_records || 0}</p>
            </div>
            <div className="text-blue-500">
              <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
                <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
            </div>
          </div>
        </div>

        <div className="bg-card rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Total Cost</p>
              <p className="text-2xl font-bold text-green-600">
                {formatCurrency(analytics.total_cost)}
              </p>
            </div>
            <div className="text-green-500">
              <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
                <path d="M8.433 7.418c.155-.103.346-.196.567-.267v1.698a2.305 2.305 0 01-.567-.267C8.07 8.34 8 8.114 8 8c0-.114.07-.34.433-.582zM11 12.849v-1.698c.22.071.412.164.567.267.364.243.433.468.433.582 0 .114-.07.34-.433.582a2.305 2.305 0 01-.567.267z"></path>
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-13a1 1 0 10-2 0v.092a4.535 4.535 0 00-1.676.662C6.602 6.234 6 7.009 6 8c0 .99.602 1.765 1.324 2.246.48.32 1.054.545 1.676.662v1.941c-.391-.127-.68-.317-.843-.504a1 1 0 10-1.51 1.31c.562.649 1.413 1.076 2.353 1.253V15a1 1 0 102 0v-.092a4.535 4.535 0 001.676-.662C13.398 13.766 14 12.991 14 12c0-.99-.602-1.765-1.324-2.246A4.535 4.535 0 0011 9.092V7.151c.391.127.68.317.843.504a1 1 0 101.51-1.31c-.562-.649-1.413-1.076-2.353-1.253V5z"
                  clipRule="evenodd"
                ></path>
              </svg>
            </div>
          </div>
        </div>

        <div className="bg-card rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Average Cost per Record</p>
              <p className="text-2xl font-bold text-purple-600">
                {formatCurrency(analytics.average_cost)}
              </p>
            </div>
            <div className="text-purple-500">
              <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M3 3a1 1 0 000 2v8a2 2 0 002 2h2.586l-1.293 1.293a1 1 0 101.414 1.414L10 15.414l2.293 2.293a1 1 0 001.414-1.414L12.414 15H15a2 2 0 002-2V5a1 1 0 100-2H3zm11.707 4.707a1 1 0 00-1.414-1.414L10 9.586 8.707 8.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                ></path>
              </svg>
            </div>
          </div>
        </div>

        <div className="bg-card rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Vehicles Serviced</p>
              <p className="text-2xl font-bold text-orange-600">{analytics.vehicles_count || 0}</p>
            </div>
            <div className="text-orange-500">
              <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
                <path d="M8 16.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0zM15 16.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0z"></path>
                <path d="M3 4a1 1 0 00-1 1v10a1 1 0 001 1h1.05a2.5 2.5 0 014.9 0H10a1 1 0 001-1V5a1 1 0 00-1-1H3zM14 7a1 1 0 00-1 1v6.05A2.5 2.5 0 0115.95 16H17a1 1 0 001-1V8a1 1 0 00-1-1h-3z"></path>
              </svg>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Cost Breakdown by Period */}
        <div className="bg-card rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold mb-4">
            Cost Breakdown by {filters.period.charAt(0).toUpperCase() + filters.period.slice(1)}
          </h3>
          {costs.periods && costs.periods.length > 0 ? (
            <div className="space-y-3">
              {costs.periods.map((period, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 bg-muted rounded-lg"
                >
                  <div>
                    <p className="font-medium">{period.period}</p>
                    <p className="text-sm text-muted-foreground">{period.record_count} records</p>
                  </div>
                  <div className="text-right">
                    <p className="font-bold">{formatCurrency(period.total_cost)}</p>
                    <p className="text-sm text-muted-foreground">
                      Avg: {formatCurrency(period.average_cost)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground text-center py-8">No cost data available</p>
          )}
        </div>

        {/* Maintenance Type Distribution */}
        <div className="bg-card rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold mb-4">Maintenance Type Distribution</h3>
          {analytics.maintenance_types && analytics.maintenance_types.length > 0 ? (
            <div className="space-y-3">
              {analytics.maintenance_types.map((type, index) => (
                <div key={index} className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <span
                      className={`px-2 py-1 rounded-full text-xs ${getMaintenanceTypeColor(index)}`}
                    >
                      {type.maintenance_type?.replace('_', ' ')}
                    </span>
                    <span className="text-sm text-muted-foreground">{type.count} records</span>
                  </div>
                  <div className="text-right">
                    <p className="font-medium">{formatCurrency(type.total_cost)}</p>
                    <div className="w-20 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                      <div
                        className="bg-primary h-2 rounded-full"
                        style={{ width: `${(type.count / (analytics.total_records || 1)) * 100}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground text-center py-8">
              No maintenance type data available
            </p>
          )}
        </div>

        {/* Vehicle Cost Breakdown */}
        <div className="bg-card rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold mb-4">Cost by Vehicle</h3>
          {costs.vehicles && costs.vehicles.length > 0 ? (
            <div className="space-y-3 max-h-64 overflow-y-auto">
              {costs.vehicles.map((vehicle, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 border border-border rounded-lg"
                >
                  <div>
                    <p className="font-medium">{getVehicleName(vehicle.vehicle_id)}</p>
                    <p className="text-sm text-muted-foreground">{vehicle.record_count} records</p>
                  </div>
                  <div className="text-right">
                    <p className="font-bold">{formatCurrency(vehicle.total_cost)}</p>
                    <p className="text-sm text-muted-foreground">
                      Avg: {formatCurrency(vehicle.average_cost)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground text-center py-8">No vehicle cost data available</p>
          )}
        </div>

        {/* Recent High-Cost Maintenance */}
        <div className="bg-card rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold mb-4">High-Cost Maintenance Records</h3>
          {analytics.high_cost_records && analytics.high_cost_records.length > 0 ? (
            <div className="space-y-3 max-h-64 overflow-y-auto">
              {analytics.high_cost_records.map((record, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 border border-border rounded-lg"
                >
                  <div>
                    <p className="font-medium">{record.maintenance_type?.replace('_', ' ')}</p>
                    <p className="text-sm text-muted-foreground">
                      {getVehicleName(record.vehicle_id)} •{' '}
                      {new Date(record.date_performed).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-red-600">{formatCurrency(record.cost)}</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground text-center py-8">No high-cost records found</p>
          )}
        </div>
      </div>

      {/* Monthly Trend Analysis */}
      {costs.monthly_trend && costs.monthly_trend.length > 0 && (
        <div className="bg-card rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold mb-4">Monthly Cost Trend</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
            {costs.monthly_trend.map((month, index) => (
              <div key={index} className="text-center p-4 bg-muted rounded-lg">
                <p className="text-sm font-medium text-muted-foreground">{month.month}</p>
                <p className="text-xl font-bold">{formatCurrency(month.total_cost)}</p>
                <p className="text-xs text-muted-foreground">{month.record_count} records</p>
                <div className="mt-2 w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div
                    className="bg-primary h-2 rounded-full"
                    style={{
                      width: `${Math.max(
                        5,
                        (month.total_cost /
                          Math.max(...costs.monthly_trend.map(m => m.total_cost))) *
                          100
                      )}%`,
                    }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default MaintenanceAnalytics;
