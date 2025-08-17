import React, { useState, useEffect, useCallback } from 'react';
import { BarChart3, TrendingUp, Calendar, Truck, AlertTriangle, Target } from 'lucide-react';
import { maintenanceAPI } from '../../backend/api/maintenance';

// Import new analytics components
import TimeframeAnalytics from './analytics/TimeframeAnalytics';
import MaintenanceTypeAnalytics from './analytics/MaintenanceTypeAnalytics';
import CostOutlierAnalytics from './analytics/CostOutlierAnalytics';
import VehicleMaintenanceAnalytics from './analytics/VehicleMaintenanceAnalytics';

const MaintenanceAnalytics = ({ vehicles }) => {
  const [analyticsData, setAnalyticsData] = useState(null);
  const [rawAnalyticsData, setRawAnalyticsData] = useState(null);
  const [costAnalytics, setCostAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [filters, setFilters] = useState({
    vehicleId: '',
    period: 'monthly',
    startDate: '',
    endDate: '',
  });

  const tabs = [
    { id: 'overview', name: 'Overview', icon: Target },
    { id: 'timeframe', name: 'Timeframe Analysis', icon: Calendar },
    { id: 'types', name: 'Maintenance Types', icon: BarChart3 },
    { id: 'outliers', name: 'Cost Outliers', icon: AlertTriangle },
    { id: 'vehicles', name: 'Vehicle Analysis', icon: Truck },
    { id: 'trends', name: 'Trends', icon: TrendingUp },
  ];

  const loadAnalytics = useCallback(async () => {
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

      // Handle nested data structure from backend
      console.log('Analytics Response:', analyticsResponse);
      console.log('Cost Response:', costResponse);

      // Extract the data from the double-nested ResponseBuilder format: { data: { data: {...} } }
      let analyticsData = {};
      let costData = {};

      // Handle analytics response - extract from double-nested structure
      if (analyticsResponse?.data?.data?.analytics) {
        analyticsData = analyticsResponse.data.data.analytics;
      } else if (analyticsResponse?.data?.analytics) {
        analyticsData = analyticsResponse.data.analytics;
      } else if (analyticsResponse?.data) {
        analyticsData = analyticsResponse.data;
      }

      // Handle cost response - extract from double-nested structure
      if (costResponse?.data?.data?.cost_analytics) {
        costData = costResponse.data.data.cost_analytics;
      } else if (costResponse?.data?.cost_analytics) {
        costData = costResponse.data.cost_analytics;
      } else if (costResponse?.data) {
        costData = costResponse.data;
      }

      // Store raw analytics data for access in components
      setRawAnalyticsData(analyticsData);

      // Transform analytics data to match expected format
      const transformedAnalytics = {
        total_records: analyticsData?.cost_analysis?.maintenance_count || 0,
        total_cost: analyticsData?.cost_analysis?.total_cost || 0,
        average_cost: analyticsData?.cost_analysis?.average_cost || 0,
        vehicles_count: analyticsData?.maintenance_summary?.total_active || 0,
        maintenance_types: [],
        high_cost_records: [],
      };

      // If we have cost_by_type, transform it to maintenance_types format
      if (costData?.cost_by_type) {
        transformedAnalytics.maintenance_types = Object.entries(costData.cost_by_type).map(
          ([type, cost]) => ({
            maintenance_type: type,
            total_cost: cost,
            count: 1, // We don't have count data from this endpoint, so defaulting to 1
          })
        );
      }

      setAnalyticsData(transformedAnalytics);
      setCostAnalytics(costData);
    } catch (err) {
      console.error('Error loading analytics:', err);
      setError('Failed to load analytics data');
    } finally {
      setLoading(false);
    }
  }, [filters.vehicleId, filters.period, filters.startDate, filters.endDate]);

  useEffect(() => {
    if (activeTab === 'overview' || activeTab === 'trends') {
      loadAnalytics();
    }
  }, [loadAnalytics, activeTab]);

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

  // Tab component for the overview
  const OverviewTab = ({
    vehicles,
    analyticsData,
    rawAnalyticsData,
    costAnalytics,
    loading,
    error,
    filters,
    setFilters,
    loadAnalytics,
    getVehicleName,
    formatCurrency,
    getMaintenanceTypeColor,
  }) => {
    // Handle the data structure correctly
    const analytics = analyticsData || {};
    const costs = costAnalytics || {};

    return (
      <div className="space-y-6">
        {/* Header and Filters */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
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
          <div className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">
                  Total Maintenance Records
                </p>
                <p className="text-2xl font-bold">{analytics?.total_records || 0}</p>
              </div>
              <div className="text-blue-500">
                <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
              </div>
            </div>
          </div>

          <div className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total Cost</p>
                <p className="text-2xl font-bold text-green-600">
                  {formatCurrency(analytics?.total_cost || 0)}
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

          <div className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Average Cost per Record</p>
                <p className="text-2xl font-bold text-purple-600">
                  {formatCurrency(analytics?.average_cost || 0)}
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

          <div className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Vehicles Serviced</p>
                <p className="text-2xl font-bold text-orange-600">
                  {analytics?.vehicles_count || 0}
                </p>
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
          <div className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold mb-4">
              Cost Breakdown by {filters.period.charAt(0).toUpperCase() + filters.period.slice(1)}
            </h3>
            {costs?.cost_by_month && Object.keys(costs.cost_by_month).length > 0 ? (
              <div className="space-y-3">
                {Object.entries(costs.cost_by_month).map(([month, data], index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-muted rounded-lg"
                  >
                    <div>
                      <p className="font-medium">{month}</p>
                      <p className="text-sm text-muted-foreground">{data.count || 0} records</p>
                    </div>
                    <div className="text-right">
                      <p className="font-bold">{formatCurrency(data.cost || 0)}</p>
                      <p className="text-sm text-muted-foreground">
                        Avg: {formatCurrency(data.average || 0)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <p className="text-muted-foreground">No monthly breakdown available</p>
                <p className="text-sm text-muted-foreground mt-2">
                  Total Cost: {formatCurrency(costs?.total_cost || 0)} | Records:{' '}
                  {costs?.record_count || 0} | Average: {formatCurrency(costs?.average_cost || 0)}
                </p>
                {costs?.cost_by_type && (
                  <div className="mt-4 text-sm">
                    <p className="font-medium mb-2">Cost by Type:</p>
                    <div className="grid grid-cols-2 gap-2 max-h-32 overflow-y-auto">
                      {Object.entries(costs.cost_by_type).map(([type, cost]) => (
                        <div key={type} className="flex justify-between">
                          <span className="capitalize">{type.replace(/_/g, ' ')}</span>
                          <span>{formatCurrency(cost)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Maintenance Type Distribution */}
          <div className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold mb-4">Maintenance Type Distribution</h3>
            {analytics?.maintenance_types && analytics.maintenance_types.length > 0 ? (
              <div className="space-y-3">
                {analytics.maintenance_types.map((type, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <span
                        className={`px-2 py-1 rounded-full text-xs ${getMaintenanceTypeColor(
                          index
                        )}`}
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
                          style={{
                            width: `${(type.count / (analytics?.total_records || 1)) * 100}%`,
                          }}
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

          {/* Recent High-Cost Maintenance */}
          <div className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold mb-4">Maintenance Overview</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                <div className="text-sm text-blue-600 dark:text-blue-400">Upcoming Maintenance</div>
                <div className="text-2xl font-bold text-blue-800 dark:text-blue-200">
                  {rawAnalyticsData?.maintenance_summary?.upcoming_count || 0}
                </div>
                <div className="text-xs text-blue-500 dark:text-blue-400">scheduled items</div>
              </div>

              <div className="p-4 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
                <div className="text-sm text-red-600 dark:text-red-400">Overdue Maintenance</div>
                <div className="text-2xl font-bold text-red-800 dark:text-red-200">
                  {rawAnalyticsData?.maintenance_summary?.overdue_count || 0}
                </div>
                <div className="text-xs text-red-500 dark:text-red-400">past due</div>
              </div>
            </div>

            {rawAnalyticsData?.performance_metrics && (
              <div className="mt-4 p-4 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
                <div className="text-sm text-green-600 dark:text-green-400 mb-1">
                  Completion Rate
                </div>
                <div className="flex items-center">
                  <div className="text-2xl font-bold text-green-800 dark:text-green-200 mr-2">
                    {rawAnalyticsData.performance_metrics.completion_rate}%
                  </div>
                  <div className="flex-1 bg-green-200 dark:bg-green-700 rounded-full h-2">
                    <div
                      className="bg-green-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${rawAnalyticsData.performance_metrics.completion_rate}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  // Tab component for trends
  const TrendsTab = ({ vehicles, costAnalytics, loading, error, formatCurrency }) => {
    // Handle the data structure correctly
    const costs = costAnalytics || {};

    return (
      <div className="space-y-6">
        {/* Monthly Trend Analysis */}
        {costs?.monthly_trend && costs.monthly_trend.length > 0 ? (
          <div className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 rounded-lg shadow-md p-6">
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
        ) : (
          <div className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold mb-4">Cost Trends</h3>
            <div className="text-center py-8">
              <p className="text-muted-foreground">No monthly trend data available</p>
              <p className="text-sm text-muted-foreground mt-2">Overall Cost Summary:</p>
              <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 bg-muted rounded-lg">
                  <p className="text-lg font-bold">{formatCurrency(costs?.total_cost || 0)}</p>
                  <p className="text-sm text-muted-foreground">Total Cost</p>
                </div>
                <div className="p-4 bg-muted rounded-lg">
                  <p className="text-lg font-bold">{costs?.record_count || 0}</p>
                  <p className="text-sm text-muted-foreground">Total Records</p>
                </div>
                <div className="p-4 bg-muted rounded-lg">
                  <p className="text-lg font-bold">{formatCurrency(costs?.average_cost || 0)}</p>
                  <p className="text-sm text-muted-foreground">Average Cost</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <h2 className="text-xl font-semibold">Maintenance Analytics</h2>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-border">
        <nav className="-mb-px flex space-x-8">
          {tabs.map(tab => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`group inline-flex items-center py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === tab.id
                    ? 'border-primary text-primary'
                    : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'
                }`}
              >
                <Icon
                  className={`-ml-0.5 mr-2 h-5 w-5 ${
                    activeTab === tab.id
                      ? 'text-primary'
                      : 'text-muted-foreground group-hover:text-foreground'
                  }`}
                />
                {tab.name}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="min-h-96">
        {activeTab === 'overview' && (
          <OverviewTab
            vehicles={vehicles}
            analyticsData={analyticsData}
            rawAnalyticsData={rawAnalyticsData}
            costAnalytics={costAnalytics}
            loading={loading}
            error={error}
            filters={filters}
            setFilters={setFilters}
            loadAnalytics={loadAnalytics}
            getVehicleName={getVehicleName}
            formatCurrency={formatCurrency}
            getMaintenanceTypeColor={getMaintenanceTypeColor}
          />
        )}

        {activeTab === 'timeframe' && <TimeframeAnalytics vehicles={vehicles} />}

        {activeTab === 'types' && <MaintenanceTypeAnalytics />}

        {activeTab === 'outliers' && <CostOutlierAnalytics vehicles={vehicles} />}

        {activeTab === 'vehicles' && <VehicleMaintenanceAnalytics vehicles={vehicles} />}

        {activeTab === 'trends' && (
          <TrendsTab
            vehicles={vehicles}
            costAnalytics={costAnalytics}
            loading={loading}
            error={error}
            formatCurrency={formatCurrency}
          />
        )}
      </div>
    </div>
  );
};

export default MaintenanceAnalytics;
