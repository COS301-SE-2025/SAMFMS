import React, { useState, useEffect, useCallback, useRef } from 'react';
import { 
  Users, 
  TrendingUp, 
  TrendingDown, 
  Shield, 
  AlertTriangle, 
  Car, 
  Phone, 
  Gauge, 
  Award, 
  Bell, 
  Clock,
  MapPin,
  Zap,
  AlertCircle
} from 'lucide-react';
import { 
  getAllDriverHistories, 
  getRiskDistribution, 
  calculateDashboardMetrics, 
  getTopPerformers,
  getRecentDriverAlerts,
  formatScore
} from '../../backend/api/driverBehavior';

const DriverBehaviorDashboard = ({ driverData: propDriverData, onDataUpdate }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [dashboardData, setDashboardData] = useState({
    drivers: propDriverData || [],
    metrics: null,
    riskDistribution: null,
    topPerformers: [],
    recentAlerts: []
  });

  // Use ref to store the onDataUpdate callback to avoid dependency issues
  const onDataUpdateRef = useRef(onDataUpdate);
  useEffect(() => {
    onDataUpdateRef.current = onDataUpdate;
  }, [onDataUpdate]);

  // Load data on component mount and when propDriverData changes
  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Fetch all driver histories
        const driversResponse = await getAllDriverHistories({ limit: 1000 });
        const drivers = driversResponse.drivers || [];

        // Calculate dashboard metrics
        const metrics = calculateDashboardMetrics(drivers);

        // Get top performers
        const topPerformers = getTopPerformers(drivers, 3);

        // Fetch risk distribution from backend
        let riskDistribution = null;
        try {
          const riskResponse = await getRiskDistribution();
          riskDistribution = riskResponse.distribution;
        } catch (riskError) {
          console.warn('Could not fetch risk distribution from backend, using calculated values:', riskError);
          riskDistribution = {
            high: { count: metrics.riskDistribution.high, percentage: (metrics.riskDistribution.high / metrics.totalDrivers * 100) || 0 },
            medium: { count: metrics.riskDistribution.medium, percentage: (metrics.riskDistribution.medium / metrics.totalDrivers * 100) || 0 },
            low: { count: metrics.riskDistribution.low, percentage: (metrics.riskDistribution.low / metrics.totalDrivers * 100) || 0 }
          };
        }

        // Fetch recent alerts
        let recentAlerts = [];
        try {
          const alertsResponse = await getRecentDriverAlerts({ limit: 5, hours_back: 24 });
          recentAlerts = alertsResponse.alerts || [];
        } catch (alertsError) {
          console.warn('Could not fetch recent alerts:', alertsError);
        }

        const newDashboardData = {
          drivers,
          metrics,
          riskDistribution,
          topPerformers,
          recentAlerts
        };

        setDashboardData(newDashboardData);

        // Notify parent component of data update
        if (onDataUpdateRef.current) {
          onDataUpdateRef.current(drivers);
        }

      } catch (err) {
        console.error('Error loading dashboard data:', err);
        setError('Failed to load driver behavior data. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    if (propDriverData && propDriverData.length > 0) {
      // Use provided data and calculate metrics
      const metrics = calculateDashboardMetrics(propDriverData);
      const topPerformers = getTopPerformers(propDriverData, 3);
      
      setDashboardData({
        drivers: propDriverData,
        metrics,
        riskDistribution: {
          high: { count: metrics.riskDistribution.high, percentage: (metrics.riskDistribution.high / metrics.totalDrivers * 100) || 0 },
          medium: { count: metrics.riskDistribution.medium, percentage: (metrics.riskDistribution.medium / metrics.totalDrivers * 100) || 0 },
          low: { count: metrics.riskDistribution.low, percentage: (metrics.riskDistribution.low / metrics.totalDrivers * 100) || 0 }
        },
        topPerformers,
        recentAlerts: []
      });
      
      // Notify parent without causing re-render loop
      if (onDataUpdateRef.current) {
        onDataUpdateRef.current(propDriverData);
      }
    } else {
      // Load data from API only once on mount
      loadDashboardData();
    }
  }, [propDriverData]); // Only depend on propDriverData

  // Separate function for retry functionality
  const retryLoad = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch all driver histories
      const driversResponse = await getAllDriverHistories({ limit: 1000 });
      const drivers = driversResponse.drivers || [];

      // Calculate dashboard metrics
      const metrics = calculateDashboardMetrics(drivers);

      // Get top performers
      const topPerformers = getTopPerformers(drivers, 3);

      // Fetch risk distribution from backend
      let riskDistribution = null;
      try {
        const riskResponse = await getRiskDistribution();
        riskDistribution = riskResponse.distribution;
      } catch (riskError) {
        console.warn('Could not fetch risk distribution from backend, using calculated values:', riskError);
        riskDistribution = {
          high: { count: metrics.riskDistribution.high, percentage: (metrics.riskDistribution.high / metrics.totalDrivers * 100) || 0 },
          medium: { count: metrics.riskDistribution.medium, percentage: (metrics.riskDistribution.medium / metrics.totalDrivers * 100) || 0 },
          low: { count: metrics.riskDistribution.low, percentage: (metrics.riskDistribution.low / metrics.totalDrivers * 100) || 0 }
        };
      }

      const newDashboardData = {
        drivers,
        metrics,
        riskDistribution,
        topPerformers
      };

      setDashboardData(newDashboardData);

      // Notify parent component of data update
      if (onDataUpdateRef.current) {
        onDataUpdateRef.current(drivers);
      }

    } catch (err) {
      console.error('Error loading dashboard data:', err);
      setError('Failed to load driver behavior data. Please try again.');
    } finally {
      setLoading(false);
    }
  }, []); // No dependencies needed since we use refs

  const { drivers, metrics, riskDistribution, topPerformers } = dashboardData;

  // Calculate summary statistics with fallbacks
  const totalDrivers = metrics?.totalDrivers || drivers.length;
  const averageScore = metrics?.averageScore || 0;
  const totalSpeedingEvents = metrics?.totalSpeedingEvents || 0;
  const totalHarshBraking = metrics?.totalHarshBraking || 0;

  // Calculate risk levels with fallbacks
  const highRiskDrivers = riskDistribution?.high?.count || drivers.filter(driver => parseFloat(driver.overallScore || 0) < 7).length;
  const mediumRiskDrivers = riskDistribution?.medium?.count || drivers.filter(driver => {
    const score = parseFloat(driver.overallScore || 0);
    return score >= 7 && score < 8.5;
  }).length;
  const lowRiskDrivers = riskDistribution?.low?.count || drivers.filter(driver => parseFloat(driver.overallScore || 0) >= 8.5).length;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-lg">Loading dashboard data...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
        <h3 className="text-red-800 dark:text-red-200 font-semibold">Error Loading Dashboard</h3>
        <p className="text-red-600 dark:text-red-400 mt-2">{error}</p>
        <button
          onClick={retryLoad}
          className="mt-4 bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 transition"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Total Drivers Card */}
        <div className="group bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-600 dark:text-slate-300 mb-2">Total Drivers</p>
              <p className="text-3xl font-bold text-slate-900 dark:text-slate-100">{totalDrivers}</p>
              <div className="flex items-center mt-2">
                <div className="w-2 h-2 bg-slate-500 rounded-full mr-2 animate-pulse"></div>
                <p className="text-xs text-slate-600 dark:text-slate-400">Active monitoring</p>
              </div>
            </div>
            <div className="h-14 w-14 bg-slate-500 dark:bg-slate-600 rounded-xl flex items-center justify-center shadow-md group-hover:shadow-lg group-hover:scale-110 transition-all duration-300">
              <Users className="w-8 h-8 text-white" />
            </div>
          </div>
        </div>

        {/* Average Score Card */}
        <div className="group bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-600 dark:text-slate-300 mb-2">Average Score</p>
              <p className="text-3xl font-bold text-slate-900 dark:text-slate-100">{averageScore}/10</p>
              <div className="flex items-center mt-2">
                <div className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"></div>
                <p className="text-xs text-slate-600 dark:text-slate-400">Safety rating</p>
              </div>
            </div>
            <div className="h-14 w-14 bg-green-500 dark:bg-green-600 rounded-xl flex items-center justify-center shadow-md group-hover:shadow-lg group-hover:scale-110 transition-all duration-300">
              <Shield className="w-8 h-8 text-white" />
            </div>
          </div>
        </div>

        {/* Speeding Events Card */}
        <div className="group bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-600 dark:text-slate-300 mb-2">Speeding Events</p>
              <p className="text-3xl font-bold text-slate-900 dark:text-slate-100">{totalSpeedingEvents}</p>
              <div className="flex items-center mt-2">
                <div className="w-2 h-2 bg-red-500 rounded-full mr-2 animate-pulse"></div>
                <p className="text-xs text-slate-600 dark:text-slate-400">Violations detected</p>
              </div>
            </div>
            <div className="h-14 w-14 bg-red-500 dark:bg-red-600 rounded-xl flex items-center justify-center shadow-md group-hover:shadow-lg group-hover:scale-110 transition-all duration-300">
              <Gauge className="w-8 h-8 text-white" />
            </div>
          </div>
        </div>

        {/* Harsh Braking Card */}
        <div className="group bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-600 dark:text-slate-300 mb-2">Harsh Braking</p>
              <p className="text-3xl font-bold text-slate-900 dark:text-slate-100">{totalHarshBraking}</p>
              <div className="flex items-center mt-2">
                <div className="w-2 h-2 bg-orange-500 rounded-full mr-2 animate-pulse"></div>
                <p className="text-xs text-slate-600 dark:text-slate-400">Incidents recorded</p>
              </div>
            </div>
            <div className="h-14 w-14 bg-orange-500 dark:bg-orange-600 rounded-xl flex items-center justify-center shadow-md group-hover:shadow-lg group-hover:scale-110 transition-all duration-300">
              <AlertTriangle className="w-8 h-8 text-white" />
            </div>
          </div>
        </div>
      </div>

      {/* Risk Level Distribution */}
      <div className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-lg p-6">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-6 flex items-center">
          <TrendingDown className="w-6 h-6 mr-3 text-slate-600 dark:text-slate-400" />
          Risk Level Distribution
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="group bg-gradient-to-br from-red-50 to-red-100 dark:from-red-950 dark:to-red-900 border border-red-200 dark:border-red-800 rounded-xl p-6 text-center hover:shadow-lg transition-all duration-300 hover:scale-105">
            <div className="text-4xl font-bold text-red-600 dark:text-red-400 mb-2">{highRiskDrivers}</div>
            <div className="text-sm font-medium text-red-600 dark:text-red-400 mb-1">High Risk</div>
            <div className="text-xs text-red-500 dark:text-red-500">Score &lt; 7.0</div>
          </div>
          <div className="group bg-gradient-to-br from-yellow-50 to-yellow-100 dark:from-yellow-950 dark:to-yellow-900 border border-yellow-200 dark:border-yellow-800 rounded-xl p-6 text-center hover:shadow-lg transition-all duration-300 hover:scale-105">
            <div className="text-4xl font-bold text-yellow-600 dark:text-yellow-400 mb-2">{mediumRiskDrivers}</div>
            <div className="text-sm font-medium text-yellow-600 dark:text-yellow-400 mb-1">Medium Risk</div>
            <div className="text-xs text-yellow-500 dark:text-yellow-500">Score 7.0 - 8.4</div>
          </div>
          <div className="group bg-gradient-to-br from-green-50 to-green-100 dark:from-green-950 dark:to-green-900 border border-green-200 dark:border-green-800 rounded-xl p-6 text-center hover:shadow-lg transition-all duration-300 hover:scale-105">
            <div className="text-4xl font-bold text-green-600 dark:text-green-400 mb-2">{lowRiskDrivers}</div>
            <div className="text-sm font-medium text-green-600 dark:text-green-400 mb-1">Low Risk</div>
            <div className="text-xs text-green-500 dark:text-green-500">Score ≥ 8.5</div>
          </div>
        </div>
      </div>

      {/* Recent Alerts */}
      <div className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-lg p-6">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-6 flex items-center">
          <Bell className="w-6 h-6 mr-3 text-slate-600 dark:text-slate-400" />
          Recent Alerts
        </h3>
        <div className="space-y-4">
          {dashboardData.recentAlerts && dashboardData.recentAlerts.length > 0 ? (
            dashboardData.recentAlerts.map((alert, index) => (
              <div key={alert.id || index} className="group flex items-center p-4 bg-gradient-to-r from-red-50 to-red-100 dark:from-red-950 dark:to-red-900 rounded-xl border border-red-200 dark:border-red-800 hover:shadow-md transition-all duration-300">
                <div className="h-10 w-10 bg-red-500 dark:bg-red-600 rounded-full flex items-center justify-center mr-4 group-hover:scale-110 transition-transform">
                  {alert.type === 'speeding' && <Gauge className="w-5 h-5 text-white" />}
                  {alert.type === 'harsh_braking' && <AlertTriangle className="w-5 h-5 text-white" />}
                  {alert.type === 'rapid_acceleration' && <Zap className="w-5 h-5 text-white" />}
                  {alert.type === 'phone_usage' && <Phone className="w-5 h-5 text-white" />}
                  {!['speeding', 'harsh_braking', 'rapid_acceleration', 'phone_usage'].includes(alert.type) && <AlertCircle className="w-5 h-5 text-white" />}
                </div>
                <div className="flex-1">
                  <p className="font-semibold text-red-800 dark:text-red-200 capitalize">{alert.type.replace('_', ' ')}</p>
                  <p className="text-sm text-red-600 dark:text-red-400">{alert.driver_name} - {alert.details}</p>
                  <div className="flex items-center mt-1">
                    <MapPin className="w-3 h-3 mr-1 text-red-500" />
                    <p className="text-xs text-red-500 dark:text-red-400">{alert.location}</p>
                  </div>
                </div>
                <div className="flex flex-col items-end">
                  <span className={`text-sm font-medium px-3 py-1 rounded-full ${
                    alert.severity === 'high' ? 'text-red-600 bg-red-100 dark:bg-red-900/30' :
                    alert.severity === 'medium' ? 'text-orange-600 bg-orange-100 dark:bg-orange-900/30' :
                    'text-yellow-600 bg-yellow-100 dark:bg-yellow-900/30'
                  }`}>
                    {alert.severity}
                  </span>
                  <div className="flex items-center mt-1">
                    <Clock className="w-3 h-3 mr-1 text-slate-500" />
                    <span className="text-xs text-slate-500">
                      {alert.timestamp ? new Date(alert.timestamp).toLocaleTimeString() : 'Unknown time'}
                    </span>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="group flex items-center p-4 bg-gradient-to-r from-green-50 to-green-100 dark:from-green-950 dark:to-green-900 rounded-xl border border-green-200 dark:border-green-800">
              <div className="h-10 w-10 bg-green-500 dark:bg-green-600 rounded-full flex items-center justify-center mr-4">
                <Shield className="w-5 h-5 text-white" />
              </div>
              <div className="flex-1">
                <p className="font-semibold text-green-800 dark:text-green-200">No Recent Alerts</p>
                <p className="text-sm text-green-600 dark:text-green-400">All drivers are performing well</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Top Performers */}
      <div className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-lg p-6">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-6 flex items-center">
          <Award className="w-6 h-6 mr-3 text-slate-600 dark:text-slate-400" />
          Top Performers This Week
        </h3>
        <div className="space-y-4">
          {(topPerformers.length > 0 ? topPerformers : drivers
            .sort((a, b) => (parseFloat(b.overallScore) || 0) - (parseFloat(a.overallScore) || 0))
            .slice(0, 3))
            .map((driver, index) => (
              <div key={driver.id || driver._id || index} className="group flex items-center p-4 bg-gradient-to-r from-green-100 to-green-200 dark:from-green-800 dark:to-green-900 rounded-xl border border-green-300 dark:border-green-700 hover:shadow-lg transition-all duration-300 hover:scale-105">
                <div className="flex items-center justify-center w-12 h-12 bg-green-500 dark:bg-green-600 rounded-full mr-4 shadow-md group-hover:shadow-lg group-hover:scale-110 transition-all duration-300">
                  <span className="text-white font-bold text-lg">{index + 1}</span>
                </div>
                <div className="flex-1">
                  <p className="font-semibold text-green-900 dark:text-green-100">{driver.name || driver.driver_name || 'Unknown Driver'}</p>
                  <p className="text-sm text-green-700 dark:text-green-300">ID: {driver.employeeId || driver.driver_id || driver.id || 'N/A'}</p>
                </div>
                <div className="text-right">
                  <p className="font-bold text-green-900 dark:text-green-100 text-lg">{formatScore(driver.overallScore)}/10</p>
                  <p className="text-sm text-green-700 dark:text-green-300">Safety Score</p>
                </div>
              </div>
            ))}
        </div>
      </div>
    </div>
  );
};

export default DriverBehaviorDashboard;