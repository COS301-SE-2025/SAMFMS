import React, { useState, useEffect } from 'react';
import { MapPin, Clock, User, Car, Navigation, Square, Phone, MessageCircle } from 'lucide-react';
import { getDriverActiveTrips, updateTrip } from '../../backend/api/trips';
import { getCurrentUser } from '../../backend/api/auth';
import { getDriverEMPID, TripFinishedStatus } from '../../backend/api/drivers';

const ActiveTrip = ({ onTripEnded }) => {
  const [activeTrip, setActiveTrip] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [endingTrip, setEndingTrip] = useState(false);
  const [canEndTrip, setCanEndTrip] = useState(false);
  const [statusCheckInterval, setStatusCheckInterval] = useState(null);

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
  const checkTripFinished = async (employeeId) => {
    try {
      const isFinished = await TripFinishedStatus(employeeId);
      setCanEndTrip(isFinished);
      return isFinished;
    } catch (error) {
      console.error('Error checking trip status:', error);
      return false;
    }
  };

  // Start monitoring trip finish status
  const startStatusMonitoring = async (employeeId) => {
    // Don't start if already monitoring
    if (statusCheckInterval) {
      return;
    }

    const interval = setInterval(async () => {
      await checkTripFinished(employeeId);
    }, 30000); // Check every 30 seconds

    setStatusCheckInterval(interval);
    
    // Also check immediately
    await checkTripFinished(employeeId);
  };

  // Stop monitoring trip finish status
  const stopStatusMonitoring = () => {
    if (statusCheckInterval) {
      clearInterval(statusCheckInterval);
      setStatusCheckInterval(null);
    }
    setCanEndTrip(false);
  };

  // Fetch active trip
  const fetchActiveTrip = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const driverId = getCurrentUserId();
      if (!driverId) {
        throw new Error('No driver ID found');
      }

      const employeeID = await getEmployeeID(driverId);
      if (!employeeID?.data) {
        throw new Error('No employee ID found');
      }
      
      console.log("Fetching active trip for EMP ID: ", employeeID.data);
      
      const response = await getDriverActiveTrips(employeeID.data);
      console.log("Active trip response: ", response);
      
      if (response && response.length > 0) {
        const trip = response[0]; // Get the first active trip
        setActiveTrip(trip);
        
        // Start monitoring trip finish status
        await startStatusMonitoring(employeeID.data);
      } else {
        setActiveTrip(null);
        stopStatusMonitoring();
      }
    } catch (err) {
      console.error('Error fetching active trip:', err);
      setError(err.message);
      setActiveTrip(null);
      stopStatusMonitoring();
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchActiveTrip();

    // Cleanup interval on unmount
    return () => {
      if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
      }
    };
  }, []);

  const formatTripData = trip => {
    if (!trip) return null;
    
    return {
      id: trip.id || trip._id,
      name: trip.name || 'Active Trip',
      startLocation: trip.origin?.address || trip.origin?.name || 'Unknown Location',
      endLocation: trip.destination?.address || trip.destination?.name || 'Unknown Location',
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
      actualStartTime: trip.actual_start_time
        ? new Date(trip.actual_start_time).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          })
        : null,
      passenger: trip.passenger_name || 'Unknown Passenger',
      passengerPhone: trip.passenger_phone || null,
      vehicle: {
        model: trip.vehicle_model || 'Unknown Vehicle',
        registration: trip.vehicle_registration || 'Unknown',
      },
      status: trip.status || 'in-progress',
      distance: trip.estimatedDistance ? `${trip.estimatedDistance} km` : 'Unknown distance',
      estimatedDuration: trip.estimated_duration
        ? `${trip.estimated_duration}m`
        : 'Unknown duration',
    };
  };

  // Handle ending a trip
  const handleEndTrip = async () => {
    if (!activeTrip) return;
    
    setEndingTrip(true);
    
    try {
      const now = new Date().toISOString();
      const data = {
        "actual_end_time": now,
        "status": "completed"
      }
      
      const tripId = activeTrip.id || activeTrip._id;
      console.log("Ending trip id: ", tripId);
      
      const response = await updateTrip(tripId, data);
      console.log("Response for ending trip: ", response);
      
      // Stop monitoring
      stopStatusMonitoring();
      
      // Clear active trip
      setActiveTrip(null);
      
      // Notify parent component
      if (onTripEnded) {
        onTripEnded(tripId);
      }
      
      console.log(`Trip ${tripId} ended successfully`);
      
    } catch (error) {
      console.error('Error ending trip:', error);
      setError('Failed to end trip. Please try again.');
    } finally {
      setEndingTrip(false);
    }
  };

  // Calculate trip duration
  const calculateTripDuration = (startTime) => {
    if (!startTime) return 'Unknown duration';
    
    const start = new Date(startTime);
    const now = new Date();
    const diffMs = now - start;
    const diffMins = Math.floor(diffMs / (1000 * 60));
    
    if (diffMins < 60) {
      return `${diffMins} minutes`;
    } else {
      const hours = Math.floor(diffMins / 60);
      const minutes = diffMins % 60;
      return `${hours}h ${minutes}m`;
    }
  };

  if (loading) {
    return (
      <div className="bg-card rounded-lg shadow-sm border border-border h-full">
        <div className="py-3 px-3 sm:p-4 border-b border-border">
          <h3 className="text-base sm:text-lg font-semibold text-foreground">Active Trip</h3>
        </div>
        <div className="p-4 sm:p-6 text-center text-muted-foreground">
          <div className="animate-spin h-8 w-8 border-2 border-primary border-t-transparent rounded-full mx-auto mb-2"></div>
          <p className="text-sm">Loading active trip...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-card rounded-lg shadow-sm border border-border h-full">
        <div className="py-3 px-3 sm:p-4 border-b border-border">
          <h3 className="text-base sm:text-lg font-semibold text-foreground">Active Trip</h3>
        </div>
        <div className="p-4 sm:p-6 text-center text-red-500">
          <p className="text-sm">Error: {error}</p>
          <button 
            onClick={fetchActiveTrip}
            className="mt-2 px-3 py-1 bg-primary text-primary-foreground rounded text-sm hover:bg-primary/90"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!activeTrip) {
    return (
      <div className="bg-card rounded-lg shadow-sm border border-border h-full">
        <div className="py-3 px-3 sm:p-4 border-b border-border">
          <h3 className="text-base sm:text-lg font-semibold text-foreground">Active Trip</h3>
        </div>
        <div className="p-4 sm:p-6 text-center text-muted-foreground">
          <Navigation className="h-10 w-10 sm:h-12 sm:w-12 mx-auto mb-2 opacity-50" />
          <p className="text-sm">No active trip</p>
          <p className="text-xs mt-1">Start a trip from your upcoming trips</p>
        </div>
      </div>
    );
  }

  const formattedTrip = formatTripData(activeTrip);

  return (
    <div className="bg-card rounded-lg shadow-sm border border-border h-full">
      {/* Header */}
      <div className="py-3 px-3 sm:p-4 border-b border-border">
        <div className="flex items-center justify-between">
          <h3 className="text-base sm:text-lg font-semibold text-foreground">Active Trip</h3>
          <div className="flex items-center space-x-2">
            <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs font-medium">
              In Progress
            </span>
          </div>
        </div>
      </div>

      {/* Trip Content */}
      <div className="p-3 sm:p-4">
        {/* Trip Name and Duration */}
        <div className="mb-4">
          <h4 className="text-lg font-semibold text-foreground mb-1">{formattedTrip.name}</h4>
          <div className="flex items-center space-x-4 text-sm text-muted-foreground">
            <span>Started: {formattedTrip.actualStartTime || formattedTrip.startTime}</span>
            <span>Duration: {calculateTripDuration(activeTrip.actual_start_time)}</span>
          </div>
        </div>

        {/* Route */}
        <div className="mb-4">
          <div className="flex items-center space-x-3 mb-2">
            <div className="flex flex-col items-center">
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
              <div className="w-0.5 h-6 bg-gray-300"></div>
              <div className="w-3 h-3 bg-red-500 rounded-full"></div>
            </div>
            <div className="flex-1">
              <div className="mb-3">
                <p className="text-sm font-medium text-foreground">{formattedTrip.startLocation}</p>
                <p className="text-xs text-muted-foreground">Origin</p>
              </div>
              <div>
                <p className="text-sm font-medium text-foreground">{formattedTrip.endLocation}</p>
                <p className="text-xs text-muted-foreground">Destination</p>
              </div>
            </div>
          </div>
        </div>

        {/* Trip Details Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
          <div className="flex items-center space-x-2">
            <User className="h-4 w-4 text-muted-foreground" />
            <div>
              <p className="text-sm font-medium text-foreground">{formattedTrip.passenger}</p>
              <p className="text-xs text-muted-foreground">Passenger</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <Car className="h-4 w-4 text-muted-foreground" />
            <div>
              <p className="text-sm font-medium text-foreground">{formattedTrip.vehicle.model}</p>
              <p className="text-xs text-muted-foreground">{formattedTrip.vehicle.registration}</p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <Clock className="h-4 w-4 text-muted-foreground" />
            <div>
              <p className="text-sm font-medium text-foreground">
                {formattedTrip.startTime} - {formattedTrip.endTime}
              </p>
              <p className="text-xs text-muted-foreground">Scheduled time</p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <MapPin className="h-4 w-4 text-muted-foreground" />
            <div>
              <p className="text-sm font-medium text-foreground">
                {formattedTrip.distance} • {formattedTrip.estimatedDuration}
              </p>
              <p className="text-xs text-muted-foreground">Distance & Duration</p>
            </div>
          </div>
        </div>

        {/* Contact Actions */}
        {formattedTrip.passengerPhone && (
          <div className="flex space-x-2 mb-4">
            <a
              href={`tel:${formattedTrip.passengerPhone}`}
              className="flex items-center space-x-2 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors flex-1 justify-center"
            >
              <Phone className="h-4 w-4" />
              <span>Call</span>
            </a>
            <a
              href={`sms:${formattedTrip.passengerPhone}`}
              className="flex items-center space-x-2 px-3 py-2 bg-green-600 hover:bg-green-700 text-white text-sm font-medium rounded-lg transition-colors flex-1 justify-center"
            >
              <MessageCircle className="h-4 w-4" />
              <span>SMS</span>
            </a>
          </div>
        )}

        {/* End Trip Button */}
        <div className="flex justify-center">
          {canEndTrip ? (
            <button
              onClick={handleEndTrip}
              disabled={endingTrip}
              className="inline-flex items-center space-x-2 px-6 py-2 bg-red-600 hover:bg-red-700 disabled:bg-red-400 text-white font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-opacity-50 w-full justify-center"
            >
              {endingTrip ? (
                <>
                  <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                  <span>Ending Trip...</span>
                </>
              ) : (
                <>
                  <Square className="h-4 w-4" />
                  <span>End Trip</span>
                </>
              )}
            </button>
          ) : (
            <div className="w-full text-center py-2 px-4 bg-gray-100 text-gray-600 rounded-lg">
              <p className="text-sm">Checking location...</p>
              <p className="text-xs text-muted-foreground mt-1">
                You can end the trip when you reach the destination
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ActiveTrip;