import React, { useState, useEffect } from 'react';
import { MapPin, Clock, User, Car, ChevronRight, ChevronDown, ChevronUp } from 'lucide-react';
import { getUpcomingTrips } from '../../backend/api/trips';
import { getCurrentUser } from '../../backend/api/auth';

const UpcomingTrips = () => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [upcomingTrips, setUpcomingTrips] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Get current user ID from authentication
  const getCurrentUserId = () => {
    const user = getCurrentUser();
    return user?.id || user?._id || user?.userId || 'driver123'; // Fallback to default if no user
  };

  useEffect(() => {
    const fetchUpcomingTrips = async () => {
      try {
        setLoading(true);
        const driverId = getCurrentUserId();
        console.log('Fetching upcoming trips for driver ID:', driverId);
        const response = await getUpcomingTrips(driverId, 10);

        if (response?.data?.trips) {
          setUpcomingTrips(response.data.trips);
        }
      } catch (err) {
        console.error('Error fetching upcoming trips:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchUpcomingTrips();
  }, []);

  const formatTripData = trip => {
    return {
      id: trip.id || trip._id,
      name: trip.name || 'Unnamed Trip',
      startLocation: trip.origin?.address || trip.origin?.name || 'Unknown Location',
      endLocation: trip.destination?.address || trip.destination?.name || 'Unknown Location',
      startTime: trip.scheduled_start_time
        ? new Date(trip.scheduled_start_time).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          })
        : 'Unknown Time',
      endTime: trip.scheduled_end_time
        ? new Date(trip.scheduled_end_time).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          })
        : null,
      date: trip.scheduled_start_time
        ? new Date(trip.scheduled_start_time).toISOString().split('T')[0]
        : new Date().toISOString().split('T')[0],
      passenger: trip.passenger_name || 'Unknown Passenger',
      vehicle: {
        model: trip.vehicle_model || 'Unknown Vehicle',
        registration: trip.vehicle_registration || 'Unknown',
      },
      status: trip.status || 'scheduled',
      distance: trip.estimated_distance ? `${trip.estimated_distance} km` : 'Unknown distance',
      estimatedDuration: trip.estimated_duration
        ? `${trip.estimated_duration}m`
        : 'Unknown duration',
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
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 sm:gap-4 text-sm">
                    <div className="flex items-center space-x-2">
                      <Clock className="h-4 w-4 min-w-4 text-muted-foreground" />
                      <span className="text-muted-foreground truncate">
                        {formattedTrip.startTime}
                        {formattedTrip.endTime && ` - ${formattedTrip.endTime}`}
                      </span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <User className="h-4 w-4 min-w-4 text-muted-foreground" />
                      <span className="text-muted-foreground truncate">
                        {formattedTrip.passenger}
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
