import React, { useState, useCallback, useEffect } from 'react';
import DriverScoreCard from '../components/driver/DriverScoreCard';
import DriverNotifications from '../components/driver/DriverNotifications';
import UpcomingTrips from '../components/driver/UpcomingTrips';
import RecentTrips from '../components/driver/RecentTrips';
import ActiveTrip from '../components/driver/ActiveTrip';
import { getDriverActiveTrips } from '../backend/api/trips';
import { getCurrentUser } from '../backend/api/auth';
import { getDriverEMPID } from '../backend/api/drivers';

const DriverHomePage = () => {
  const [hasActiveTrip, setHasActiveTrip] = useState(false);
  const [checkingActiveTrip, setCheckingActiveTrip] = useState(true);

  // Get current user ID from authentication
  const getCurrentUserId = () => {
    const user = getCurrentUser();
    return user?.id || user?._id || user?.userId;
  };

  const getEmployeeID = async (security_id) => {
    try {
      const response = await getDriverEMPID(security_id);
      const employee_id = response.data;
      return employee_id;
    } catch (error) {
      console.error("Error fetching employee ID:", error);
      return null;
    }
  };

  // Check for active trips on component mount
  const checkForActiveTrips = useCallback(async () => {
    try {
      setCheckingActiveTrip(true);
      const driverId = getCurrentUserId();
      
      if (!driverId) {
        console.log('No driver ID found');
        return;
      }

      const employeeID = await getEmployeeID(driverId);
      if (!employeeID?.data) {
        console.log('No employee ID found');
        return;
      }

      console.log("Checking for active trips for EMP ID: ", employeeID.data);
      
      const response = await getDriverActiveTrips(employeeID.data);
      console.log("Active trip check response: ", response);
      
      if (response && response.length > 0) {
        console.log('Active trip found on load, showing ActiveTrip panel');
        setHasActiveTrip(true);
      } else {
        console.log('No active trips found');
        setHasActiveTrip(false);
      }
    } catch (error) {
      console.error('Error checking for active trips:', error);
      setHasActiveTrip(false);
    } finally {
      setCheckingActiveTrip(false);
    }
  }, []);

  // Check for active trips on component mount
  useEffect(() => {
    checkForActiveTrips();
  }, [checkForActiveTrips]);

  // Callback when a trip is started from UpcomingTrips
  const handleTripStarted = useCallback((tripId) => {
    console.log(`Trip ${tripId} started, showing ActiveTrip panel`);
    setHasActiveTrip(true);
  }, []);

  // Callback when a trip is ended from ActiveTrip
  const handleTripEnded = useCallback((tripId) => {
    console.log(`Trip ${tripId} ended, hiding ActiveTrip panel`);
    setHasActiveTrip(false);
  }, []);

  return (
    <div className="px-3 py-4 sm:p-6 space-y-4 sm:space-y-6 max-w-7xl mx-auto">
      {/* Driver Score Card at the top */}
      <DriverScoreCard />

      {/* Bottom section with notifications on left and trips on right */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
        {/* Notifications - takes up full width on mobile, 1 column on desktop */}
        <div className="md:col-span-1 lg:col-span-1 order-3 md:order-1">
          <DriverNotifications />
        </div>

        {/* Trips section - takes up full width on mobile, 2 columns on desktop */}
        <div className="md:col-span-1 lg:col-span-2 space-y-4 sm:space-y-6 order-1 md:order-2">
          {/* Active Trip Panel - Only show when there's an active trip */}
          {(hasActiveTrip && !checkingActiveTrip) && (
            <div className="order-1">
              <ActiveTrip onTripEnded={handleTripEnded} />
            </div>
          )}
          
          {/* Loading indicator while checking for active trips */}
          {checkingActiveTrip && (
            <div className="order-1 bg-card rounded-lg shadow-sm border border-border">
              <div className="py-3 px-3 sm:p-4 border-b border-border">
                <h3 className="text-base sm:text-lg font-semibold text-foreground">Active Trip</h3>
              </div>
              <div className="p-4 sm:p-6 text-center text-muted-foreground">
                <div className="animate-spin h-8 w-8 border-2 border-primary border-t-transparent rounded-full mx-auto mb-2"></div>
                <p className="text-sm">Checking for active trips...</p>
              </div>
            </div>
          )}
          
          {/* Upcoming Trips Panel */}
          <div className={hasActiveTrip || checkingActiveTrip ? "order-2" : "order-1"}>
            <UpcomingTrips onTripStarted={handleTripStarted} />
          </div>
          
          {/* Recent Trips Panel */}
          <div className={hasActiveTrip || checkingActiveTrip ? "order-3 mt-4 sm:mt-6" : "order-2 mt-4 sm:mt-6"}>
            <RecentTrips />
          </div>
        </div>
      </div>
    </div>
  );
};

export default DriverHomePage;