import React, { useEffect, useState } from 'react';
import {
  getTotalVehicles,
  getVehiclesInMaintenance,
  getFleetUtilization,
  getStatusBreakdown
} from '../../backend/api/analytics';

const DataVisualization = () => {
  const [analytics, setAnalytics] = useState({
    totalVehicles: null,
    vehiclesInMaintenance: null,
    utilizationRate: null,
    statusBreakdown: [],
    loading: true,
    error: null
  });

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        setAnalytics(a => ({ ...a, loading: true, error: null }));
        // Fetch all analytics in parallel
        const [fleetUtil, maintenance, status] = await Promise.all([
          getFleetUtilization(),
          getVehiclesInMaintenance(),
          getStatusBreakdown()
        ]);
        setAnalytics({
          totalVehicles: fleetUtil.total,
          vehiclesInMaintenance: maintenance.in_maintenance,
          utilizationRate: fleetUtil.utilization_rate,
          statusBreakdown: status,
          loading: false,
          error: null
        });
      } catch (error) {
        setAnalytics(a => ({ ...a, loading: false, error: error.message || 'Failed to load analytics' }));
      }
    };
    fetchAnalytics();
  }, []);

  if (analytics.loading) {
    return (
      <div className="mt-6">
        <div className="bg-card rounded-lg shadow-md p-6 text-center">
          <p className="text-muted-foreground">Loading analytics...</p>
        </div>
      </div>
    );
  }
  if (analytics.error) {
    return (
      <div className="mt-6">
        <div className="bg-card rounded-lg shadow-md p-6 text-center text-destructive">
          <p>{analytics.error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="mt-6">
      <div className="bg-card rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold mb-4">Fleet Analytics</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <div className="bg-background p-4 rounded-md border border-border text-center">
            <h3 className="font-medium mb-2">Total Vehicles</h3>
            <div className="text-3xl font-bold">{analytics.totalVehicles}</div>
          </div>
          <div className="bg-background p-4 rounded-md border border-border text-center">
            <h3 className="font-medium mb-2">Vehicles in Maintenance</h3>
            <div className="text-3xl font-bold">{analytics.vehiclesInMaintenance}</div>
          </div>
          <div className="bg-background p-4 rounded-md border border-border text-center">
            <h3 className="font-medium mb-2">Fleet Utilization</h3>
            <div className="text-3xl font-bold">{(analytics.utilizationRate * 100).toFixed(1)}%</div>
          </div>
        </div>
        <div className="bg-background p-4 rounded-md border border-border mt-4">
          <h3 className="font-medium mb-2">Status Breakdown</h3>
          <div className="flex flex-wrap gap-4">
            {analytics.statusBreakdown.map((item, idx) => (
              <div key={idx} className="flex flex-col items-center px-4 py-2 bg-muted rounded">
                <span className="font-semibold">{item._id}</span>
                <span className="text-lg">{item.count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DataVisualization;
