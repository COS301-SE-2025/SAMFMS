import React from 'react';
import { MapPin, User, Clock, Calendar } from 'lucide-react';

const UpcomingTripsTable = ({ upcomingTrips = [] }) => {
  // Helper function to format date/time
  const formatDateTime = (dateString) => {
    if (!dateString) return 'Not set';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  // Helper function to format priority
  const formatPriority = (priority) => {
    switch (priority?.toLowerCase()) {
      case 'urgent': return 'High';
      case 'high': return 'High';
      case 'normal': return 'Medium';
      case 'low': return 'Low';
      default: return 'Medium';
    }
  };

  // Helper function to format status
  const formatStatus = (status) => {
    switch (status?.toLowerCase()) {
      case 'scheduled': return 'Scheduled';
      case 'in-progress': return 'In Progress';
      case 'completed': return 'Completed';
      default: return 'Scheduled';
    }
  };

  return (
    <div className="bg-card border border-border rounded-xl shadow-lg overflow-hidden animate-fade-in animate-delay-200">
      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Calendar className="h-5 w-5 text-primary" />
            <h3 className="text-lg font-semibold">Upcoming Trips</h3>
          </div>
          <div className="text-sm text-muted-foreground">
            {upcomingTrips.length} trips scheduled
          </div>
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
                Schedule
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Destination
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Priority
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Status
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {upcomingTrips.map(trip => (
              <tr key={trip.id} className="hover:bg-muted/30 transition-colors">
                <td className="px-4 py-4">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center">
                      <MapPin className="h-4 w-4 text-blue-600 dark:text-blue-300" />
                    </div>
                    <div>
                      <div className="font-medium text-foreground">{trip.name || 'Unnamed Trip'}</div>
                      <div className="text-sm text-muted-foreground">ID: #{trip.id.slice(-8)}</div>
                    </div>
                  </div>
                </td>
                <td className="px-4 py-4">
                  <div>
                    <div className="font-medium text-foreground">{trip.vehicleId?.slice(-8) || 'Not assigned'}</div>
                    <div className="text-sm text-muted-foreground flex items-center gap-1">
                      <User className="h-3 w-3" />
                      {trip.driverAssignment || 'No driver assigned'}
                    </div>
                  </div>
                </td>
                <td className="px-4 py-4">
                  <div className="flex items-center gap-1 text-sm">
                    <Clock className="h-3 w-3 text-muted-foreground" />
                    <span>{formatDateTime(trip.scheduledStartTime)}</span>
                  </div>
                </td>
                <td className="px-4 py-4">
                  <span className="text-sm">{trip.destination?.name || 'Unknown destination'}</span>
                </td>
                <td className="px-4 py-4">
                  <span
                    className={`px-2 py-1 text-xs font-medium rounded-full ${
                      formatPriority(trip.priority) === 'High'
                        ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300'
                        : formatPriority(trip.priority) === 'Medium'
                        ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300'
                        : 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300'
                    }`}
                  >
                    {formatPriority(trip.priority)}
                  </span>
                </td>
                <td className="px-4 py-4">
                  <span
                    className={`px-2 py-1 text-xs font-medium rounded-full ${
                      formatStatus(trip.status) === 'Scheduled'
                        ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300'
                        : formatStatus(trip.status) === 'In Progress'
                        ? 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300'
                        : 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300'
                    }`}
                  >
                    {formatStatus(trip.status)}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {upcomingTrips.length === 0 && (
        <div className="p-8 text-center text-muted-foreground">
          <MapPin className="h-12 w-12 mx-auto mb-3 opacity-50" />
          <p>No upcoming trips scheduled</p>
        </div>
      )}
    </div>
  );
};

export default UpcomingTripsTable;