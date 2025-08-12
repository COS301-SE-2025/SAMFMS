import React from 'react';
import DriverScoreCard from '../components/driver/DriverScoreCard';
import DriverNotifications from '../components/driver/DriverNotifications';
import UpcomingTrips from '../components/driver/UpcomingTrips';
import RecentTrips from '../components/driver/RecentTrips';

const DriverHomePage = () => {
  return (
    <div className="px-3 py-4 sm:p-6 space-y-4 sm:space-y-6 max-w-7xl mx-auto">
      {/* Page header for mobile - only visible on small screens */}
      <div className="sm:hidden">
        <h1 className="text-xl font-bold text-foreground">Driver Dashboard</h1>
        <p className="text-sm text-muted-foreground">Welcome back, Driver</p>
      </div>

      {/* Driver Score Card at the top */}
      <DriverScoreCard />

      {/* Bottom section with notifications on left and trips on right */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
        {/* Notifications - takes up full width on mobile, 1 column on desktop */}
        <div className="md:col-span-1 lg:col-span-1 order-2 md:order-1">
          <DriverNotifications />
        </div>

        {/* Trips section - takes up full width on mobile, 2 columns on desktop */}
        <div className="md:col-span-1 lg:col-span-2 space-y-4 sm:space-y-6 order-1 md:order-2">
          <UpcomingTrips />
          <RecentTrips />
        </div>
      </div>
    </div>
  );
};

export default DriverHomePage;
