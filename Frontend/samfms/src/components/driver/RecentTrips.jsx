import React, { useState, useEffect } from 'react';
import {
  MapPin,
  Clock,
  User,
  Car,
  CheckCircle,
  AlertTriangle,
  ChevronRight,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { getRecentTrips } from '../../backend/api/trips';
import { getCurrentUser } from '../../backend/api/auth';

const RecentTrips = () => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [recentTrips, setRecentTrips] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Get current user ID from authentication
  const getCurrentUserId = () => {
    const user = getCurrentUser();
    return user?.id || user?._id || user?.userId || 'driver123'; // Fallback to default if no user
  };

  useEffect(() => {
    const fetchRecentTrips = async () => {
      try {
        setLoading(true);
        const driverId = getCurrentUserId();
        console.log('Fetching recent trips for driver ID:', driverId);
        const response = await getRecentTrips(driverId, 5, 30); // Last 5 trips in 30 days

        if (response?.data?.trips) {
          setRecentTrips(response.data.trips);
        }
      } catch (err) {
        console.error('Error fetching recent trips:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchRecentTrips();
  }, []);

  const formatTripData = trip => {
    return {
      id: trip.id || trip._id,
      name: trip.name || 'Unnamed Trip',
      startLocation: trip.origin?.address || trip.origin?.name || 'Unknown Location',
      endLocation: trip.destination?.address || trip.destination?.name || 'Unknown Location',
      startTime: trip.actual_start_time
        ? new Date(trip.actual_start_time).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          })
        : 'Unknown Time',
      endTime: trip.actual_end_time
        ? new Date(trip.actual_end_time).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          })
        : null,
      date: trip.actual_end_time
        ? new Date(trip.actual_end_time).toISOString().split('T')[0]
        : new Date().toISOString().split('T')[0],
      passenger: trip.passenger_name || 'Unknown Passenger',
      vehicle: {
        model: trip.vehicle_model || 'Unknown Vehicle',
        registration: trip.vehicle_registration || 'Unknown',
      },
      status: trip.status || 'completed',
      distance: trip.estimated_distance ? `${trip.estimated_distance} km` : 'Unknown distance',
      duration: trip.estimated_duration ? `${trip.estimated_duration}m` : 'Unknown duration',
      onTime:
        trip.scheduled_start_time && trip.actual_start_time
          ? new Date(trip.actual_start_time) <= new Date(trip.scheduled_start_time)
          : true, // Default to on time if we don't have timing data
    };
  };

  const getStatusColor = status => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'cancelled':
        return 'bg-red-100 text-red-800';
      case 'delayed':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = dateString => {
    const date = new Date(dateString);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(today.getDate() - 1);

    if (date.toDateString() === today.toDateString()) {
      return 'Today';
    } else if (date.toDateString() === yesterday.toDateString()) {
      return 'Yesterday';
    } else {
      return date.toLocaleDateString('en-US', {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
      });
    }
  };

  return (
    <div className="bg-card rounded-lg shadow-sm border border-border">
      {/* Header */}
      <div className="py-3 px-3 sm:p-4 border-b border-border">
        <div className="flex items-center justify-between">
          <h3 className="text-base sm:text-lg font-semibold text-foreground">Recent Trips</h3>
          <div className="flex items-center space-x-2">
            <span className="text-xs sm:text-sm text-muted-foreground">Last 5 trips</span>
            <button
              onClick={() => setIsCollapsed(!isCollapsed)}
              className="p-1 hover:bg-accent rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary focus:ring-opacity-50"
              aria-label={isCollapsed ? 'Expand recent trips' : 'Collapse recent trips'}
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
              <p className="text-sm">Loading recent trips...</p>
            </div>
          ) : error ? (
            <div className="p-4 sm:p-6 text-center text-red-500">
              <p className="text-sm">Error loading trips: {error}</p>
            </div>
          ) : recentTrips.length === 0 ? (
            <div className="p-4 sm:p-6 text-center text-muted-foreground">
              <MapPin className="h-10 w-10 sm:h-12 sm:w-12 mx-auto mb-2 opacity-50" />
              <p className="text-sm">No recent trips</p>
            </div>
          ) : (
            recentTrips.map(trip => {
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
                      {formattedTrip.onTime ? (
                        <CheckCircle
                          className="h-3 w-3 sm:h-4 sm:w-4 text-green-500"
                          title="On time"
                        />
                      ) : (
                        <AlertTriangle
                          className="h-3 w-3 sm:h-4 sm:w-4 text-yellow-500"
                          title="Delayed"
                        />
                      )}
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
                        {formattedTrip.startTime} - {formattedTrip.endTime}
                      </span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <User className="h-4 w-4 min-w-4 text-muted-foreground" />
                      <span className="text-muted-foreground truncate">
                        {formattedTrip.passenger}
                      </span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Car className="h-4 w-4 min-w-4 text-muted-foreground" />
                      <span className="text-muted-foreground truncate">
                        {formattedTrip.vehicle?.model} ({formattedTrip.vehicle?.registration})
                      </span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <MapPin className="h-4 w-4 min-w-4 text-muted-foreground" />
                      <span className="text-muted-foreground truncate">
                        {formattedTrip.distance} • {formattedTrip.duration}
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
      {!isCollapsed && recentTrips.length > 0 && (
        <div className="p-3 border-t border-border">
          <button className="w-full text-xs sm:text-sm text-primary hover:text-primary/80 font-medium transition-colors py-1">
            View Trip History
          </button>
        </div>
      )}
    </div>
  );
};

export default RecentTrips;
