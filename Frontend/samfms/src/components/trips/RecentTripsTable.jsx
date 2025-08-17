import React from 'react';
import { MapPin, User, Clock } from 'lucide-react';

const RecentTripsTable = ({ recentTrips = [] }) => {
  return (
    <div className="bg-card border border-border rounded-xl shadow-lg overflow-hidden animate-fade-in animate-delay-200">
      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Clock className="h-5 w-5 text-primary" />
            <h3 className="text-lg font-semibold">Recent Trips</h3>
          </div>
          <div className="text-sm text-muted-foreground">{recentTrips.length} completed trips</div>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-muted/50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Trip Details
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Vehicle & Driver
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Completed
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Destination
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Duration
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Distance
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Status
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {recentTrips.map(trip => (
              <tr key={trip.id} className="hover:bg-muted/30 transition-colors">
                <td className="px-4 py-4">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center">
                      <MapPin className="h-4 w-4 text-green-600 dark:text-green-300" />
                    </div>
                    <div>
                      <div className="font-medium text-foreground">{trip.tripName}</div>
                      <div className="text-sm text-muted-foreground">ID: #{trip.id}</div>
                    </div>
                  </div>
                </td>
                <td className="px-4 py-4">
                  <div>
                    <div className="font-medium text-foreground">{trip.vehicle}</div>
                    <div className="text-sm text-muted-foreground flex items-center gap-1">
                      <User className="h-3 w-3" />
                      {trip.driver}
                    </div>
                  </div>
                </td>
                <td className="px-4 py-4">
                  <div className="flex items-center gap-1 text-sm">
                    <Clock className="h-3 w-3 text-muted-foreground" />
                    <span>{trip.completedAt}</span>
                  </div>
                </td>
                <td className="px-4 py-4">
                  <span className="text-sm">{trip.destination}</span>
                </td>
                <td className="px-4 py-4">
                  <span className="text-sm font-medium">{trip.duration}</span>
                </td>
                <td className="px-4 py-4">
                  <span className="text-sm text-muted-foreground">{trip.distance}</span>
                </td>
                <td className="px-4 py-4">
                  <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300">
                    {trip.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default RecentTripsTable;
