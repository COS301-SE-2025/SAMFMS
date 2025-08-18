import React, { useState, useEffect } from 'react';
import { Calendar, TrendingUp, DollarSign } from 'lucide-react';
import { maintenanceAPI } from '../../../backend/api/maintenance';

const TimeframeAnalytics = ({ vehicles }) => {
  const [data, setData] = useState({
    totalCost: null,
    recordsCount: null,
    vehiclesServiced: null,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [dateRange, setDateRange] = useState({
    startDate: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 30 days ago
    endDate: new Date().toISOString().split('T')[0], // today
  });

  const fetchTimeframeData = async () => {
    if (!dateRange.startDate || !dateRange.endDate) return;

    try {
      setLoading(true);
      setError(null);

      const startDateTime = new Date(dateRange.startDate).toISOString();
      const endDateTime = new Date(dateRange.endDate + 'T23:59:59').toISOString();

      console.log('Fetching timeframe data:', { startDateTime, endDateTime });

      const [costResponse, countResponse, vehiclesResponse] = await Promise.all([
        maintenanceAPI.getTotalCostTimeframe(startDateTime, endDateTime),
        maintenanceAPI.getRecordsCountTimeframe(startDateTime, endDateTime),
        maintenanceAPI.getVehiclesServicedTimeframe(startDateTime, endDateTime),
      ]);

      console.log('Timeframe analytics responses:', {
        costResponse,
        countResponse,
        vehiclesResponse,
      });

      // Handle the double-nested response structure: { data: { data: { ... } } }
      // Extract total_cost from the response
      let totalCost = 0;
      if (costResponse?.data?.data?.total_cost) {
        totalCost = costResponse.data.data.total_cost;
      } else if (costResponse?.data?.total_cost) {
        totalCost = costResponse.data.total_cost;
      }

      // Extract records_count from the response
      let recordsCount = 0;
      if (countResponse?.data?.data?.records_count) {
        recordsCount = countResponse.data.data.records_count;
      } else if (countResponse?.data?.records_count) {
        recordsCount = countResponse.data.records_count;
      }

      // Extract vehicles_serviced from the response
      let vehiclesServiced = 0;
      if (vehiclesResponse?.data?.data?.vehicles_serviced) {
        vehiclesServiced = vehiclesResponse.data.data.vehicles_serviced;
      } else if (vehiclesResponse?.data?.vehicles_serviced) {
        vehiclesServiced = vehiclesResponse.data.vehicles_serviced;
      }

      setData({
        totalCost: totalCost,
        recordsCount: recordsCount,
        vehiclesServiced: vehiclesServiced,
      });
    } catch (err) {
      console.error('Error fetching timeframe analytics:', err);
      setError('Failed to load timeframe analytics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTimeframeData();
  }, [dateRange]);

  const formatCurrency = amount => {
    return `R${(amount || 0).toLocaleString('en-ZA', { minimumFractionDigits: 2 })}`;
  };

  const getDaysDifference = () => {
    if (!dateRange.startDate || !dateRange.endDate) return 0;
    const start = new Date(dateRange.startDate);
    const end = new Date(dateRange.endDate);
    return Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + 1;
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <Calendar className="w-5 h-5" />
          Timeframe Analytics
        </h3>

        <div className="flex flex-col sm:flex-row gap-2">
          <input
            type="date"
            value={dateRange.startDate}
            onChange={e => setDateRange(prev => ({ ...prev, startDate: e.target.value }))}
            className="border border-border rounded-md px-3 py-2 text-sm"
          />
          <input
            type="date"
            value={dateRange.endDate}
            onChange={e => setDateRange(prev => ({ ...prev, endDate: e.target.value }))}
            className="border border-border rounded-md px-3 py-2 text-sm"
          />
        </div>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <p className="text-red-600 dark:text-red-400 text-sm">{error}</p>
          <button
            onClick={fetchTimeframeData}
            className="mt-2 text-red-800 dark:text-red-200 hover:underline text-xs"
          >
            Retry
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Total Cost Card */}
        <div className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-950 dark:to-green-900 rounded-lg p-4 border border-green-200 dark:border-green-800">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-green-700 dark:text-green-300">Total Cost</p>
              <p className="text-xl font-bold text-green-800 dark:text-green-200">
                {loading ? (
                  <div className="animate-pulse bg-green-200 dark:bg-green-700 h-6 w-24 rounded"></div>
                ) : (
                  formatCurrency(data.totalCost)
                )}
              </p>
              <p className="text-xs text-green-600 dark:text-green-400 mt-1">
                {getDaysDifference()} days period
              </p>
            </div>
            <div className="text-green-600 dark:text-green-400">
              <DollarSign className="w-8 h-8" />
            </div>
          </div>
        </div>

        {/* Records Count Card */}
        <div className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-950 dark:to-blue-900 rounded-lg p-4 border border-blue-200 dark:border-blue-800">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-blue-700 dark:text-blue-300">
                Maintenance Records
              </p>
              <p className="text-xl font-bold text-blue-800 dark:text-blue-200">
                {loading ? (
                  <div className="animate-pulse bg-blue-200 dark:bg-blue-700 h-6 w-16 rounded"></div>
                ) : (
                  data.recordsCount
                )}
              </p>
              <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                {data.recordsCount > 0
                  ? `Avg ${(data.recordsCount / getDaysDifference()).toFixed(1)}/day`
                  : 'No records'}
              </p>
            </div>
            <div className="text-blue-600 dark:text-blue-400">
              <TrendingUp className="w-8 h-8" />
            </div>
          </div>
        </div>

        {/* Vehicles Serviced Card */}
        <div className="bg-gradient-to-br from-orange-50 to-orange-100 dark:from-orange-950 dark:to-orange-900 rounded-lg p-4 border border-orange-200 dark:border-orange-800">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-orange-700 dark:text-orange-300">
                Vehicles Serviced
              </p>
              <p className="text-xl font-bold text-orange-800 dark:text-orange-200">
                {loading ? (
                  <div className="animate-pulse bg-orange-200 dark:bg-orange-700 h-6 w-16 rounded"></div>
                ) : (
                  data.vehiclesServiced
                )}
              </p>
              <p className="text-xs text-orange-600 dark:text-orange-400 mt-1">
                {data.vehiclesServiced > 0 && vehicles?.length > 0
                  ? `${((data.vehiclesServiced / vehicles.length) * 100).toFixed(1)}% of fleet`
                  : 'Unique vehicles'}
              </p>
            </div>
            <div className="text-orange-600 dark:text-orange-400">
              <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
                <path d="M8 16.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0zM15 16.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0z"></path>
                <path d="M3 4a1 1 0 00-1 1v10a1 1 0 001 1h1.05a2.5 2.5 0 014.9 0H10a1 1 0 001-1V5a1 1 0 00-1-1H3zM14 7a1 1 0 00-1 1v6.05A2.5 2.5 0 0115.95 16H17a1 1 0 001-1V8a1 1 0 00-1-1h-3z"></path>
              </svg>
            </div>
          </div>
        </div>
      </div>

      {/* Additional insights */}
      {!loading && data.totalCost > 0 && data.recordsCount > 0 && (
        <div className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 rounded-lg p-4 border border-border">
          <h4 className="text-sm font-semibold mb-2">Quick Insights</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <p className="text-muted-foreground">Avg Cost/Record</p>
              <p className="font-semibold">{formatCurrency(data.totalCost / data.recordsCount)}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Avg Cost/Vehicle</p>
              <p className="font-semibold">
                {data.vehiclesServiced > 0
                  ? formatCurrency(data.totalCost / data.vehiclesServiced)
                  : 'N/A'}
              </p>
            </div>
            <div>
              <p className="text-muted-foreground">Records/Vehicle</p>
              <p className="font-semibold">
                {data.vehiclesServiced > 0
                  ? (data.recordsCount / data.vehiclesServiced).toFixed(1)
                  : 'N/A'}
              </p>
            </div>
            <div>
              <p className="text-muted-foreground">Daily Avg Cost</p>
              <p className="font-semibold">
                {formatCurrency(data.totalCost / getDaysDifference())}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TimeframeAnalytics;
