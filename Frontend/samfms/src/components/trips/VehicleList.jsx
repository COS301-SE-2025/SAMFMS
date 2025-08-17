import React, { useState } from 'react';
import {
  Search,
  Filter,
  ChevronDown,
  Check,
  ChevronLeft,
  ChevronRight,
  Car,
  AlertCircle,
  CheckCircle,
} from 'lucide-react';

const VehicleList = ({ vehicles, onSelectVehicle }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [selectedStatus, setSelectedStatus] = useState('all');
  const [sortBy, setSortBy] = useState('id');
  const [currentPage, setCurrentPage] = useState(1);
  const [vehiclesPerPage] = useState(5); // Show 5 vehicles per page for better readability
  const [sortDropdownOpen, setSortDropdownOpen] = useState(false);

  // Filter and sort vehicles
  const filteredVehicles = vehicles
    .filter(vehicle => {
      // Apply search filter
      const matchesSearch =
        String(vehicle.id).toLowerCase().includes(searchTerm.toLowerCase()) ||
        (vehicle.model ? vehicle.model.toLowerCase().includes(searchTerm.toLowerCase()) : false);

      // Apply status filter
      const matchesStatus = selectedStatus === 'all' || vehicle.status === selectedStatus;

      return matchesSearch && matchesStatus;
    })
    .sort((a, b) => {
      // Apply sorting
      if (sortBy === 'id') {
        return a.id - b.id;
      } else if (sortBy === 'status') {
        return a.status.localeCompare(b.status);
      } else if (sortBy === 'model') {
        return a.model.localeCompare(b.model);
      }
      return 0;
    });

  // Calculate pagination values
  const indexOfLastVehicle = currentPage * vehiclesPerPage;
  const indexOfFirstVehicle = indexOfLastVehicle - vehiclesPerPage;
  const currentVehicles = filteredVehicles.slice(indexOfFirstVehicle, indexOfLastVehicle);
  const totalPages = Math.ceil(filteredVehicles.length / vehiclesPerPage);

  // Reset to first page when search/filter changes
  React.useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm, selectedStatus, sortBy]);

  const handleSearch = e => {
    e.preventDefault();
    // Search is already applied via the filter
  };

  const getStatusIndicatorClass = status => {
    switch (status) {
      case 'online':
        return 'bg-green-500';
      case 'offline':
        return 'bg-amber-500';
      // case 'idle':
      //   return 'bg-blue-500';
      // case 'maintenance':
      //   return 'bg-amber-500';
      // case 'breakdown':
      //   return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getStatusLabel = status => {
    return status.charAt(0).toUpperCase() + status.slice(1);
  };

  return (
    <div className="bg-card rounded-lg shadow-md border border-border overflow-hidden h-[500px] flex flex-col">
      <div className="p-4 border-b border-border">
        <h3 className="font-semibold mb-3">Vehicle Locations</h3>

        {/* Search and filters */}
        <form onSubmit={handleSearch} className="relative mb-3">
          <input
            type="text"
            placeholder="Search vehicles..."
            className="w-full px-4 py-2 pl-10 rounded-md border border-input bg-background text-sm"
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
          />
          <Search
            className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground"
            size={16}
          />
        </form>

        <div className="flex justify-between">
          <button
            className="text-sm flex items-center gap-1 text-primary"
            onClick={() => setShowFilters(!showFilters)}
          >
            <Filter size={14} /> Filters
          </button>

          <div className="relative">
            <button
              className="text-sm flex items-center gap-1 text-primary"
              onClick={() => document.getElementById('sortDropdown').classList.toggle('hidden')}
            >
              Sort by: {sortBy === 'id' ? 'Vehicle ID' : sortBy === 'status' ? 'Status' : 'Model'}
              <ChevronDown size={14} />
            </button>

            <div
              id="sortDropdown"
              className="hidden absolute right-0 top-full mt-1 bg-background border border-input rounded-md shadow-md z-10"
            >
              <div className="p-1">
                <button
                  onClick={() => {
                    setSortBy('id');
                    document.getElementById('sortDropdown').classList.add('hidden');
                  }}
                  className="flex items-center gap-2 px-3 py-1.5 text-sm w-full text-left hover:bg-accent rounded-sm"
                >
                  {sortBy === 'id' && <Check size={14} />}
                  <span className={sortBy === 'id' ? '' : 'ml-5'}>Vehicle ID</span>
                </button>
                <button
                  onClick={() => {
                    setSortBy('status');
                    document.getElementById('sortDropdown').classList.add('hidden');
                  }}
                  className="flex items-center gap-2 px-3 py-1.5 text-sm w-full text-left hover:bg-accent rounded-sm"
                >
                  {sortBy === 'status' && <Check size={14} />}
                  <span className={sortBy === 'status' ? '' : 'ml-5'}>Status</span>
                </button>
                <button
                  onClick={() => {
                    setSortBy('model');
                    document.getElementById('sortDropdown').classList.add('hidden');
                  }}
                  className="flex items-center gap-2 px-3 py-1.5 text-sm w-full text-left hover:bg-accent rounded-sm"
                >
                  {sortBy === 'model' && <Check size={14} />}
                  <span className={sortBy === 'model' ? '' : 'ml-5'}>Model</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        {showFilters && (
          <div className="mt-3 p-3 bg-muted/10 border border-border rounded-md">
            <p className="text-sm font-medium mb-2">Filter by status:</p>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => setSelectedStatus('all')}
                className={`px-2 py-1 text-xs rounded-full ${
                  selectedStatus === 'all'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-muted-foreground'
                }`}
              >
                All
              </button>
              <button
                onClick={() => setSelectedStatus('online')}
                className={`px-2 py-1 text-xs rounded-full ${
                  selectedStatus === 'online'
                    ? 'bg-green-500 text-white'
                    : 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200'
                }`}
              >
                Active
              </button>
              <button
                onClick={() => setSelectedStatus('offline')}
                className={`px-2 py-1 text-xs rounded-full ${
                  selectedStatus === 'offline'
                    ? 'bg-blue-500 text-white'
                    : 'bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200'
                }`}
              >
                Idle
              </button>
              {/* <button
                onClick={() => setSelectedStatus('maintenance')}
                className={`px-2 py-1 text-xs rounded-full ${
                  selectedStatus === 'maintenance'
                    ? 'bg-amber-500 text-white'
                    : 'bg-amber-100 dark:bg-amber-900 text-amber-800 dark:text-amber-200'
                }`}
              >
                Maintenance
              </button> */}
              {/* <button
                onClick={() => setSelectedStatus('breakdown')}
                className={`px-2 py-1 text-xs rounded-full ${
                  selectedStatus === 'breakdown'
                    ? 'bg-red-500 text-white'
                    : 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200'
                }`}
              >
                Breakdown
              </button> */}
            </div>
          </div>
        )}
      </div>

      {/* Vehicle list */}
      <div className="flex-grow flex flex-col">
        <div className="overflow-y-auto flex-grow">
          {currentVehicles.length > 0 ? (
            currentVehicles.map(vehicle => (
              <div
                key={vehicle.id}
                className="p-4 border-b border-border hover:bg-accent/10 cursor-pointer transition-colors"
                onClick={() => onSelectVehicle(vehicle)}
              >
                <div className="flex items-center mb-2">
                  <div
                    className={`w-2 h-2 rounded-full ${getStatusIndicatorClass(
                      vehicle.status
                    )} mr-2`}
                  ></div>
                  <span className="font-medium">{vehicle.id}</span>
                  <span className="ml-auto text-xs bg-muted px-2 py-0.5 rounded">
                    {getStatusLabel(vehicle.status)}
                  </span>
                </div>
                <div className="text-sm mb-1">{vehicle.model}</div>
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>{vehicle.driver || 'No driver assigned'}</span>
                  <span>{vehicle.lastUpdate || 'Unknown'}</span>
                </div>
              </div>
            ))
          ) : (
            <div className="p-8 text-center text-muted-foreground">
              No vehicles match your search criteria
            </div>
          )}
        </div>

        {/* Pagination Controls */}
        {totalPages > 1 && (
          <div className="px-4 py-3 border-t border-border flex items-center justify-between bg-muted/30">
            <div className="text-sm text-muted-foreground">
              Showing {indexOfFirstVehicle + 1} to{' '}
              {Math.min(indexOfLastVehicle, filteredVehicles.length)} of {filteredVehicles.length}{' '}
              vehicles
            </div>
            <div className="flex items-center gap-1">
              <button
                onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                disabled={currentPage === 1}
                className="h-8 w-8 p-0 border border-input bg-background hover:bg-accent hover:text-accent-foreground disabled:pointer-events-none disabled:opacity-50 rounded-md flex items-center justify-center text-sm font-medium"
                title="Previous page"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>

              {/* Page numbers */}
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                let pageNumber;
                if (totalPages <= 5) {
                  pageNumber = i + 1;
                } else if (currentPage <= 3) {
                  pageNumber = i + 1;
                } else if (currentPage >= totalPages - 2) {
                  pageNumber = totalPages - 4 + i;
                } else {
                  pageNumber = currentPage - 2 + i;
                }

                return (
                  <button
                    key={pageNumber}
                    onClick={() => setCurrentPage(pageNumber)}
                    className={`h-8 w-8 p-0 text-sm font-medium rounded-md flex items-center justify-center ${
                      currentPage === pageNumber
                        ? 'bg-primary text-primary-foreground'
                        : 'border border-input bg-background hover:bg-accent hover:text-accent-foreground'
                    }`}
                    title={`Go to page ${pageNumber}`}
                  >
                    {pageNumber}
                  </button>
                );
              })}

              <button
                onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                disabled={currentPage === totalPages}
                className="h-8 w-8 p-0 border border-input bg-background hover:bg-accent hover:text-accent-foreground disabled:pointer-events-none disabled:opacity-50 rounded-md flex items-center justify-center text-sm font-medium"
                title="Next page"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default VehicleList;
