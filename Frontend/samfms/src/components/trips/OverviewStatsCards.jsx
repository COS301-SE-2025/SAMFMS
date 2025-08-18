import React from 'react';
import { MapPin, User } from 'lucide-react';

const OverviewStatsCards = ({ availableVehicles = 0, availableDrivers = 0 }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-fade-in animate-delay-100">
      {/* Available Vehicles Card */}
      <div className="group bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-950 dark:to-blue-900 border border-blue-200 dark:border-blue-800 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-blue-600 dark:text-blue-300 mb-2">
              Available Vehicles
            </p>
            <p className="text-3xl font-bold text-blue-900 dark:text-blue-100 transition-colors duration-300">
              {availableVehicles}
            </p>
            <div className="flex items-center mt-2">
              <div className="w-2 h-2 bg-blue-500 rounded-full mr-2 animate-pulse"></div>
              <p className="text-xs text-blue-600 dark:text-blue-400">Ready for trips</p>
            </div>
          </div>
          <div className="h-14 w-14 bg-blue-500 dark:bg-blue-600 rounded-xl flex items-center justify-center shadow-md group-hover:shadow-lg group-hover:scale-110 transition-all duration-300">
            <MapPin className="h-7 w-7 text-white" />
          </div>
        </div>
      </div>

      {/* Available Drivers Card */}
      <div className="group bg-gradient-to-br from-green-50 to-green-100 dark:from-green-950 dark:to-green-900 border border-green-200 dark:border-green-800 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-green-600 dark:text-green-300 mb-2">
              Available Drivers
            </p>
            <p className="text-3xl font-bold text-green-900 dark:text-green-100 transition-colors duration-300">
              {availableDrivers}
            </p>
            <div className="flex items-center mt-2">
              <div className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"></div>
              <p className="text-xs text-green-600 dark:text-green-400">Ready to drive</p>
            </div>
          </div>
          <div className="h-14 w-14 bg-green-500 dark:bg-green-600 rounded-xl flex items-center justify-center shadow-md group-hover:shadow-lg group-hover:scale-110 transition-all duration-300">
            <User className="h-7 w-7 text-white" />
          </div>
        </div>
      </div>
    </div>
  );
};

export default OverviewStatsCards;
