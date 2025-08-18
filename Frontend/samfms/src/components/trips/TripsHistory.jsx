import React, { useState } from 'react';
import {
  History,
  ChevronDown,
  Search,
  User,
  Car,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Filter,
} from 'lucide-react';

const TripsHistory = ({ trips }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [showFilters, setShowFilters] = useState(false);

  // Format date in a more readable way
  const formatDateTime = dateString => {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // Get status badge styling
  const getStatusBadge = status => {
    const statusMap = {
      completed: {
        bg: 'bg-green-100 dark:bg-green-900/40',
        text: 'text-green-800 dark:text-green-200',
        icon: <CheckCircle className="h-3 w-3 mr-1" />,
      },
      cancelled: {
        bg: 'bg-red-100 dark:bg-red-900/40',
        text: 'text-red-800 dark:text-red-200',
        icon: <XCircle className="h-3 w-3 mr-1" />,
      },
      delayed: {
        bg: 'bg-amber-100 dark:bg-amber-900/40',
        text: 'text-amber-800 dark:text-amber-200',
        icon: <AlertTriangle className="h-3 w-3 mr-1" />,
      },
      'in progress': {
        bg: 'bg-blue-100 dark:bg-blue-900/40',
        text: 'text-blue-800 dark:text-blue-200',
        icon: <Clock className="h-3 w-3 mr-1" />,
      },
    };

    const style = statusMap[status?.toLowerCase()] || {
      bg: 'bg-gray-100 dark:bg-gray-800',
      text: 'text-gray-800 dark:text-gray-200',
      icon: null,
    };

    return (
      <span
        className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${style.bg} ${style.text}`}
      >
        {style.icon}
        {status ? status.charAt(0).toUpperCase() + status.slice(1) : 'Unknown'}
      </span>
    );
  };

  // Filter trips based on search term and status
  const filteredTrips =
    trips?.filter(trip => {
      const matchesSearch =
        (trip.name?.toLowerCase() || '').includes(searchTerm.toLowerCase()) ||
        (trip.driver?.toLowerCase() || '').includes(searchTerm.toLowerCase()) ||
        (trip.vehicle?.toLowerCase() || '').includes(searchTerm.toLowerCase());

      const matchesStatus =
        statusFilter === 'all' || trip.status?.toLowerCase() === statusFilter.toLowerCase();

      return matchesSearch && matchesStatus;
    }) || [];

  return (
    <div className="bg-card dark:bg-card rounded-lg shadow-md p-6 border border-border">
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center gap-2">
          <History className="h-5 w-5 text-primary" />
          <h2 className="text-xl font-semibold text-foreground">Trip History</h2>
        </div>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="text-sm text-muted-foreground hover:text-foreground flex items-center gap-1"
        >
          <Filter className="h-4 w-4" />
          Filters
          <ChevronDown
            className={`h-4 w-4 transition-transform ${showFilters ? 'rotate-180' : ''}`}
          />
        </button>
      </div>

      {/* Search and filter section */}
      <div
        className={`mb-4 space-y-3 transition-all duration-300 ${showFilters ? 'block' : 'hidden'}`}
      >
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-grow">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
            <input
              type="text"
              placeholder="Search trips..."
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              className="pl-9 pr-4 py-2 w-full border border-input rounded-md bg-background text-foreground focus:ring-2 focus:ring-primary focus:border-transparent"
            />
          </div>
          <select
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value)}
            className="px-3 py-2 border border-input rounded-md bg-background text-foreground focus:ring-2 focus:ring-primary focus:border-transparent sm:w-40"
          >
            <option value="all">All Statuses</option>
            <option value="completed">Completed</option>
            <option value="cancelled">Cancelled</option>
            <option value="delayed">Delayed</option>
            <option value="in progress">In Progress</option>
          </select>
        </div>
      </div>

      {/* Table section */}
      <div className="overflow-x-auto border border-border rounded-md">
        <table className="w-full">
          <thead>
            <tr className="bg-muted/30">
              <th className="text-left py-3 px-4 text-foreground font-medium">Trip Name</th>
              <th className="text-left py-3 px-4 text-foreground font-medium">Driver</th>
              <th className="text-left py-3 px-4 text-foreground font-medium">Vehicle</th>
              <th className="text-left py-3 px-4 text-foreground font-medium">Start Time</th>
              <th className="text-left py-3 px-4 text-foreground font-medium">End Time</th>
              <th className="text-left py-3 px-4 text-foreground font-medium">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {filteredTrips.length > 0 ? (
              filteredTrips.map(trip => (
                <tr key={trip.id} className="hover:bg-accent/10 transition-colors cursor-pointer">
                  <td className="py-3 px-4 text-foreground font-medium">
                    {trip.name || 'Unnamed Trip'}
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      <User className="h-3.5 w-3.5 text-muted-foreground" />
                      <span className="text-muted-foreground">{trip.driver || '-'}</span>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      <Car className="h-3.5 w-3.5 text-muted-foreground" />
                      <span className="text-muted-foreground">{trip.vehicle || '-'}</span>
                    </div>
                  </td>
                  <td className="py-3 px-4 text-muted-foreground">
                    {formatDateTime(trip.startTime)}
                  </td>
                  <td className="py-3 px-4 text-muted-foreground">
                    {formatDateTime(trip.endTime)}
                  </td>
                  <td className="py-3 px-4">{getStatusBadge(trip.status)}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="6" className="py-10 text-center text-muted-foreground">
                  {trips?.length > 0
                    ? 'No trips match your search criteria'
                    : 'No trip history available'}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default TripsHistory;
