import React, { useState, useEffect } from 'react';
import Chart from 'react-apexcharts';
import { TrendingUp, TrendingDown, AlertTriangle, Target, Shield, BarChart3, Activity, Users } from 'lucide-react';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://samfms.co.za/api';

const DriverBehaviorAnalytics = ({ driverData }) => {
  const [analyticsData, setAnalyticsData] = useState({
    violationTrends: null,
    riskDistribution: null,
    performanceMetrics: null,
    violationComparison: null
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedPeriod, setSelectedPeriod] = useState('30d');

  // Fetch analytics data from our new endpoints
  const fetchAnalyticsData = async (period = '30d') => {
    setLoading(true);
    setError(null);
    
    try {
      const cacheBuster = Date.now();
      const [trendsRes, riskRes, metricsRes, comparisonRes] = await Promise.all([
        fetch(`${API_BASE_URL}/trips/driver-behavior/violation-trends?period=${period}&_t=${cacheBuster}`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
          }
        }),
        fetch(`${API_BASE_URL}/trips/driver-behavior/risk-distribution?_t=${cacheBuster}`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
          }
        }),
        fetch(`${API_BASE_URL}/trips/driver-behavior/performance-metrics?period=${period}&_t=${cacheBuster}`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
          }
        }),
        fetch(`${API_BASE_URL}/trips/driver-behavior/violation-comparison?period=${period}&_t=${cacheBuster}`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
          }
        })
      ]);

      const [trends, risk, metrics, comparison] = await Promise.all([
        trendsRes.ok ? trendsRes.json() : null,
        riskRes.ok ? riskRes.json() : null,
        metricsRes.ok ? metricsRes.json() : null,
        comparisonRes.ok ? comparisonRes.json() : null
      ]);

      setAnalyticsData({
        violationTrends: trends?.data,
        riskDistribution: risk?.data,
        performanceMetrics: metrics?.data,
        violationComparison: comparison?.data
      });
    } catch (err) {
      setError('Failed to load analytics data');
      console.error('Analytics fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalyticsData(selectedPeriod);
  }, [selectedPeriod]);

  // Chart configurations
  const getViolationTrendsChart = () => {
    if (!analyticsData.violationTrends?.trends) return null;

    const trends = analyticsData.violationTrends.trends;
    const categories = trends.speeding?.map(item => item.date) || [];
    
    return {
      options: {
        chart: {
          type: 'line',
          height: 350,
          toolbar: { show: false },
          zoom: { enabled: false }
        },
        colors: ['#ef4444', '#f97316', '#eab308', '#8b5cf6'],
        dataLabels: { enabled: false },
        stroke: {
          curve: 'smooth',
          width: 3
        },
        grid: {
          borderColor: '#f1f5f9',
          strokeDashArray: 5
        },
        xaxis: {
          categories: categories,
          labels: {
            style: { colors: '#64748b', fontSize: '12px' }
          }
        },
        yaxis: {
          labels: {
            style: { colors: '#64748b', fontSize: '12px' }
          }
        },
        legend: {
          position: 'top',
          horizontalAlign: 'left'
        },
        tooltip: {
          shared: true,
          intersect: false
        }
      },
      series: [
        {
          name: 'Speeding',
          data: trends.speeding?.map(item => item.count) || []
        },
        {
          name: 'Harsh Braking',
          data: trends.braking?.map(item => item.count) || []
        },
        {
          name: 'Rapid Acceleration',
          data: trends.acceleration?.map(item => item.count) || []
        },
        {
          name: 'Phone Usage',
          data: trends.phone_usage?.map(item => item.count) || []
        }
      ]
    };
  };

  const getRiskDistributionChart = () => {
    if (!analyticsData.riskDistribution?.distribution) return null;

    const distribution = analyticsData.riskDistribution.distribution;
    
    return {
      options: {
        chart: {
          type: 'donut',
          height: 350
        },
        colors: ['#22c55e', '#f59e0b', '#ef4444'],
        labels: ['Low Risk', 'Medium Risk', 'High Risk'],
        dataLabels: {
          enabled: true,
          formatter: function (val) {
            return Math.round(val) + '%';
          }
        },
        legend: {
          position: 'bottom'
        },
        tooltip: {
          y: {
            formatter: function (val, opts) {
              const label = opts.w.globals.labels[opts.seriesIndex];
              return `${label}: ${val} drivers (${Math.round(opts.percent)}%)`;
            }
          }
        }
      },
      series: [
        distribution.low_risk || 0,
        distribution.medium_risk || 0,
        distribution.high_risk || 0
      ]
    };
  };

  const getViolationComparisonChart = () => {
    if (!analyticsData.violationComparison?.comparison) return null;

    const comparison = analyticsData.violationComparison.comparison;
    
    return {
      options: {
        chart: {
          type: 'bar',
          height: 350,
          toolbar: { show: false }
        },
        colors: ['#3b82f6', '#ef4444', '#f59e0b', '#8b5cf6'],
        plotOptions: {
          bar: {
            borderRadius: 4,
            horizontal: false,
            columnWidth: '60%'
          }
        },
        dataLabels: { enabled: false },
        xaxis: {
          categories: ['Speeding', 'Harsh Braking', 'Rapid Acceleration', 'Phone Usage'],
          labels: {
            style: { colors: '#64748b', fontSize: '12px' }
          }
        },
        yaxis: {
          labels: {
            style: { colors: '#64748b', fontSize: '12px' }
          }
        },
        grid: {
          borderColor: '#f1f5f9',
          strokeDashArray: 5
        },
        tooltip: {
          y: {
            formatter: function (val) {
              return val + ' violations';
            }
          }
        }
      },
      series: [{
        name: 'Violations',
        data: [
          comparison.speeding?.count || 0,
          comparison.braking?.count || 0,
          comparison.acceleration?.count || 0,
          comparison.phone_usage?.count || 0
        ]
      }]
    };
  };

  const getSafetyScoreChart = () => {
    if (!analyticsData.riskDistribution?.safety_score_ranges) return null;

    const ranges = analyticsData.riskDistribution.safety_score_ranges;
    
    return {
      options: {
        chart: {
          type: 'bar',
          height: 350,
          toolbar: { show: false }
        },
        colors: ['#22c55e', '#3b82f6', '#f59e0b', '#ef4444'],
        plotOptions: {
          bar: {
            borderRadius: 4,
            horizontal: true,
            barHeight: '60%'
          }
        },
        dataLabels: { enabled: false },
        xaxis: {
          labels: {
            style: { colors: '#64748b', fontSize: '12px' }
          }
        },
        yaxis: {
          labels: {
            style: { colors: '#64748b', fontSize: '12px' }
          }
        },
        grid: {
          borderColor: '#f1f5f9',
          strokeDashArray: 5
        },
        tooltip: {
          y: {
            formatter: function (val) {
              return val + ' drivers';
            }
          }
        }
      },
      series: [{
        name: 'Drivers',
        data: [
          { x: 'Excellent (90-100)', y: ranges.excellent || 0 },
          { x: 'Good (80-89)', y: ranges.good || 0 },
          { x: 'Fair (70-79)', y: ranges.fair || 0 },
          { x: 'Poor (<70)', y: ranges.poor || 0 }
        ]
      }]
    };
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-red-800 mb-2">Error Loading Analytics</h3>
          <p className="text-red-600 mb-4">{error}</p>
          <button 
            onClick={() => fetchAnalyticsData(selectedPeriod)}
            className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const performanceMetrics = analyticsData.performanceMetrics;
  const violationMetrics = performanceMetrics?.violation_metrics;
  const safetyMetrics = performanceMetrics?.safety_metrics;
  const operationalMetrics = performanceMetrics?.operational_metrics;

  return (
    <div className="space-y-6">
      {/* Period Selector */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Driver Behavior Analytics</h2>
        <div className="flex space-x-2">
          {['7d', '30d', '90d'].map(period => (
            <button
              key={period}
              onClick={() => setSelectedPeriod(period)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                selectedPeriod === period
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700'
              }`}
            >
              {period === '7d' ? '7 Days' : period === '30d' ? '30 Days' : '90 Days'}
            </button>
          ))}
        </div>
      </div>

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-slate-200 dark:border-slate-700">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
              <Shield className="h-6 w-6 text-blue-600 dark:text-blue-400" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-slate-600 dark:text-slate-400">Avg Safety Score</p>
              <p className="text-2xl font-semibold text-slate-900 dark:text-white">
                {safetyMetrics?.avg_safety_score || 'N/A'}
              </p>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                Range: {safetyMetrics?.min_safety_score || 0} - {safetyMetrics?.max_safety_score || 100}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-slate-200 dark:border-slate-700">
          <div className="flex items-center">
            <div className="p-2 bg-red-100 dark:bg-red-900 rounded-lg">
              <AlertTriangle className="h-6 w-6 text-red-600 dark:text-red-400" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-slate-600 dark:text-slate-400">Total Violations</p>
              <p className="text-2xl font-semibold text-slate-900 dark:text-white">
                {violationMetrics?.total_violations || 0}
              </p>
              <p className="text-sm flex items-center">
                {violationMetrics?.improvement_rate !== undefined && (
                  <>
                    {violationMetrics.improvement_rate > 0 ? (
                      <TrendingDown className="h-4 w-4 text-green-500 mr-1" />
                    ) : (
                      <TrendingUp className="h-4 w-4 text-red-500 mr-1" />
                    )}
                    <span className={violationMetrics.improvement_rate > 0 ? 'text-green-600' : 'text-red-600'}>
                      {Math.abs(violationMetrics.improvement_rate).toFixed(1)}%
                    </span>
                  </>
                )}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-slate-200 dark:border-slate-700">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
              <Target className="h-6 w-6 text-green-600 dark:text-green-400" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-slate-600 dark:text-slate-400">Trip Completion Rate</p>
              <p className="text-2xl font-semibold text-slate-900 dark:text-white">
                {operationalMetrics?.trip_completion_rate || 0}%
              </p>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                {operationalMetrics?.completed_trips || 0} / {operationalMetrics?.total_trips || 0} trips
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-slate-200 dark:border-slate-700">
          <div className="flex items-center">
            <div className="p-2 bg-purple-100 dark:bg-purple-900 rounded-lg">
              <Users className="h-6 w-6 text-purple-600 dark:text-purple-400" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-slate-600 dark:text-slate-400">Active Drivers</p>
              <p className="text-2xl font-semibold text-slate-900 dark:text-white">
                {operationalMetrics?.total_drivers || 0}
              </p>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                Avg completion: {operationalMetrics?.avg_driver_completion_rate || 0}%
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-slate-200 dark:border-slate-700">
          <div className="flex items-center mb-4">
            <Activity className="h-5 w-5 text-slate-600 dark:text-slate-400 mr-2" />
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Violation Trends</h3>
          </div>
          {analyticsData.violationTrends?.trends ? (
            <Chart
              options={getViolationTrendsChart().options}
              series={getViolationTrendsChart().series}
              type="line"
              height={350}
            />
          ) : (
            <div className="flex items-center justify-center h-80 text-slate-500">
              No trend data available
            </div>
          )}
        </div>

        <div className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-slate-200 dark:border-slate-700">
          <div className="flex items-center mb-4">
            <Target className="h-5 w-5 text-slate-600 dark:text-slate-400 mr-2" />
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Driver Risk Distribution</h3>
          </div>
          {analyticsData.riskDistribution?.distribution ? (
            <Chart
              options={getRiskDistributionChart().options}
              series={getRiskDistributionChart().series}
              type="donut"
              height={350}
            />
          ) : (
            <div className="flex items-center justify-center h-80 text-slate-500">
              No risk distribution data available
            </div>
          )}
        </div>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-slate-200 dark:border-slate-700">
          <div className="flex items-center mb-4">
            <BarChart3 className="h-5 w-5 text-slate-600 dark:text-slate-400 mr-2" />
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Violation Comparison</h3>
          </div>
          {analyticsData.violationComparison?.comparison ? (
            <Chart
              options={getViolationComparisonChart().options}
              series={getViolationComparisonChart().series}
              type="bar"
              height={350}
            />
          ) : (
            <div className="flex items-center justify-center h-80 text-slate-500">
              No comparison data available
            </div>
          )}
        </div>

        <div className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-slate-200 dark:border-slate-700">
          <div className="flex items-center mb-4">
            <Shield className="h-5 w-5 text-slate-600 dark:text-slate-400 mr-2" />
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Safety Score Distribution</h3>
          </div>
          {analyticsData.riskDistribution?.safety_score_ranges ? (
            <Chart
              options={getSafetyScoreChart().options}
              series={getSafetyScoreChart().series}
              type="bar"
              height={350}
            />
          ) : (
            <div className="flex items-center justify-center h-80 text-slate-500">
              No safety score data available
            </div>
          )}
        </div>
      </div>

      {/* Top/Worst Performers Section */}
      {analyticsData.riskDistribution?.top_performers && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-slate-200 dark:border-slate-700">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4 flex items-center">
              <TrendingUp className="h-5 w-5 text-green-600 mr-2" />
              Top Performers
            </h3>
            <div className="space-y-3">
              {analyticsData.riskDistribution.top_performers.slice(0, 5).map((driver, index) => (
                <div key={driver.driver_id} className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-700 rounded-lg">
                  <div className="flex items-center">
                    <div className="w-8 h-8 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center text-green-600 dark:text-green-400 font-semibold text-sm mr-3">
                      {index + 1}
                    </div>
                    <div>
                      <p className="font-medium text-slate-900 dark:text-white">{driver.driver_name}</p>
                      <p className="text-sm text-slate-500 dark:text-slate-400">{driver.total_violations} violations</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-green-600 dark:text-green-400">{driver.safety_score}</p>
                    <p className="text-sm text-slate-500 dark:text-slate-400">{driver.completion_rate}% completion</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-slate-200 dark:border-slate-700">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4 flex items-center">
              <TrendingDown className="h-5 w-5 text-red-600 mr-2" />
              Needs Improvement
            </h3>
            <div className="space-y-3">
              {analyticsData.riskDistribution.worst_performers.slice(0, 5).map((driver, index) => (
                <div key={driver.driver_id} className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-700 rounded-lg">
                  <div className="flex items-center">
                    <div className="w-8 h-8 bg-red-100 dark:bg-red-900 rounded-full flex items-center justify-center text-red-600 dark:text-red-400 font-semibold text-sm mr-3">
                      {index + 1}
                    </div>
                    <div>
                      <p className="font-medium text-slate-900 dark:text-white">{driver.driver_name}</p>
                      <p className="text-sm text-slate-500 dark:text-slate-400">{driver.total_violations} violations</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-red-600 dark:text-red-400">{driver.safety_score}</p>
                    <p className="text-sm text-slate-500 dark:text-slate-400">{driver.completion_rate}% completion</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DriverBehaviorAnalytics;