import React, { useState, useEffect } from 'react';
import { AlertTriangle, TrendingUp, DollarSign } from 'lucide-react';
import { maintenanceAPI } from '../../../backend/api/maintenance';

const CostOutlierAnalytics = ({ vehicles }) => {
  const [data, setData] = useState({ outliers: [], statistics: {} });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    startDate: '',
    endDate: '',
    thresholdMultiplier: 2.0,
  });

  const fetchCostOutliers = async () => {
    try {
      setLoading(true);
      setError(null);

      const startDateTime = filters.startDate ? new Date(filters.startDate).toISOString() : null;
      const endDateTime = filters.endDate
        ? new Date(filters.endDate + 'T23:59:59').toISOString()
        : null;

      console.log('Fetching cost outliers:', {
        startDateTime,
        endDateTime,
        thresholdMultiplier: filters.thresholdMultiplier,
      });

      const response = await maintenanceAPI.getCostOutliers(
        startDateTime,
        endDateTime,
        filters.thresholdMultiplier
      );

      console.log('Cost outliers response:', response);

      setData({
        outliers: response.data?.outliers || [],
        statistics: response.data?.statistics || {},
      });
    } catch (err) {
      console.error('Error fetching cost outliers:', err);
      setError('Failed to load cost outlier analytics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCostOutliers();
  }, [filters]);

  const formatCurrency = amount => {
    return `R${(amount || 0).toLocaleString('en-ZA', { minimumFractionDigits: 2 })}`;
  };

  const formatMaintenanceType = type => {
    if (!type) return 'Unknown';
    return type.replace(/_/g, ' ').replace(/\b\w/g, letter => letter.toUpperCase());
  };

  const getVehicleName = vehicleId => {
    if (!vehicleId || !vehicles?.length) return `Vehicle ${vehicleId?.slice(-6) || ''}`;

    const vehicle = vehicles.find(v => v.id === vehicleId || v._id === vehicleId);
    if (vehicle) {
      return `${vehicle.year || ''} ${vehicle.make || ''} ${vehicle.model || ''} (${
        vehicle.license_plate || vehicle.vin || ''
      })`.trim();
    }
    return `Vehicle ${vehicleId.slice(-6)}`;
  };

  const getSeverityColor = multiplier => {
    if (multiplier >= 4) return 'border-red-500 bg-red-50 dark:bg-red-900/20';
    if (multiplier >= 3) return 'border-orange-500 bg-orange-50 dark:bg-orange-900/20';
    if (multiplier >= 2) return 'border-yellow-500 bg-yellow-50 dark:bg-yellow-900/20';
    return 'border-blue-500 bg-blue-50 dark:bg-blue-900/20';
  };

  const getSeverityIcon = multiplier => {
    if (multiplier >= 4) return <AlertTriangle className="w-5 h-5 text-red-500" />;
    if (multiplier >= 3) return <AlertTriangle className="w-5 h-5 text-orange-500" />;
    if (multiplier >= 2) return <TrendingUp className="w-5 h-5 text-yellow-500" />;
    return <TrendingUp className="w-5 h-5 text-blue-500" />;
  };

  const getSeverityLabel = multiplier => {
    if (multiplier >= 4) return 'Critical';
    if (multiplier >= 3) return 'High';
    if (multiplier >= 2) return 'Medium';
    return 'Low';
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <AlertTriangle className="w-5 h-5" />
          Cost Outlier Analysis
        </h3>

        <div className="flex flex-col sm:flex-row gap-2">
          <input
            type="date"
            value={filters.startDate}
            onChange={e => setFilters(prev => ({ ...prev, startDate: e.target.value }))}
            className="border border-border rounded-md px-3 py-2 text-sm"
            placeholder="Start date (optional)"
          />
          <input
            type="date"
            value={filters.endDate}
            onChange={e => setFilters(prev => ({ ...prev, endDate: e.target.value }))}
            className="border border-border rounded-md px-3 py-2 text-sm"
            placeholder="End date (optional)"
          />
          <select
            value={filters.thresholdMultiplier}
            onChange={e =>
              setFilters(prev => ({
                ...prev,
                thresholdMultiplier: parseFloat(e.target.value),
              }))
            }
            className="border border-border rounded-md px-3 py-2 text-sm"
          >
            <option value={1.5}>1.5x Average</option>
            <option value={2.0}>2.0x Average</option>
            <option value={2.5}>2.5x Average</option>
            <option value={3.0}>3.0x Average</option>
            <option value={4.0}>4.0x Average</option>
            <option value={5.0}>5.0x Average</option>
          </select>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <p className="text-red-600 dark:text-red-400 text-sm">{error}</p>
          <button
            onClick={fetchCostOutliers}
            className="mt-2 text-red-800 dark:text-red-200 hover:underline text-xs"
          >
            Retry
          </button>
        </div>
      )}

      {/* Statistics Summary */}
      {!loading && data.statistics && Object.keys(data.statistics).length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 rounded-lg p-4 text-center border border-border">
            <div className="text-2xl font-bold text-blue-600">
              {formatCurrency(data.statistics.average_cost)}
            </div>
            <div className="text-sm text-muted-foreground">Average Cost</div>
          </div>

          <div className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 rounded-lg p-4 text-center border border-border">
            <div className="text-2xl font-bold text-orange-600">
              {formatCurrency(data.statistics.threshold)}
            </div>
            <div className="text-sm text-muted-foreground">Outlier Threshold</div>
          </div>

          <div className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 rounded-lg p-4 text-center border border-border">
            <div className="text-2xl font-bold text-red-600">
              {data.statistics.outlier_count || 0}
            </div>
            <div className="text-sm text-muted-foreground">Outliers Found</div>
          </div>

          <div className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 rounded-lg p-4 text-center border border-border">
            <div className="text-2xl font-bold text-purple-600">
              {data.statistics.total_records || 0}
            </div>
            <div className="text-sm text-muted-foreground">Total Records</div>
          </div>
        </div>
      )}

      {/* Outliers List */}
      <div className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 rounded-lg p-6 border border-border">
        <h4 className="text-md font-semibold mb-4">
          Cost Outliers ({filters.thresholdMultiplier}x above average)
        </h4>

        {loading ? (
          <div className="space-y-4">
            {[1, 2, 3].map(i => (
              <div key={i} className="animate-pulse border border-border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="bg-muted h-4 w-48 rounded"></div>
                  <div className="bg-muted h-4 w-24 rounded"></div>
                </div>
                <div className="bg-muted h-3 w-32 rounded"></div>
              </div>
            ))}
          </div>
        ) : data.outliers && data.outliers.length > 0 ? (
          <div className="space-y-4 max-h-96 overflow-y-auto">
            {data.outliers.map((outlier, index) => (
              <div
                key={outlier.id}
                className={`border rounded-lg p-4 transition-all hover:shadow-md ${getSeverityColor(
                  outlier.cost_multiplier
                )}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      {getSeverityIcon(outlier.cost_multiplier)}
                      <span className="font-semibold">
                        {formatMaintenanceType(outlier.maintenance_type)}
                      </span>
                      <span className="text-xs px-2 py-1 bg-gray-200 dark:bg-gray-700 rounded-full">
                        {getSeverityLabel(outlier.cost_multiplier)}
                      </span>
                    </div>

                    <div className="text-sm text-muted-foreground space-y-1">
                      <div>
                        <span className="font-medium">Vehicle:</span>{' '}
                        {getVehicleName(outlier.vehicle_id)}
                      </div>
                      {outlier.title && (
                        <div>
                          <span className="font-medium">Title:</span> {outlier.title}
                        </div>
                      )}
                      <div>
                        <span className="font-medium">Date:</span>{' '}
                        {new Date(outlier.created_at).toLocaleDateString()}
                      </div>
                    </div>
                  </div>

                  <div className="text-right">
                    <div className="text-xl font-bold text-red-600 flex items-center gap-1">
                      <DollarSign className="w-4 h-4" />
                      {formatCurrency(outlier.cost)}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {outlier.cost_multiplier}x average
                    </div>
                    <div className="text-xs text-muted-foreground mt-1">
                      vs {formatCurrency(data.statistics.average_cost)} avg
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <AlertTriangle className="w-12 h-12 text-muted-foreground mx-auto mb-3" />
            <p className="text-muted-foreground">No cost outliers found</p>
            <p className="text-sm text-muted-foreground mt-1">
              {filters.thresholdMultiplier <= 2
                ? 'Try lowering the threshold multiplier'
                : 'All maintenance costs are within normal range'}
            </p>
          </div>
        )}
      </div>

      {/* Analysis Notes */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <h4 className="text-sm font-semibold text-blue-800 dark:text-blue-200 mb-2">
          Understanding Cost Outliers
        </h4>
        <div className="text-sm text-blue-700 dark:text-blue-300 space-y-1">
          <p>
            • <strong>Outliers</strong> are maintenance records with costs significantly above the
            average
          </p>
          <p>
            • <strong>Threshold</strong> determines how much above average constitutes an outlier
          </p>
          <p>
            • <strong>High outliers</strong> may indicate major repairs, premium parts, or billing
            errors
          </p>
          <p>
            • Regular review helps identify cost optimization opportunities and unusual expenses
          </p>
        </div>
      </div>
    </div>
  );
};

export default CostOutlierAnalytics;
