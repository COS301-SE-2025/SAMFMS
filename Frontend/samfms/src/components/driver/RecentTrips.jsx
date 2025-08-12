import React from 'react';
import { MapPin, Clock, User, Car, CheckCircle, AlertTriangle, ChevronRight } from 'lucide-react';

const RecentTrips = () => {
  // Static recent trips data for now
  const recentTrips = [
    {
      id: 'T098',
      startLocation: 'City Mall',
      endLocation: 'Airport Terminal 1',
      startTime: '07:00 AM',
      endTime: '08:15 AM',
      date: '2025-08-12',
      passenger: 'Emily Davis',
      vehicle: 'VH-001',
      status: 'completed',
      distance: '28 km',
      duration: '1h 15m',
      onTime: true,
    },
    {
      id: 'T097',
      startLocation: 'Hotel Paradise',
      endLocation: 'Business Center',
      startTime: '03:30 PM',
      endTime: '04:10 PM',
      date: '2025-08-11',
      passenger: 'Robert Brown',
      vehicle: 'VH-001',
      status: 'completed',
      distance: '15 km',
      duration: '40m',
      onTime: true,
    },
    {
      id: 'T096',
      startLocation: 'Train Station',
      endLocation: 'University Campus',
      startTime: '10:00 AM',
      endTime: '10:55 AM',
      date: '2025-08-11',
      passenger: 'Lisa Anderson',
      vehicle: 'VH-001',
      status: 'completed',
      distance: '22 km',
      duration: '55m',
      onTime: false,
    },
    {
      id: 'T095',
      startLocation: 'Medical Center',
      endLocation: 'Residential Area',
      startTime: '01:15 PM',
      endTime: '02:00 PM',
      date: '2025-08-10',
      passenger: 'James Wilson',
      vehicle: 'VH-001',
      status: 'completed',
      distance: '18 km',
      duration: '45m',
      onTime: true,
    },
    {
      id: 'T094',
      startLocation: 'Shopping Plaza',
      endLocation: 'Office Complex',
      startTime: '11:30 AM',
      endTime: '12:20 PM',
      date: '2025-08-10',
      passenger: 'Maria Garcia',
      vehicle: 'VH-001',
      status: 'completed',
      distance: '20 km',
      duration: '50m',
      onTime: true,
    },
  ];

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
          <span className="text-xs sm:text-sm text-muted-foreground">Last 5 trips</span>
        </div>
      </div>

      {/* Trips List */}
      <div className="divide-y divide-border max-h-[320px] sm:max-h-none overflow-y-auto overscroll-contain">
        {recentTrips.length === 0 ? (
          <div className="p-4 sm:p-6 text-center text-muted-foreground">
            <MapPin className="h-10 w-10 sm:h-12 sm:w-12 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No recent trips</p>
          </div>
        ) : (
          recentTrips.map(trip => (
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
                  {trip.onTime ? (
                    <CheckCircle className="h-4 w-4 text-green-500" title="On time" />
                  ) : (
                    <AlertTriangle className="h-4 w-4 text-yellow-500" title="Delayed" />
                  )}
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
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="flex items-center space-x-2">
                  <Clock className="h-4 w-4 text-muted-foreground" />
                  <span className="text-muted-foreground">
                    {trip.startTime} - {trip.endTime}
                  </span>
                </div>
                <div className="flex items-center space-x-2">
                  <User className="h-4 w-4 text-muted-foreground" />
                  <span className="text-muted-foreground">{trip.passenger}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Car className="h-4 w-4 text-muted-foreground" />
                  <span className="text-muted-foreground">{trip.vehicle}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <MapPin className="h-4 w-4 text-muted-foreground" />
                  <span className="text-muted-foreground">
                    {trip.distance} • {trip.duration}
                  </span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Footer */}
      {recentTrips.length > 0 && (
        <div className="p-3 border-t border-border">
          <button className="w-full text-sm text-primary hover:text-primary/80 font-medium transition-colors">
            View Trip History
          </button>
        </div>
      )}
    </div>
  );
};

export default RecentTrips;
