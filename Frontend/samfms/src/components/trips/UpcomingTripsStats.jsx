import React from 'react';
import { Calendar, Clock, User } from 'lucide-react';

const UpcomingTripsStats = ({ upcomingTrips = [] }) => {
  const highPriorityCount = upcomingTrips.filter(trip => trip.priority === 'High').length;
  const pendingApprovalCount = upcomingTrips.filter(
    trip => trip.status === 'Pending Approval'
  ).length;

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 animate-fade-in animate-delay-100">
      <div className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-950 dark:to-blue-900 border border-blue-200 dark:border-blue-800 rounded-xl shadow-lg p-4">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 bg-blue-500 rounded-lg flex items-center justify-center">
            <Calendar className="h-5 w-5 text-white" />
          </div>
          <div>
            <p className="text-sm font-medium text-blue-600 dark:text-blue-300">Total Scheduled</p>
            <p className="text-2xl font-bold text-blue-900 dark:text-blue-100">
              {upcomingTrips.length}
            </p>
          </div>
        </div>
      </div>
      <div className="bg-gradient-to-br from-red-50 to-red-100 dark:from-red-950 dark:to-red-900 border border-red-200 dark:border-red-800 rounded-xl shadow-lg p-4">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 bg-red-500 rounded-lg flex items-center justify-center">
            <Clock className="h-5 w-5 text-white" />
          </div>
          <div>
            <p className="text-sm font-medium text-red-600 dark:text-red-300">High Priority</p>
            <p className="text-2xl font-bold text-red-900 dark:text-red-100">{highPriorityCount}</p>
          </div>
        </div>
      </div>
      <div className="bg-gradient-to-br from-orange-50 to-orange-100 dark:from-orange-950 dark:to-orange-900 border border-orange-200 dark:border-orange-800 rounded-xl shadow-lg p-4">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 bg-orange-500 rounded-lg flex items-center justify-center">
            <User className="h-5 w-5 text-white" />
          </div>
          <div>
            <p className="text-sm font-medium text-orange-600 dark:text-orange-300">
              Pending Approval
            </p>
            <p className="text-2xl font-bold text-orange-900 dark:text-orange-100">
              {pendingApprovalCount}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UpcomingTripsStats;
