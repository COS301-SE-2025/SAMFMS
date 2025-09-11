import React from 'react';
import { Clock, MapPin, TrendingUp, Activity, ChartColumnBig, ChartNoAxesColumnIncreasing} from 'lucide-react';

const RecentTripsStats = ({ recentTrips = [], tripHistoryStats = null, loading = false }) => {
  // Debug logging
  console.log('RecentTripsStats received props:', { recentTrips, tripHistoryStats, loading });

  // Use trip history stats if available, otherwise fall back to calculating from recent trips
  const stats = {
    totalTrips: tripHistoryStats?.total_trips || recentTrips.length,
    totalDistance:
      tripHistoryStats?.total_distance_km ||
      recentTrips.reduce((total, trip) => total + parseFloat(trip.distance || 0), 0),
    averageDuration: tripHistoryStats?.average_duration_hours || 0,
    averageDistance: tripHistoryStats?.average_distance_km || 0,
  };

  console.log('Calculated stats:', stats);

  // Format duration from hours to readable format
  const formatDuration = hours => {
    if (!hours || hours === 0) return '0m';
    const h = Math.floor(hours);
    const m = Math.round((hours - h) * 60);
    if (h > 0) {
      return m > 0 ? `${h}h ${m}m` : `${h}h`;
    }
    return `${m}m`;
  };

  // Format distance with appropriate unit
  const formatDistance = km => {
    if (!km || km === 0) return '0 km';
    return km >= 1000 ? `${(km / 1000).toFixed(1)}k km` : `${km.toFixed(1)} km`;
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 animate-fade-in animate-delay-100">
      <div className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-950 dark:to-green-900 border border-green-200 dark:border-green-800 rounded-xl shadow-lg p-4">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 bg-green-500 rounded-lg flex items-center justify-center">
            <ChartColumnBig />
          </div>
          <div>
            <p className="text-sm font-medium text-green-600 dark:text-green-300">
              Total Completed
            </p>
            <p className="text-2xl font-bold text-green-900 dark:text-green-100">
              {loading ? '...' : stats.totalTrips.toLocaleString()}
            </p>
          </div>
        </div>
      </div>

      <div className="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-950 dark:to-purple-900 border border-purple-200 dark:border-purple-800 rounded-xl shadow-lg p-4">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 bg-purple-500 rounded-lg flex items-center justify-center">
            <ChartNoAxesColumnIncreasing />
          </div>
          <div>
            <p className="text-sm font-medium text-purple-600 dark:text-purple-300">
              Total Distance
            </p>
            <p className="text-2xl font-bold text-purple-900 dark:text-purple-100">
              {loading ? '...' : formatDistance(stats.totalDistance)}
            </p>
          </div>
        </div>
      </div>

      <div className="bg-gradient-to-br from-indigo-50 to-indigo-100 dark:from-indigo-950 dark:to-indigo-900 border border-indigo-200 dark:border-indigo-800 rounded-xl shadow-lg p-4">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 bg-indigo-500 rounded-lg flex items-center justify-center">
            <TrendingUp className="h-5 w-5 text-white" />
          </div>
          <div>
            <p className="text-sm font-medium text-indigo-600 dark:text-indigo-300">Avg Distance</p>
            <p className="text-2xl font-bold text-indigo-900 dark:text-indigo-100">
              {loading ? '...' : formatDistance(stats.averageDistance)}
            </p>
          </div>
        </div>
      </div>

      <div className="bg-gradient-to-br from-teal-50 to-teal-100 dark:from-teal-950 dark:to-teal-900 border border-teal-200 dark:border-teal-800 rounded-xl shadow-lg p-4">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 bg-teal-500 rounded-lg flex items-center justify-center">
            <Clock className="h-5 w-5 text-white" />
          </div>
          <div>
            <p className="text-sm font-medium text-teal-600 dark:text-teal-300">Avg Duration</p>
            <p className="text-2xl font-bold text-teal-900 dark:text-teal-100">
              {loading ? '...' : formatDuration(stats.averageDuration)}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RecentTripsStats;
