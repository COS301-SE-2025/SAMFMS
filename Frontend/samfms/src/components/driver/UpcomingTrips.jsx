import React, { useState, useEffect } from 'react';
import { MapPin, Clock, User, Car, ChevronRight, ChevronDown, ChevronUp, Play, Square } from 'lucide-react';
import { getUpcomingTrips, updateTrip, finishTrip } from '../../backend/api/trips';
import { getCurrentUser } from '../../backend/api/auth';
import { getDriverEMPID, TripFinishedStatus } from '../../backend/api/drivers';

const UpcomingTrips = ({ onTripStarted }) => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [upcomingTrips, setUpcomingTrips] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [startingTrips, setStartingTrips] = useState(new Set()); // Track which trips are being started
  const [endingTrips, setEndingTrips] = useState(new Set()); // Track which trips are being ended
  const [tripStatuses, setTripStatuses] = useState(new Map()); // Track trip finish status
  const [statusCheckIntervals, setStatusCheckIntervals] = useState(new Map()); // Track intervals for each trip

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

  // Function to check if trip is finished
  const checkTripFinished = async (employeeId, tripId) => {
    try {
      const isFinished = await TripFinishedStatus(employeeId);
      setTripStatuses(prev => new Map(prev.set(tripId, isFinished)));
      return isFinished;
    } catch (error) {
      console.error(`Error checking trip status for trip ${tripId}:`, error);
      return false;
    }
  };

  // Start monitoring a trip's finish status
  const startTripStatusMonitoring = (employeeId, tripId) => {
    // Don't start monitoring if already monitoring this trip
    if (statusCheckIntervals.has(tripId)) {
      return;
    }

    const interval = setInterval(async () => {
      await checkTripFinished(employeeId, tripId);
    }, 5000); // Check every 30 seconds

    setStatusCheckIntervals(prev => new Map(prev.set(tripId, interval)));
    
    // Also check immediately
    checkTripFinished(employeeId, tripId);
  };

  // Stop monitoring a trip's finish status
  const stopTripStatusMonitoring = (tripId) => {
    const interval = statusCheckIntervals.get(tripId);
    if (interval) {
      clearInterval(interval);
      setStatusCheckIntervals(prev => {
        const newMap = new Map(prev);
        newMap.delete(tripId);
        return newMap;
      });
    }
    setTripStatuses(prev => {
      const newMap = new Map(prev);
      newMap.delete(tripId);
      return newMap;
    });
  };

  const fetchUpcomingTrips = async () => {
    try {
      setLoading(true);
      const driverId = getCurrentUserId();
      
      if (!driverId) {
        throw new Error('No driver ID found');
      }

      // FIXED: Await the async function
      const employeeID = await getEmployeeID(driverId);
      console.log("EMP ID: ", employeeID);
      
      const response = await getUpcomingTrips(employeeID.data);
      console.log("Response for upcoming trips: ", response);
      
      // FIXED: Access the correct path in the response
      if (response?.data?.trips) {
        const trips = response.data.trips;
        setUpcomingTrips(trips);
        
        // Start monitoring in-progress trips
        trips.forEach(trip => {
          if (trip.status === 'in-progress') {
            startTripStatusMonitoring(employeeID.data, trip.id || trip._id);
          }
        });
      } else {
        setUpcomingTrips([]);  // Ensure it's always an array
      }
    } catch (err) {
      console.error('Error fetching upcoming trips:', err);
      setError(err.message);
      setUpcomingTrips([]);  // Ensure it's always an array even on error
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUpcomingTrips();

    // Cleanup intervals on unmount
    return () => {
      statusCheckIntervals.forEach(interval => clearInterval(interval));
    };
  }, [fetchUpcomingTrips, statusCheckIntervals]);

  const formatTripData = trip => {
    return {
      id: trip.id || trip._id,
      name: trip.name || 'Unnamed Trip',
      startLocation: trip.origin?.address || trip.origin?.name || 'Unknown Location',
      endLocation: trip.destination?.address || trip.destination?.name || 'Unknown Location',
      // FIXED: Use camelCase field names to match API response
      startTime: trip.scheduledStartTime
        ? new Date(trip.scheduledStartTime).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          })
        : 'Unknown Time',
      endTime: trip.scheduledEndTime
        ? new Date(trip.scheduledEndTime).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          })
        : null,
      date: trip.scheduledStartTime
        ? new Date(trip.scheduledStartTime).toISOString().split('T')[0]
        : new Date().toISOString().split('T')[0],
      vehicle: {
        model: trip.vehicle_model || 'Unknown Vehicle',
        registration: trip.vehicle_registration || 'Unknown',
      },
      status: trip.status || 'scheduled',
      distance: trip.estimatedDistance ? `${trip.estimatedDistance} km` : 'Unknown distance',
      estimatedDuration: trip.estimated_duration
        ? `${trip.estimated_duration}m`
        : 'Unknown duration',
      scheduledStartTime: trip.scheduledStartTime,
    };
  };

  const getStatusColor = status => {
    switch (status) {
      case 'scheduled':
        return 'bg-blue-100 text-blue-800';
      case 'in-progress':
        return 'bg-green-100 text-green-800';
      case 'delayed':
        return 'bg-yellow-100 text-yellow-800';
      case 'completed':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = dateString => {
    const date = new Date(dateString);
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(today.getDate() + 1);

    if (date.toDateString() === today.toDateString()) {
      return 'Today';
    } else if (date.toDateString() === tomorrow.toDateString()) {
      return 'Tomorrow';
    } else {
      return date.toLocaleDateString('en-US', {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
      });
    }
  };

  // Check if trip can be started (within 15 minutes of scheduled start time)
  const canStartTrip = (trip) => {
    if (trip.status !== 'scheduled') return false;
    
    const now = new Date();
    const scheduledStart = new Date(trip.scheduledStartTime);
    const timeDifference = scheduledStart.getTime() - now.getTime();
    const minutesDifference = timeDifference / (1000 * 60);
    
    // Allow starting if within 15 minutes before or after scheduled time
    return minutesDifference <= 15 && minutesDifference >= -15;
  };

  // Check if trip can be ended (trip is in progress and driver has reached destination)
  const canEndTrip = (tripId) => {
    return tripStatuses.get(tripId) === true;
  };

  // Handle starting a trip
  const handleStartTrip = async (tripId, event) => {
    event.stopPropagation(); // Prevent triggering the row click
    
    setStartingTrips(prev => new Set([...prev, tripId]));
    
    try {
      const now = new Date().toISOString();
      const data = {
        "actual_start_time": now,
      }
      console.log("Trip id: ", tripId);
      const response = await updateTrip(tripId, data);
      console.log("Response for updating: ", response);
      
      // Start monitoring this trip's finish status
      const driverId = getCurrentUserId();
      const employeeID = await getEmployeeID(driverId);
      if (employeeID?.data) {
        startTripStatusMonitoring(employeeID.data, tripId);
      }

      // Notify parent component that a trip has started
      if (onTripStarted) {
        onTripStarted(tripId);
      }

      // Refresh the upcoming trips list to remove the started trip
      await fetchUpcomingTrips();
      
      console.log(`Trip ${tripId} started successfully`);
      
    } catch (error) {
      console.error('Error starting trip:', error);
      // Handle error - show toast notification or error message
    } finally {
      setStartingTrips(prev => {
        const newSet = new Set(prev);
        newSet.delete(tripId);
        return newSet;
      });
    }
  };

  // Handle ending a trip
  const handleEndTrip = async (tripId, event) => {
    event.stopPropagation(); // Prevent triggering the row click
    
    setEndingTrips(prev => new Set([...prev, tripId]));
    
    try {
      const now = new Date().toISOString();
      const data = {
        "actual_end_time": now,
        "status": "completed"
      }
      console.log("Ending trip id: ", tripId);
      const response = await finishTrip(tripId, data);
      console.log("Response for finishing trip: ", response);
      
      // Stop monitoring this trip's finish status
      stopTripStatusMonitoring(tripId);

      // Refresh the upcoming trips list
      await fetchUpcomingTrips();
      
      console.log(`Trip ${tripId} ended successfully`);
      
    } catch (error) {
      console.error('Error ending trip:', error);
      // Handle error - show toast notification or error message
    } finally {
      setEndingTrips(prev => {
        const newSet = new Set(prev);
        newSet.delete(tripId);
        return newSet;
      });
    }
  };

  return (
    <div className="bg-card rounded-lg shadow-sm border border-border h-full">
      {/* Header */}
      <div className="py-3 px-3 sm:p-4 border-b border-border">
        <div className="flex items-center justify-between">
          <h3 className="text-base sm:text-lg font-semibold text-foreground">Upcoming Trips</h3>
          <div className="flex items-center space-x-2">
            <span className="text-xs sm:text-sm text-muted-foreground">
              {upcomingTrips.length} trips scheduled
            </span>
            <button
              onClick={() => setIsCollapsed(!isCollapsed)}
              className="p-1 hover:bg-accent rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary focus:ring-opacity-50"
              aria-label={isCollapsed ? 'Expand upcoming trips' : 'Collapse upcoming trips'}
            >
              {isCollapsed ? (
                <ChevronDown className="h-5 w-5" />
              ) : (
                <ChevronUp className="h-5 w-5" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Trips List - Collapsible */}
      {!isCollapsed && (
        <div className="divide-y divide-border max-h-[320px] sm:max-h-none overflow-y-auto overscroll-contain">
          {loading ? (
            <div className="p-4 sm:p-6 text-center text-muted-foreground">
              <div className="animate-spin h-8 w-8 border-2 border-primary border-t-transparent rounded-full mx-auto mb-2"></div>
              <p className="text-sm">Loading upcoming trips...</p>
            </div>
          ) : error ? (
            <div className="p-4 sm:p-6 text-center text-red-500">
              <p className="text-sm">Error loading trips: {error}</p>
            </div>
          ) : upcomingTrips.length === 0 ? (
            <div className="p-4 sm:p-6 text-center text-muted-foreground">
              <MapPin className="h-10 w-10 sm:h-12 sm:w-12 mx-auto mb-2 opacity-50" />
              <p className="text-sm">No upcoming trips</p>
            </div>
          ) : (
            upcomingTrips.map(trip => {
              const formattedTrip = formatTripData(trip);
              const canStart = canStartTrip(formattedTrip);
              const canEnd = canEndTrip(formattedTrip.id);
              const isStarting = startingTrips.has(formattedTrip.id);
              const isEnding = endingTrips.has(formattedTrip.id);
              
              return (
                <div
                  key={formattedTrip.id}
                  className="py-3 px-3 sm:p-4 hover:bg-accent/50 transition-colors cursor-pointer"
                >
                  <div className="flex flex-col sm:flex-row justify-between mb-3">
                    <div className="flex items-center space-x-1 sm:space-x-2 mb-1 sm:mb-0">
                      <span className="text-xs sm:text-sm font-medium text-foreground">
                        {formattedTrip.name}
                      </span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span
                        className={`px-1.5 sm:px-2 py-0.5 sm:py-1 rounded-full text-xs font-medium ${getStatusColor(
                          formattedTrip.status
                        )}`}
                      >
                        {formattedTrip.status}
                      </span>
                      <span className="text-xs sm:text-sm text-muted-foreground">
                        {formatDate(formattedTrip.date)}
                      </span>
                    </div>
                  </div>

                  {/* Route */}
                  <div className="flex flex-col sm:flex-row items-start sm:items-center space-y-2 sm:space-y-0 sm:space-x-2 mb-3">
                    <div className="flex items-center space-x-2 w-full sm:flex-1 truncate">
                      <div className="w-2 h-2 min-w-2 bg-green-500 rounded-full"></div>
                      <span className="text-sm text-foreground font-medium truncate">
                        {formattedTrip.startLocation}
                      </span>
                    </div>
                    <ChevronRight className="hidden sm:block h-4 w-4 text-muted-foreground" />
                    <div className="flex items-center space-x-2 w-full sm:flex-1 truncate">
                      <div className="w-2 h-2 min-w-2 bg-red-500 rounded-full"></div>
                      <span className="text-sm text-foreground font-medium truncate">
                        {formattedTrip.endLocation}
                      </span>
                    </div>
                  </div>

                  {/* Trip Details */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 sm:gap-4 text-sm mb-3">
                    <div className="flex items-center space-x-2">
                      <Clock className="h-4 w-4 min-w-4 text-muted-foreground" />
                      <span className="text-muted-foreground truncate">
                        {formattedTrip.startTime}
                        {formattedTrip.endTime && ` - ${formattedTrip.endTime}`}
                      </span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Car className="h-4 w-4 text-muted-foreground" />
                      <span className="text-muted-foreground">
                        {formattedTrip.vehicle.model} ({formattedTrip.vehicle.registration})
                      </span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <MapPin className="h-4 w-4 text-muted-foreground" />
                      <span className="text-muted-foreground">
                        {formattedTrip.distance} • {formattedTrip.estimatedDuration}
                      </span>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex justify-end">
                    {/* Start Trip Button */}
                    {canStart && formattedTrip.status === 'scheduled' && (
                      <button
                        onClick={(e) => handleStartTrip(formattedTrip.id, e)}
                        disabled={isStarting}
                        className="inline-flex items-center space-x-2 px-3 py-1.5 bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white text-sm font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-opacity-50"
                      >
                        {isStarting ? (
                          <>
                            <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                            <span>Starting...</span>
                          </>
                        ) : (
                          <>
                            <Play className="h-4 w-4" />
                            <span>Start Trip</span>
                          </>
                        )}
                      </button>
                    )}

                    {/* End Trip Button */}
                    {canEnd && formattedTrip.status === 'in-progress' && (
                      <button
                        onClick={(e) => handleEndTrip(formattedTrip.id, e)}
                        disabled={isEnding}
                        className="inline-flex items-center space-x-2 px-3 py-1.5 bg-red-600 hover:bg-red-700 disabled:bg-red-400 text-white text-sm font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-opacity-50"
                      >
                        {isEnding ? (
                          <>
                            <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                            <span>Ending...</span>
                          </>
                        ) : (
                          <>
                            <Square className="h-4 w-4" />
                            <span>End Trip</span>
                          </>
                        )}
                      </button>
                    )}

                    {/* Status indicators for in-progress trips */}
                    {formattedTrip.status === 'in-progress' && !canEnd && (
                      <span className="text-xs text-muted-foreground px-3 py-1.5">
                        Checking location...
                      </span>
                    )}

                    {/* Time until trip starts (for scheduled trips) */}
                    {formattedTrip.status === 'scheduled' && !canStart && (
                      <span className="text-xs text-muted-foreground px-3 py-1.5">
                        {(() => {
                          const now = new Date();
                          const scheduledStart = new Date(formattedTrip.scheduledStartTime);
                          const timeDifference = scheduledStart.getTime() - now.getTime();
                          const minutesDifference = Math.round(timeDifference / (1000 * 60));
                          
                          if (minutesDifference > 0) {
                            return `Starts in ${minutesDifference} minutes`;
                          } else {
                            return 'Trip time passed';
                          }
                        })()}
                      </span>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>
      )}

      {/* Footer */}
      {!isCollapsed && upcomingTrips.length > 0 && (
        <div className="p-3 border-t border-border">
          <button className="w-full text-sm text-primary hover:text-primary/80 font-medium transition-colors">
            View All Trips
          </button>
        </div>
      )}
    </div>
  );
};

export default UpcomingTrips;