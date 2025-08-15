import React from 'react';
import { Clock, MapPin, User } from 'lucide-react';

const RecentTripsStats = ({ recentTrips = [] }) => {
  const totalDistance = recentTrips.reduce(
    (total, trip) => total + parseFloat(trip.distance || 0),
    0
  );
  const uniqueDrivers = new Set(recentTrips.map(trip => trip.driver)).size;

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 animate-fade-in animate-delay-100">
      <div className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-950 dark:to-green-900 border border-green-200 dark:border-green-800 rounded-xl shadow-lg p-4">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 bg-green-500 rounded-lg flex items-center justify-center">
            <Clock className="h-5 w-5 text-white" />
          </div>
          <div>
            <p className="text-sm font-medium text-green-600 dark:text-green-300">Completed</p>
            <p className="text-2xl font-bold text-green-900 dark:text-green-100">
              {recentTrips.length}
            </p>
          </div>
        </div>
      </div>
      <div className="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-950 dark:to-purple-900 border border-purple-200 dark:border-purple-800 rounded-xl shadow-lg p-4">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 bg-purple-500 rounded-lg flex items-center justify-center">
            <MapPin className="h-5 w-5 text-white" />
          </div>
          <div>
            <p className="text-sm font-medium text-purple-600 dark:text-purple-300">
              Total Distance
            </p>
            <p className="text-2xl font-bold text-purple-900 dark:text-purple-100">
              {totalDistance.toFixed(1)}mi
            </p>
          </div>
        </div>
      </div>
      <div className="bg-gradient-to-br from-indigo-50 to-indigo-100 dark:from-indigo-950 dark:to-indigo-900 border border-indigo-200 dark:border-indigo-800 rounded-xl shadow-lg p-4">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 bg-indigo-500 rounded-lg flex items-center justify-center">
            <User className="h-5 w-5 text-white" />
          </div>
          <div>
            <p className="text-sm font-medium text-indigo-600 dark:text-indigo-300">
              Active Drivers
            </p>
            <p className="text-2xl font-bold text-indigo-900 dark:text-indigo-100">
              {uniqueDrivers}
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
            <p className="text-2xl font-bold text-teal-900 dark:text-teal-100">2h 3m</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RecentTripsStats;
