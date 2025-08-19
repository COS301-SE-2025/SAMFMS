import React, { useState, useEffect } from 'react';
import { CheckCircle, AlertTriangle, Clock, Loader2 } from 'lucide-react';
import { getDriverPerformanceById } from '../../backend/api/analytics';
import { getCurrentUser } from '../../backend/api/auth';
import { getDriverSpecificAnalytics } from '../../backend/api/trips';
import { getDriverEMPID } from '../../backend/api/drivers';

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

        const driverId = await getDriverEMPID(currentUser.id);
        console.log("Driver id: ", driverId)

        // Fetch driver performance data
        const response = await getDriverSpecificAnalytics(driverId.data.data);
        console.log("Response for driver performace data: ", response);

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
        tripsCompleted: performanceData.completed_trips || 0,
        //totalDistance: performanceData.performance?.total_distance || 0,
        // fuelEfficiency: performanceData.performance?.fuel_efficiency || 0,
        // overallScore: performanceData.score?.overall_score || 0,
        // efficiencyScore: performanceData.score?.efficiency_score || 0,
        // activityScore: performanceData.score?.activity_score || 0,
        // consistencyScore: performanceData.score?.consistency_score || 0,
      }
    : {
        // Fallback static data
        tripsCompleted: 47,
        completedTrips: 44,
        totalTrips: 47,
      };

  // Calculate metrics based on available data
  let completionRate;
  let avgTripsPerDay;
  let overallScore;

  if (performanceData) {
    // Use API data - assuming we can derive these from existing data
    completionRate = Math.round((performanceData.completed_trips/performanceData.completed_trips+performanceData.cancelled_trips)*100)  || 
      Math.round((driverScore.consistencyScore || 85)); // Using consistency as proxy
    
    // Calculate average trips per day (assuming last 30 days)
    avgTripsPerDay = Math.round(( (performanceData.completed_trips+performanceData.cancelled_trips)/ 30) * 10) / 10;
    
    overallScore = Math.round(driverScore.overallScore);
  } else {
    // Use static calculation for fallback
    completionRate = driverScore.totalTrips > 0
      ? Math.round((driverScore.completedTrips / driverScore.totalTrips) * 100)
      : 0;
    
    // Assuming trips are spread over 30 days
    avgTripsPerDay = Math.round((driverScore.tripsCompleted / 30) * 10) / 10;
    
    overallScore = Math.max(0, Math.min(100, completionRate * 0.8 + 20));
  }

  return (
    <div className="bg-card rounded-lg shadow-sm border border-border p-4 sm:p-6">
      {/* <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-4 sm:mb-6">
        <h2 className="text-xl sm:text-2xl font-semibold text-foreground">Driver Performance</h2>
        <div className="mt-2 sm:mt-0 flex sm:block items-center">
          <div className="text-2xl sm:text-3xl font-bold text-primary">{overallScore}%</div>
          <div className="text-sm text-muted-foreground ml-2 sm:ml-0">Overall Score</div>
        </div>
      </div> */}

      {error && !performanceData && (
        <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
          <div className="text-sm text-yellow-800">
            <AlertTriangle className="h-4 w-4 inline mr-1" />
            Using demo data: {error}
          </div>
        </div>
      )}

      <div className="grid grid-cols-3 gap-3 sm:gap-4">
        {/* Total Trips */}
        <div className="bg-background rounded-lg p-2 sm:p-4 border border-border">
          <div className="flex items-center justify-between mb-1 sm:mb-2">
            <div className="p-1 sm:p-2 bg-green-100 rounded-lg">
              <CheckCircle className="h-4 w-4 sm:h-6 sm:w-6 text-green-600" />
            </div>
            <span className="text-base sm:text-2xl font-bold text-foreground">
              {driverScore.tripsCompleted}
            </span>
          </div>
          <div className="text-xs sm:text-sm font-medium text-foreground">Total Trips</div>
          <div className="text-2xs sm:text-xs text-muted-foreground">
            {performanceData ? 'All time' : 'This month'}
          </div>
        </div>

        {/* Completion Rate */}
        <div className="bg-background rounded-lg p-2 sm:p-4 border border-border">
          <div className="flex items-center justify-between mb-1 sm:mb-2">
            <div className="p-1 sm:p-2 bg-blue-100 rounded-lg">
              <Clock className="h-4 w-4 sm:h-6 sm:w-6 text-blue-600" />
            </div>
            <span className="text-base sm:text-2xl font-bold text-foreground">
              {completionRate}%
            </span>
          </div>
          <div className="text-xs sm:text-sm font-medium text-foreground">Completion Rate</div>
          <div className="text-2xs sm:text-xs text-muted-foreground">Success rate</div>
        </div>

        {/* Average Trips per Day */}
        <div className="bg-background rounded-lg p-2 sm:p-4 border border-border">
          <div className="flex items-center justify-between mb-1 sm:mb-2">
            <div className="p-1 sm:p-2 bg-orange-100 rounded-lg">
              <AlertTriangle className="h-4 w-4 sm:h-6 sm:w-6 text-orange-600" />
            </div>
            <div className="text-right">
              <span className="text-base sm:text-2xl font-bold text-foreground">
                {avgTripsPerDay}
              </span>
            </div>
          </div>
          <div className="text-xs sm:text-sm font-medium text-foreground">Avg. Trips/Day</div>
          <div className="text-2xs sm:text-xs text-muted-foreground">Daily average</div>
        </div>
      </div>
    </div>
  );
};

export default DriverScoreCard;
