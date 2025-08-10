import React from 'react';

const ActiveTripsPanel = ({ activeTrips }) => {
  return (
    <div className="bg-card dark:bg-card rounded-lg shadow-md p-6 mb-6 border border-border">
      <h2 className="text-xl font-semibold mb-4 text-foreground">Active Trips</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {activeTrips?.map(trip => (
          <div
            key={trip.id}
            className={`border rounded-md p-4 ${
              trip.status === 'delayed'
                ? 'border-red-300 bg-red-50 dark:border-red-800 dark:bg-red-950/20'
                : trip.status === 'on_time'
                ? 'border-green-300 bg-green-50 dark:border-green-800 dark:bg-green-950/20'
                : 'border-border bg-card'
            }`}
          >
            <h3 className="font-medium text-foreground">{trip.name}</h3>
            <p className="text-sm text-muted-foreground">
              Started: {new Date(trip.startTime).toLocaleString()}
            </p>
            <p className="text-sm text-muted-foreground">
              ETA: {new Date(trip.estimatedEndTime).toLocaleString()}
            </p>
            <p className="text-sm text-muted-foreground">
              Scheduled: {new Date(trip.scheduledEndTime).toLocaleString()}
            </p>
            <div className="mt-2 flex justify-between items-center">
              <span className="text-sm text-foreground">Driver: {trip.driver.name}</span>
              <span
                className={`text-sm px-2 py-1 rounded-full ${
                  trip.status === 'delayed'
                    ? 'bg-red-200 text-red-800 dark:bg-red-900 dark:text-red-200'
                    : trip.status === 'on_time'
                    ? 'bg-green-200 text-green-800 dark:bg-green-900 dark:text-green-200'
                    : 'bg-muted text-muted-foreground'
                }`}
              >
                {trip.status.replace('_', ' ').toUpperCase()}
              </span>
            </div>
          </div>
        ))}
        {!activeTrips?.length && (
          <div className="col-span-full text-center text-muted-foreground">No active trips</div>
        )}
      </div>
    </div>
  );
};

export default ActiveTripsPanel;
