import React from 'react';

const DriverBehaviorDashboard = ({ driverData }) => {
  // Calculate summary statistics
  const totalDrivers = driverData.length;
  const averageScore = driverData.length > 0 
    ? (driverData.reduce((sum, driver) => sum + driver.overallScore, 0) / driverData.length).toFixed(1)
    : 0;
  const totalSpeedingEvents = driverData.reduce((sum, driver) => sum + driver.speedingEvents, 0);
  const totalHarshBraking = driverData.reduce((sum, driver) => sum + driver.harshBraking, 0);

  // Calculate risk levels
  const highRiskDrivers = driverData.filter(driver => driver.overallScore < 7).length;
  const mediumRiskDrivers = driverData.filter(driver => driver.overallScore >= 7 && driver.overallScore < 8.5).length;
  const lowRiskDrivers = driverData.filter(driver => driver.overallScore >= 8.5).length;

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
              <span className="text-2xl">👥</span>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Drivers</p>
              <p className="text-2xl font-semibold text-gray-900 dark:text-white">{totalDrivers}</p>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
              <span className="text-2xl">⭐</span>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Average Score</p>
              <p className="text-2xl font-semibold text-gray-900 dark:text-white">{averageScore}</p>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border">
          <div className="flex items-center">
            <div className="p-2 bg-red-100 dark:bg-red-900 rounded-lg">
              <span className="text-2xl">🚨</span>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Speeding Events</p>
              <p className="text-2xl font-semibold text-gray-900 dark:text-white">{totalSpeedingEvents}</p>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border">
          <div className="flex items-center">
            <div className="p-2 bg-orange-100 dark:bg-orange-900 rounded-lg">
              <span className="text-2xl">🛑</span>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Harsh Braking</p>
              <p className="text-2xl font-semibold text-gray-900 dark:text-white">{totalHarshBraking}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Risk Level Distribution */}
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Risk Level Distribution</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center p-4 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
            <div className="text-3xl font-bold text-red-600 dark:text-red-400">{highRiskDrivers}</div>
            <div className="text-sm text-red-600 dark:text-red-400">High Risk</div>
            <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">Score &lt; 7.0</div>
          </div>
          <div className="text-center p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg border border-yellow-200 dark:border-yellow-800">
            <div className="text-3xl font-bold text-yellow-600 dark:text-yellow-400">{mediumRiskDrivers}</div>
            <div className="text-sm text-yellow-600 dark:text-yellow-400">Medium Risk</div>
            <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">Score 7.0 - 8.4</div>
          </div>
          <div className="text-center p-4 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
            <div className="text-3xl font-bold text-green-600 dark:text-green-400">{lowRiskDrivers}</div>
            <div className="text-sm text-green-600 dark:text-green-400">Low Risk</div>
            <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">Score ≥ 8.5</div>
          </div>
        </div>
      </div>

      {/* Recent Alerts */}
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Recent Alerts</h3>
        <div className="space-y-3">
          <div className="flex items-center p-3 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
            <span className="text-red-500 text-xl mr-3">⚠️</span>
            <div className="flex-1">
              <p className="font-medium text-red-800 dark:text-red-200">Speeding Event</p>
              <p className="text-sm text-red-600 dark:text-red-400">Mike Wilson - Highway 101 - 15 mph over limit</p>
            </div>
            <span className="text-sm text-red-500">2 hours ago</span>
          </div>
          
          <div className="flex items-center p-3 bg-orange-50 dark:bg-orange-900/20 rounded-lg border border-orange-200 dark:border-orange-800">
            <span className="text-orange-500 text-xl mr-3">🛑</span>
            <div className="flex-1">
              <p className="font-medium text-orange-800 dark:text-orange-200">Harsh Braking</p>
              <p className="text-sm text-orange-600 dark:text-orange-400">John Smith - Main Street intersection</p>
            </div>
            <span className="text-sm text-orange-500">4 hours ago</span>
          </div>
          
          <div className="flex items-center p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg border border-yellow-200 dark:border-yellow-800">
            <span className="text-yellow-500 text-xl mr-3">📱</span>
            <div className="flex-1">
              <p className="font-medium text-yellow-800 dark:text-yellow-200">Distraction Event</p>
              <p className="text-sm text-yellow-600 dark:text-yellow-400">Mike Wilson - Phone usage detected</p>
            </div>
            <span className="text-sm text-yellow-500">6 hours ago</span>
          </div>
        </div>
      </div>

      {/* Top Performers */}
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Top Performers This Week</h3>
        <div className="space-y-3">
          {driverData
            .sort((a, b) => b.overallScore - a.overallScore)
            .slice(0, 3)
            .map((driver, index) => (
              <div key={driver.id} className="flex items-center p-3 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
                <div className="flex items-center justify-center w-8 h-8 bg-green-100 dark:bg-green-900 rounded-full mr-3">
                  <span className="text-green-600 dark:text-green-400 font-semibold">{index + 1}</span>
                </div>
                <div className="flex-1">
                  <p className="font-medium text-green-800 dark:text-green-200">{driver.name}</p>
                  <p className="text-sm text-green-600 dark:text-green-400">ID: {driver.employeeId}</p>
                </div>
                <div className="text-right">
                  <p className="font-semibold text-green-800 dark:text-green-200">{driver.overallScore}/10</p>
                  <p className="text-sm text-green-600 dark:text-green-400">Safety Score</p>
                </div>
              </div>
            ))}
        </div>
      </div>
    </div>
  );
};

export default DriverBehaviorDashboard;