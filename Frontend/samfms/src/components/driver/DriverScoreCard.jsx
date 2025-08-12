import React from 'react';
import { CheckCircle, AlertTriangle, Clock } from 'lucide-react';

const DriverScoreCard = () => {
  // Static data for now
  const driverScore = {
    tripsCompleted: 47,
    violations: 3,
    onTimeTrips: 42,
  };

  // Calculate on-time percentage
  const onTimePercentage =
    driverScore.tripsCompleted > 0
      ? Math.round((driverScore.onTimeTrips / driverScore.tripsCompleted) * 100)
      : 0;

  // Calculate overall score (simple scoring system)
  const overallScore = Math.max(
    0,
    Math.min(
      100,
      onTimePercentage * 0.7 + // 70% weight for on-time performance
        Math.max(0, 50 - driverScore.violations * 5) * 0.3 // 30% weight for violations (penalty)
    )
  );

  return (
    <div className="bg-card rounded-lg shadow-sm border border-border p-4 sm:p-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-4 sm:mb-6">
        <h2 className="text-xl sm:text-2xl font-semibold text-foreground">Driver Performance</h2>
        <div className="mt-2 sm:mt-0 flex sm:block items-center">
          <div className="text-2xl sm:text-3xl font-bold text-primary">{Math.round(overallScore)}%</div>
          <div className="text-sm text-muted-foreground ml-2 sm:ml-0">Overall Score</div>
        </div>
      </div>

      <div className="grid grid-cols-1 xs:grid-cols-2 sm:grid-cols-3 gap-3 sm:gap-4">
        {/* Trips Completed */}
        <div className="bg-background rounded-lg p-4 border border-border">
          <div className="flex items-center justify-between mb-2">
            <div className="p-2 bg-green-100 rounded-lg">
              <CheckCircle className="h-6 w-6 text-green-600" />
            </div>
            <span className="text-2xl font-bold text-foreground">{driverScore.tripsCompleted}</span>
          </div>
          <div className="text-sm font-medium text-foreground">Trips Completed</div>
          <div className="text-xs text-muted-foreground">This month</div>
        </div>

        {/* Violations */}
        <div className="bg-background rounded-lg p-4 border border-border">
          <div className="flex items-center justify-between mb-2">
            <div className="p-2 bg-red-100 rounded-lg">
              <AlertTriangle className="h-6 w-6 text-red-600" />
            </div>
            <span className="text-2xl font-bold text-foreground">{driverScore.violations}</span>
          </div>
          <div className="text-sm font-medium text-foreground">Violations</div>
          <div className="text-xs text-muted-foreground">This month</div>
        </div>

        {/* On-Time Trips */}
        <div className="bg-background rounded-lg p-4 border border-border">
          <div className="flex items-center justify-between mb-2">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Clock className="h-6 w-6 text-blue-600" />
            </div>
            <div className="text-right">
              <span className="text-2xl font-bold text-foreground">{driverScore.onTimeTrips}</span>
              <div className="text-xs text-muted-foreground">({onTimePercentage}%)</div>
            </div>
          </div>
          <div className="text-sm font-medium text-foreground">On-Time Trips</div>
          <div className="text-xs text-muted-foreground">This month</div>
        </div>
      </div>

      {/* Performance Insights */}
      <div className="mt-3 sm:mt-4 p-3 sm:p-4 bg-background rounded-lg border border-border">
        <div className="text-sm font-medium text-foreground mb-2">Performance Insights</div>
        <div className="text-xs sm:text-sm text-muted-foreground">
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
          {driverScore.violations > 5 && (
            <span className="block sm:inline mt-2 sm:mt-0 sm:ml-2 text-red-600">
              ⚠️ Work on reducing violations for better performance.
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

export default DriverScoreCard;
