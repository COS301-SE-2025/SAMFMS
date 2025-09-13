import React, { useState } from 'react';

const DriverBehaviorAnalytics = ({ driverData }) => {
  const [selectedTimeRange, setSelectedTimeRange] = useState('week');
  const [selectedMetric, setSelectedMetric] = useState('overallScore');

  // Mock data for charts (in a real app, this would come from an API)
  const generateMockTrendData = () => {
    const days = selectedTimeRange === 'week' ? 7 : selectedTimeRange === 'month' ? 30 : 90;
    return Array.from({ length: days }, (_, i) => ({
      day: i + 1,
      value: Math.random() * 10,
      events: Math.floor(Math.random() * 10)
    }));
  };

  const trendData = generateMockTrendData();

  // Calculate analytics metrics
  const analytics = {
    avgScore: (driverData.reduce((sum, d) => sum + d.overallScore, 0) / driverData.length).toFixed(1),
    totalEvents: driverData.reduce((sum, d) => sum + d.speedingEvents + d.harshBraking + d.rapidAcceleration + d.distraction, 0),
    improvement: '+12%', // Mock improvement
    riskDistribution: {
      high: driverData.filter(d => d.overallScore < 7).length,
      medium: driverData.filter(d => d.overallScore >= 7 && d.overallScore < 8.5).length,
      low: driverData.filter(d => d.overallScore >= 8.5).length
    }
  };

  // Mock chart component (placeholder)
  const MockChart = ({ title, type, data }) => (
    <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-6 h-64 flex items-center justify-center">
      <div className="text-center">
        <div className="text-6xl mb-2">📊</div>
        <h4 className="font-semibold text-gray-700 dark:text-gray-300">{title}</h4>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{type} Chart</p>
        <p className="text-xs text-gray-400 dark:text-gray-500 mt-2">Mock visualization with {data} data points</p>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border">
        <div className="flex flex-col md:flex-row gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Time Range
            </label>
            <select
              value={selectedTimeRange}
              onChange={(e) => setSelectedTimeRange(e.target.value)}
              className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
            >
              <option value="week">Last 7 days</option>
              <option value="month">Last 30 days</option>
              <option value="quarter">Last 90 days</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Primary Metric
            </label>
            <select
              value={selectedMetric}
              onChange={(e) => setSelectedMetric(e.target.value)}
              className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
            >
              <option value="overallScore">Safety Score</option>
              <option value="speedingEvents">Speeding Events</option>
              <option value="harshBraking">Harsh Braking</option>
              <option value="distraction">Distraction Events</option>
            </select>
          </div>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
              <span className="text-2xl">📈</span>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Avg Safety Score</p>
              <p className="text-2xl font-semibold text-gray-900 dark:text-white">{analytics.avgScore}</p>
              <p className="text-sm text-green-600 dark:text-green-400">+0.3 from last period</p>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border">
          <div className="flex items-center">
            <div className="p-2 bg-red-100 dark:bg-red-900 rounded-lg">
              <span className="text-2xl">⚠️</span>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Events</p>
              <p className="text-2xl font-semibold text-gray-900 dark:text-white">{analytics.totalEvents}</p>
              <p className="text-sm text-red-600 dark:text-red-400">-5% from last period</p>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
              <span className="text-2xl">🎯</span>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Improvement Rate</p>
              <p className="text-2xl font-semibold text-gray-900 dark:text-white">{analytics.improvement}</p>
              <p className="text-sm text-green-600 dark:text-green-400">Month over month</p>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border">
          <div className="flex items-center">
            <div className="p-2 bg-purple-100 dark:bg-purple-900 rounded-lg">
              <span className="text-2xl">⭐</span>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Top Performers</p>
              <p className="text-2xl font-semibold text-gray-900 dark:text-white">{analytics.riskDistribution.low}</p>
              <p className="text-sm text-purple-600 dark:text-purple-400">Score ≥ 8.5</p>
            </div>
          </div>
        </div>
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Safety Score Trends</h3>
          <MockChart title="Safety Score Over Time" type="Line" data={trendData.length} />
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Event Distribution</h3>
          <MockChart title="Event Types Breakdown" type="Pie" data="4 categories" />
        </div>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Driver Risk Heat Map</h3>
          <MockChart title="Risk Level Distribution" type="Heat Map" data="location-based" />
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Weekly Performance</h3>
          <MockChart title="Daily Safety Metrics" type="Bar" data="7 days" />
        </div>
      </div>

      {/* Detailed Analytics Table */}
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Detailed Analytics by Driver</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Driver
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Safety Score
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Score Trend
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Total Events
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Risk Category
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Improvement
                </th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              {driverData.map((driver, index) => {
                const totalEvents = driver.speedingEvents + driver.harshBraking + driver.rapidAcceleration + driver.distraction;
                const riskLevel = driver.overallScore < 7 ? 'High' : driver.overallScore < 8.5 ? 'Medium' : 'Low';
                const mockTrend = Math.random() > 0.5 ? 'up' : 'down';
                const mockImprovement = ((Math.random() - 0.5) * 20).toFixed(1);
                
                return (
                  <tr key={driver.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="flex-shrink-0 h-8 w-8">
                          <div className="h-8 w-8 rounded-full bg-gray-300 dark:bg-gray-600 flex items-center justify-center">
                            <span className="text-xs font-medium text-gray-700 dark:text-gray-300">
                              {driver.name.split(' ').map(n => n[0]).join('').toUpperCase()}
                            </span>
                          </div>
                        </div>
                        <div className="ml-3">
                          <div className="text-sm font-medium text-gray-900 dark:text-white">{driver.name}</div>
                          <div className="text-sm text-gray-500 dark:text-gray-400">{driver.employeeId}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-semibold text-gray-900 dark:text-white">{driver.overallScore}/10</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center text-sm ${
                        mockTrend === 'up' ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                      }`}>
                        {mockTrend === 'up' ? '📈' : '📉'} {mockTrend === 'up' ? 'Improving' : 'Declining'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                      {totalEvents}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        riskLevel === 'High' ? 'text-red-600 bg-red-100 dark:bg-red-900/20 dark:text-red-400' :
                        riskLevel === 'Medium' ? 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900/20 dark:text-yellow-400' :
                        'text-green-600 bg-green-100 dark:bg-green-900/20 dark:text-green-400'
                      }`}>
                        {riskLevel}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`text-sm font-medium ${
                        parseFloat(mockImprovement) > 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                      }`}>
                        {parseFloat(mockImprovement) > 0 ? '+' : ''}{mockImprovement}%
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Export Options */}
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Export Analytics</h3>
        <div className="flex flex-wrap gap-3">
          <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
            📊 Export Charts
          </button>
          <button className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition">
            📋 Export Report
          </button>
          <button className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition">
            📈 Export Raw Data
          </button>
          <button className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition">
            📧 Schedule Report
          </button>
        </div>
      </div>
    </div>
  );
};

export default DriverBehaviorAnalytics;