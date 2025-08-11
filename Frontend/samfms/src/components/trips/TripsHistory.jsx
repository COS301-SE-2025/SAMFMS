import React from 'react';

const TripsHistory = ({ trips }) => {
  return (
    <div className="bg-card dark:bg-card rounded-lg shadow-md p-6 border border-border">
      <h2 className="text-xl font-semibold mb-4 text-foreground">Trip History</h2>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-border">
              <th className="text-left py-3 px-4 text-foreground">Trip Name</th>
              <th className="text-left py-3 px-4 text-foreground">Driver</th>
              <th className="text-left py-3 px-4 text-foreground">Vehicle</th>
              <th className="text-left py-3 px-4 text-foreground">Start Time</th>
              <th className="text-left py-3 px-4 text-foreground">End Time</th>
              <th className="text-left py-3 px-4 text-foreground">Status</th>
            </tr>
          </thead>
          <tbody>
            {trips?.map(trip => (
              <tr key={trip.id} className="border-b border-border hover:bg-accent/10">
                <td className="py-3 px-4 text-foreground">{trip.name}</td>
                <td className="py-3 px-4 text-muted-foreground">{trip.driver}</td>
                <td className="py-3 px-4 text-muted-foreground">{trip.vehicle}</td>
                <td className="py-3 px-4 text-muted-foreground">{trip.startTime}</td>
                <td className="py-3 px-4 text-muted-foreground">{trip.endTime}</td>
                <td className="py-3 px-4 text-muted-foreground">{trip.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default TripsHistory;
