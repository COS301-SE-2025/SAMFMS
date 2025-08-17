import React, { useState, useEffect } from 'react';
import { Truck, BarChart3, Calendar } from 'lucide-react';
import { maintenanceAPI } from '../../../backend/api/maintenance';

const VehicleMaintenanceAnalytics = ({ vehicles }) => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [dateRange, setDateRange] = useState({
    startDate: new Date(Date.now() - 90 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 90 days ago
    endDate: new Date().toISOString().split('T')[0], // today
  });
  const [sortBy, setSortBy] = useState('maintenance_count'); // maintenance_count, total_cost, average_cost

  const fetchVehicleMaintenanceData = async () => {
    if (!dateRange.startDate || !dateRange.endDate) return;

    try {
      setLoading(true);
      setError(null);

      const startDateTime = new Date(dateRange.startDate).toISOString();
      const endDateTime = new Date(dateRange.endDate + 'T23:59:59').toISOString();

      console.log('Fetching vehicle maintenance data:', { startDateTime, endDateTime });

      const response = await maintenanceAPI.getMaintenancePerVehicleTimeframe(
        startDateTime,
        endDateTime
      );
      console.log('Vehicle maintenance response:', response);

      const vehicleData = response.data?.maintenance_per_vehicle || response.data || [];

      // Sort the data based on selected criteria
      const sortedData = [...vehicleData].sort((a, b) => {
        switch (sortBy) {
          case 'total_cost':
            return b.total_cost - a.total_cost;
          case 'average_cost':
            return b.average_cost - a.average_cost;
          case 'maintenance_count':
          default:
            return b.maintenance_count - a.maintenance_count;
        }
      });

      setData(sortedData);
    } catch (err) {
      console.error('Error fetching vehicle maintenance data:', err);
      setError('Failed to load vehicle maintenance analytics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchVehicleMaintenanceData();
  }, [dateRange, sortBy]);

  const formatCurrency = amount => {
    return `R${(amount || 0).toLocaleString('en-ZA', { minimumFractionDigits: 2 })}`;
  };

  const getVehicleName = vehicleId => {
    if (!vehicleId || !vehicles?.length) return `Vehicle ${vehicleId?.slice(-6) || ''}`;

    const vehicle = vehicles.find(v => v.id === vehicleId || v._id === vehicleId);
    if (vehicle) {
      return (
        `${vehicle.year || ''} ${vehicle.make || ''} ${vehicle.model || ''}`.trim() ||
        'Unknown Vehicle'
      );
    }
    return `Vehicle ${vehicleId.slice(-6)}`;
  };

  const getVehicleLicensePlate = vehicleId => {
    if (!vehicleId || !vehicles?.length) return '';

    const vehicle = vehicles.find(v => v.id === vehicleId || v._id === vehicleId);
    return vehicle?.license_plate || vehicle?.vin || '';
  };

  const formatMaintenanceTypes = types => {
    if (!types || !Array.isArray(types)) return '';
    return (
      types
        .slice(0, 3)
        .map(type => type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()))
        .join(', ') + (types.length > 3 ? ` (+${types.length - 3} more)` : '')
    );
  };

  const getDaysDifference = () => {
    if (!dateRange.startDate || !dateRange.endDate) return 0;
    const start = new Date(dateRange.startDate);
    const end = new Date(dateRange.endDate);
    return Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + 1;
  };

  const getMaintenanceFrequencyColor = (count, maxCount) => {
    const ratio = count / maxCount;
    if (ratio >= 0.8) return 'text-red-600 bg-red-50 dark:bg-red-900/20';
    if (ratio >= 0.6) return 'text-orange-600 bg-orange-50 dark:bg-orange-900/20';
    if (ratio >= 0.3) return 'text-yellow-600 bg-yellow-50 dark:bg-yellow-900/20';
    return 'text-green-600 bg-green-50 dark:bg-green-900/20';
  };

  const maxMaintenanceCount =
    data.length > 0 ? Math.max(...data.map(item => item.maintenance_count)) : 1;
  const maxTotalCost = data.length > 0 ? Math.max(...data.map(item => item.total_cost)) : 1;

  return (
    <div className="space-y-4">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <Truck className="w-5 h-5" />
          Maintenance per Vehicle
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
          <select
            value={sortBy}
            onChange={e => setSortBy(e.target.value)}
            className="border border-border rounded-md px-3 py-2 text-sm"
          >
            <option value="maintenance_count">Sort by Maintenance Count</option>
            <option value="total_cost">Sort by Total Cost</option>
            <option value="average_cost">Sort by Average Cost</option>
          </select>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <p className="text-red-600 dark:text-red-400 text-sm">{error}</p>
          <button
            onClick={fetchVehicleMaintenanceData}
            className="mt-2 text-red-800 dark:text-red-200 hover:underline text-xs"
          >
            Retry
          </button>
        </div>
      )}

      {/* Summary Cards */}
      {!loading && data.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 rounded-lg p-4 text-center border border-border">
            <div className="text-2xl font-bold text-blue-600">{data.length}</div>
            <div className="text-sm text-muted-foreground">Vehicles Serviced</div>
          </div>

          <div className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 rounded-lg p-4 text-center border border-border">
            <div className="text-2xl font-bold text-green-600">
              {data.reduce((sum, item) => sum + item.maintenance_count, 0)}
            </div>
            <div className="text-sm text-muted-foreground">Total Services</div>
          </div>

          <div className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 rounded-lg p-4 text-center border border-border">
            <div className="text-2xl font-bold text-purple-600">
              {formatCurrency(data.reduce((sum, item) => sum + item.total_cost, 0))}
            </div>
            <div className="text-sm text-muted-foreground">Total Cost</div>
          </div>

          <div className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 rounded-lg p-4 text-center border border-border">
            <div className="text-2xl font-bold text-orange-600">
              {(data.reduce((sum, item) => sum + item.maintenance_count, 0) / data.length).toFixed(
                1
              )}
            </div>
            <div className="text-sm text-muted-foreground">Avg Services/Vehicle</div>
          </div>
        </div>
      )}

      {/* Vehicle List */}
      <div className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 rounded-lg p-6 border border-border">
        {loading ? (
          <div className="space-y-4">
            {[1, 2, 3, 4, 5].map(i => (
              <div key={i} className="animate-pulse border border-border rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="bg-muted h-5 w-48 rounded"></div>
                  <div className="bg-muted h-5 w-24 rounded"></div>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-muted h-4 w-16 rounded"></div>
                  <div className="bg-muted h-4 w-20 rounded"></div>
                  <div className="bg-muted h-4 w-24 rounded"></div>
                  <div className="bg-muted h-4 w-18 rounded"></div>
                </div>
              </div>
            ))}
          </div>
        ) : data.length > 0 ? (
          <div className="space-y-4 max-h-96 overflow-y-auto">
            {data.map((vehicle, index) => (
              <div
                key={vehicle.vehicle_id}
                className="border border-border rounded-lg p-4 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <Truck className="w-4 h-4 text-muted-foreground" />
                      <span className="font-semibold">{getVehicleName(vehicle.vehicle_id)}</span>
                      {getVehicleLicensePlate(vehicle.vehicle_id) && (
                        <span className="text-xs bg-muted px-2 py-1 rounded-full">
                          {getVehicleLicensePlate(vehicle.vehicle_id)}
                        </span>
                      )}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      <Calendar className="w-3 h-3 inline mr-1" />
                      Latest: {new Date(vehicle.latest_maintenance).toLocaleDateString()} •
                      Earliest: {new Date(vehicle.earliest_maintenance).toLocaleDateString()}
                    </div>
                  </div>

                  <div
                    className={`px-3 py-1 rounded-full text-sm font-medium ${getMaintenanceFrequencyColor(
                      vehicle.maintenance_count,
                      maxMaintenanceCount
                    )}`}
                  >
                    {vehicle.maintenance_count} service{vehicle.maintenance_count !== 1 ? 's' : ''}
                  </div>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">Total Cost:</span>
                    <div className="font-semibold">{formatCurrency(vehicle.total_cost)}</div>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Avg Cost:</span>
                    <div className="font-semibold">{formatCurrency(vehicle.average_cost)}</div>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Service Types:</span>
                    <div className="font-semibold">{vehicle.types_count}</div>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Frequency:</span>
                    <div className="font-semibold">
                      {((vehicle.maintenance_count / getDaysDifference()) * 30).toFixed(1)}/month
                    </div>
                  </div>
                </div>

                {/* Progress bars */}
                <div className="mt-3 space-y-2">
                  <div>
                    <div className="flex justify-between text-xs text-muted-foreground mb-1">
                      <span>Maintenance Count</span>
                      <span>
                        {vehicle.maintenance_count}/{maxMaintenanceCount}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                      <div
                        className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                        style={{
                          width: `${(vehicle.maintenance_count / maxMaintenanceCount) * 100}%`,
                        }}
                      ></div>
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between text-xs text-muted-foreground mb-1">
                      <span>Cost Relative to Highest</span>
                      <span>{formatCurrency(vehicle.total_cost)}</span>
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                      <div
                        className="bg-green-500 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${(vehicle.total_cost / maxTotalCost) * 100}%` }}
                      ></div>
                    </div>
                  </div>
                </div>

                {/* Maintenance types */}
                {vehicle.maintenance_types && vehicle.maintenance_types.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-border">
                    <div className="text-xs text-muted-foreground mb-1">Service Types:</div>
                    <div className="text-sm">
                      {formatMaintenanceTypes(vehicle.maintenance_types)}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <Truck className="w-12 h-12 text-muted-foreground mx-auto mb-3" />
            <p className="text-muted-foreground">No vehicle maintenance data available</p>
            <p className="text-sm text-muted-foreground mt-1">
              {dateRange.startDate && dateRange.endDate
                ? 'No maintenance records found in the selected date range'
                : 'Select a date range to view vehicle maintenance analytics'}
            </p>
          </div>
        )}
      </div>

      {/* Analysis Notes */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <h4 className="text-sm font-semibold text-blue-800 dark:text-blue-200 mb-2">
          Vehicle Maintenance Insights
        </h4>
        <div className="text-sm text-blue-700 dark:text-blue-300 space-y-1">
          <p>
            • <strong>High maintenance count</strong> may indicate aging vehicles or heavy usage
          </p>
          <p>
            • <strong>High average cost</strong> could suggest premium parts or complex repairs
          </p>
          <p>
            • <strong>Service frequency</strong> helps identify vehicles needing attention
          </p>
          <p>
            • <strong>Service type variety</strong> shows maintenance complexity per vehicle
          </p>
        </div>
      </div>
    </div>
  );
};

export default VehicleMaintenanceAnalytics;
