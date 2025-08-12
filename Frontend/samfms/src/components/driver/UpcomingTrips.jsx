import React from 'react';
import { MapPin, Clock, User, Car, ChevronRight } from 'lucide-react';

const UpcomingTrips = () => {
  // Static upcoming trips data for now
  const upcomingTrips = [
    {
      id: 'T001',
      startLocation: 'Main Office',
      endLocation: 'Airport Terminal 2',
      startTime: '09:00 AM',
      endTime: '10:30 AM',
      date: '2025-08-13',
      passenger: 'John Smith',
      vehicle: 'VH-001',
      status: 'scheduled',
      distance: '25 km',
      estimatedDuration: '1h 30m',
    },
    {
      id: 'T002',
      startLocation: 'Downtown Plaza',
      endLocation: 'Business District',
      startTime: '02:00 PM',
      endTime: '02:45 PM',
      date: '2025-08-13',
      passenger: 'Sarah Johnson',
      vehicle: 'VH-001',
      status: 'scheduled',
      distance: '12 km',
      estimatedDuration: '45m',
    },
    {
      id: 'T003',
      startLocation: 'Hotel Grand',
      endLocation: 'Conference Center',
      startTime: '08:30 AM',
      date: '2025-08-14',
      passenger: 'Mike Wilson',
      vehicle: 'VH-001',
      status: 'scheduled',
      distance: '18 km',
      estimatedDuration: '1h 15m',
    },
  ];

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
          <span className="text-xs sm:text-sm text-muted-foreground">
            {upcomingTrips.length} trips scheduled
          </span>
        </div>
      </div>

      {/* Trips List */}
      <div className="divide-y divide-border max-h-[320px] sm:max-h-none overflow-y-auto overscroll-contain">
        {upcomingTrips.length === 0 ? (
          <div className="p-4 sm:p-6 text-center text-muted-foreground">
            <MapPin className="h-10 w-10 sm:h-12 sm:w-12 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No upcoming trips</p>
          </div>
        ) : (
          upcomingTrips.map(trip => (
            <div key={trip.id} className="py-3 px-3 sm:p-4 hover:bg-accent/50 transition-colors cursor-pointer">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-medium text-foreground">{trip.id}</span>
                  <span
                    className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(
                      trip.status
                    )}`}
                  >
                    {trip.status}
                  </span>
                </div>
                <span className="text-sm text-muted-foreground">{formatDate(trip.date)}</span>
              </div>

              {/* Route */}
              <div className="flex flex-col sm:flex-row items-start sm:items-center space-y-2 sm:space-y-0 sm:space-x-2 mb-3">
                <div className="flex items-center space-x-2 w-full sm:flex-1 truncate">
                  <div className="w-2 h-2 min-w-2 bg-green-500 rounded-full"></div>
                  <span className="text-sm text-foreground font-medium truncate">{trip.startLocation}</span>
                </div>
                <ChevronRight className="hidden sm:block h-4 w-4 text-muted-foreground" />
                <div className="flex items-center space-x-2 w-full sm:flex-1 truncate">
                  <div className="w-2 h-2 min-w-2 bg-red-500 rounded-full"></div>
                  <span className="text-sm text-foreground font-medium truncate">{trip.endLocation}</span>
                </div>
              </div>

              {/* Trip Details */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 sm:gap-4 text-sm">
                <div className="flex items-center space-x-2">
                  <Clock className="h-4 w-4 min-w-4 text-muted-foreground" />
                  <span className="text-muted-foreground truncate">
                    {trip.startTime}
                    {trip.endTime && ` - ${trip.endTime}`}
                  </span>
                </div>
                <div className="flex items-center space-x-2">
                  <User className="h-4 w-4 min-w-4 text-muted-foreground" />
                  <span className="text-muted-foreground truncate">{trip.passenger}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Car className="h-4 w-4 text-muted-foreground" />
                  <span className="text-muted-foreground">{trip.vehicle}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <MapPin className="h-4 w-4 text-muted-foreground" />
                  <span className="text-muted-foreground">
                    {trip.distance} • {trip.estimatedDuration}
                  </span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Footer */}
      {upcomingTrips.length > 0 && (
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
