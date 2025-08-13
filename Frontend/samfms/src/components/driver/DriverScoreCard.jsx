import React, { useState, useEffect } from 'react';
import { CheckCircle, AlertTriangle, Clock, Loader2 } from 'lucide-react';
import { getDriverPerformanceById } from '../../backend/api/analytics';
import { getCurrentUser } from '../../backend/api/auth';

const DriverScoreCard = () => {
  const [performanceData, setPerformanceData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchDriverPerformance = async () => {
      try {
        setLoading(true);
        setError(null);

        // Get current user
        const currentUser = getCurrentUser();
        if (!currentUser || !currentUser.id) {
          throw new Error('No authenticated user found');
        }

        // Use user ID as driver ID (this might need adjustment based on your data structure)
        const driverId = currentUser.id;

        // Fetch driver performance data
        const response = await getDriverPerformanceById(driverId);

        // Handle both direct data and wrapped response formats
        const data = response.data || response;
        setPerformanceData(data);
      } catch (err) {
        console.error('Error fetching driver performance:', err);
        setError(err.message);
        // Fallback to static data if API fails
        setPerformanceData(null);
      } finally {
        setLoading(false);
      }
    };

    fetchDriverPerformance();
  }, []);

  // Loading state
  if (loading) {
    return (
      <div className="bg-card rounded-lg shadow-sm border border-border p-4 sm:p-6">
        <div className="flex items-center justify-center h-32">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <span className="ml-2 text-muted-foreground">Loading performance data...</span>
        </div>
      </div>
    );
  }

  // Use API data if available, otherwise fallback to static data
  const driverScore = performanceData
    ? {
        tripsCompleted: performanceData.performance?.trip_count || 0,
        totalDistance: performanceData.performance?.total_distance || 0,
        fuelEfficiency: performanceData.performance?.fuel_efficiency || 0,
        overallScore: performanceData.score?.overall_score || 0,
        efficiencyScore: performanceData.score?.efficiency_score || 0,
        activityScore: performanceData.score?.activity_score || 0,
        consistencyScore: performanceData.score?.consistency_score || 0,
      }
    : {
        // Fallback static data
        tripsCompleted: 47,
        violations: 3,
        onTimeTrips: 42,
      };

  // Calculate metrics based on available data
  let onTimePercentage;
  let overallScore;
  let violations = 0; // Default for now, can be added to backend later

  if (performanceData) {
    // Use API data
    overallScore = Math.round(driverScore.overallScore);
    onTimePercentage = Math.round(driverScore.consistencyScore); // Using consistency as proxy for on-time
  } else {
    // Use static calculation for fallback
    onTimePercentage =
      driverScore.tripsCompleted > 0
        ? Math.round((driverScore.onTimeTrips / driverScore.tripsCompleted) * 100)
        : 0;
    overallScore = Math.max(
      0,
      Math.min(100, onTimePercentage * 0.7 + Math.max(0, 50 - violations * 5) * 0.3)
    );
  }

  return (
    <div className="bg-card rounded-lg shadow-sm border border-border p-4 sm:p-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-4 sm:mb-6">
        <h2 className="text-xl sm:text-2xl font-semibold text-foreground">Driver Performance</h2>
        <div className="mt-2 sm:mt-0 flex sm:block items-center">
          <div className="text-2xl sm:text-3xl font-bold text-primary">{overallScore}%</div>
          <div className="text-sm text-muted-foreground ml-2 sm:ml-0">Overall Score</div>
        </div>
      </div>

      {error && !performanceData && (
        <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
          <div className="text-sm text-yellow-800">
            <AlertTriangle className="h-4 w-4 inline mr-1" />
            Using demo data: {error}
          </div>
        </div>
      )}

      <div className="grid grid-cols-3 gap-3 sm:gap-4">
        {/* Trips Completed */}
        <div className="bg-background rounded-lg p-2 sm:p-4 border border-border">
          <div className="flex items-center justify-between mb-1 sm:mb-2">
            <div className="p-1 sm:p-2 bg-green-100 rounded-lg">
              <CheckCircle className="h-4 w-4 sm:h-6 sm:w-6 text-green-600" />
            </div>
            <span className="text-base sm:text-2xl font-bold text-foreground">
              {driverScore.tripsCompleted}
            </span>
          </div>
          <div className="text-xs sm:text-sm font-medium text-foreground">Trips Completed</div>
          <div className="text-2xs sm:text-xs text-muted-foreground">
            {performanceData ? 'Total' : 'This month'}
          </div>
        </div>

        {/* Efficiency/Violations */}
        <div className="bg-background rounded-lg p-2 sm:p-4 border border-border">
          <div className="flex items-center justify-between mb-1 sm:mb-2">
            <div className="p-1 sm:p-2 bg-red-100 rounded-lg">
              <AlertTriangle className="h-4 w-4 sm:h-6 sm:w-6 text-red-600" />
            </div>
            <span className="text-base sm:text-2xl font-bold text-foreground">
              {performanceData ? `${Math.round(driverScore.fuelEfficiency)} L/km` : violations}
            </span>
          </div>
          <div className="text-xs sm:text-sm font-medium text-foreground">
            {performanceData ? 'Fuel Efficiency' : 'Violations'}
          </div>
          <div className="text-2xs sm:text-xs text-muted-foreground">
            {performanceData ? 'Average' : 'This month'}
          </div>
        </div>

        {/* Performance Score/On-Time Trips */}
        <div className="bg-background rounded-lg p-2 sm:p-4 border border-border">
          <div className="flex items-center justify-between mb-1 sm:mb-2">
            <div className="p-1 sm:p-2 bg-blue-100 rounded-lg">
              <Clock className="h-4 w-4 sm:h-6 sm:w-6 text-blue-600" />
            </div>
            <div className="text-right">
              <span className="text-base sm:text-2xl font-bold text-foreground">
                {performanceData
                  ? `${Math.round(driverScore.efficiencyScore)}%`
                  : `${onTimePercentage}%`}
              </span>
            </div>
          </div>
          <div className="text-xs sm:text-sm font-medium text-foreground">
            {performanceData ? 'Efficiency Score' : 'On-Time Rate'}
          </div>
          <div className="text-2xs sm:text-xs text-muted-foreground">
            {performanceData ? 'Performance' : 'This month'}
          </div>
        </div>
      </div>

      {/* Performance Insights */}
      <div className="mt-3 sm:mt-4 p-3 sm:p-4 bg-background rounded-lg border border-border">
        <div className="text-sm font-medium text-foreground mb-2">Performance Insights</div>
        <div className="text-xs sm:text-sm text-muted-foreground">
          {performanceData ? (
            // API-based insights
            <>
              {overallScore >= 80 && (
                <span className="text-green-600 block sm:inline">
                  🎉 Excellent overall performance! You're doing great.
                </span>
              )}
              {overallScore >= 60 && overallScore < 80 && (
                <span className="text-yellow-600 block sm:inline">
                  ⚡ Good performance! Keep working to reach excellent levels.
                </span>
              )}
              {overallScore < 60 && (
                <span className="text-red-600 block sm:inline">
                  📈 Focus on improving your driving metrics to boost your score.
                </span>
              )}
              {driverScore.fuelEfficiency > 0 && (
                <span className="block sm:inline mt-2 sm:mt-0 sm:ml-2 text-blue-600">
                  ⛽ Fuel efficiency: {Math.round(driverScore.fuelEfficiency * 100) / 100} L/km
                </span>
              )}
            </>
          ) : (
            // Fallback static insights
            <>
              {onTimePercentage >= 90 && (
                <span className="text-green-600 block sm:inline">
                  🎉 Excellent on-time performance! Keep up the great work.
                </span>
              )}
              {onTimePercentage >= 75 && onTimePercentage < 90 && (
                <span className="text-yellow-600 block sm:inline">
                  ⚡ Good performance! Try to improve punctuality for better scores.
                </span>
              )}
              {onTimePercentage < 75 && (
                <span className="text-red-600 block sm:inline">
                  📈 Focus on improving on-time delivery to boost your score.
                </span>
              )}
              {violations > 5 && (
                <span className="block sm:inline mt-2 sm:mt-0 sm:ml-2 text-red-600">
                  ⚠️ Work on reducing violations for better performance.
                </span>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default DriverScoreCard;
