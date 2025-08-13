import React from 'react';
import { Clock, MapPin, Calendar, User, AlertCircle, CheckCircle } from 'lucide-react';

const ActiveTripsPanel = ({ activeTrips }) => {
  // Function to format date in a more readable way
  const formatDateTime = dateString => {
    const date = new Date(dateString);
    return date.toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="bg-card dark:bg-card rounded-lg shadow-md p-6 mb-6 border border-border">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-semibold text-foreground flex items-center gap-2">
          <Clock className="h-5 w-5 text-primary" />
          Active Trips
        </h2>
        <span className="text-sm text-muted-foreground bg-muted px-3 py-1 rounded-full">
          {activeTrips?.length || 0} active
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {activeTrips?.map(trip => (
          <div
            key={trip.id}
            className={`border rounded-md hover:shadow-md transition-all duration-300 transform hover:-translate-y-1 ${
              trip.status === 'delayed'
                ? 'border-red-300 dark:border-red-800'
                : trip.status === 'on_time'
                ? 'border-green-300 dark:border-green-800'
                : 'border-border'
            }`}
          >
            <div
              className={`p-4 rounded-t-md ${
                trip.status === 'delayed'
                  ? 'bg-red-50 dark:bg-red-950/20'
                  : trip.status === 'on_time'
                  ? 'bg-green-50 dark:bg-green-950/20'
                  : 'bg-muted/20'
              }`}
            >
              <div className="flex justify-between items-center">
                <h3 className="font-medium text-foreground truncate pr-2">{trip.name}</h3>
                <span
                  className={`text-xs font-medium px-2 py-1 rounded-full flex items-center ${
                    trip.status === 'delayed'
                      ? 'bg-red-200 text-red-800 dark:bg-red-900/70 dark:text-red-200'
                      : trip.status === 'on_time'
                      ? 'bg-green-200 text-green-800 dark:bg-green-900/70 dark:text-green-200'
                      : 'bg-muted text-muted-foreground'
                  }`}
                >
                  {trip.status === 'delayed' ? (
                    <AlertCircle className="h-3 w-3 mr-1" />
                  ) : (
                    <CheckCircle className="h-3 w-3 mr-1" />
                  )}
                  {trip.status.replace('_', ' ').toUpperCase()}
                </span>
              </div>
            </div>

            <div className="p-4 space-y-2 bg-card">
              <div className="flex items-start gap-2">
                <Calendar className="h-4 w-4 text-muted-foreground mt-0.5 flex-shrink-0" />
                <div className="text-xs space-y-1">
                  <p className="text-muted-foreground">
                    <span className="font-medium text-foreground">Started:</span>{' '}
                    {formatDateTime(trip.startTime)}
                  </p>
                  <p className="text-muted-foreground">
                    <span className="font-medium text-foreground">ETA:</span>{' '}
                    {formatDateTime(trip.estimatedEndTime)}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <User className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                <p className="text-xs text-foreground font-medium truncate">{trip.driver.name}</p>
              </div>

              <div className="pt-1 border-t border-border flex justify-end">
                <button className="text-xs text-primary hover:underline">View Details</button>
              </div>
            </div>
          </div>
        ))}

        {!activeTrips?.length && (
          <div className="col-span-full flex flex-col items-center justify-center py-10 text-muted-foreground">
            <MapPin className="h-12 w-12 mb-3 opacity-30" />
            <p className="text-sm">No active trips at the moment</p>
            <p className="text-xs">Schedule a new trip to get started</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ActiveTripsPanel;
