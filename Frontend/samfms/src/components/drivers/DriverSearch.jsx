import React, { useState } from 'react';
import { Search, Filter, X } from 'lucide-react';

const DriverSearch = ({ filterOpen, setFilterOpen, onSearch, onApplyFilters, onResetFilters }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState({
    status: '',
    licenseType: '',
    department: '',
    dateRange: '',
  });

  const handleSearch = e => {
    e.preventDefault();
    onSearch(searchTerm);
  };

  const handleFilterChange = e => {
    setFilters({
      ...filters,
      [e.target.name]: e.target.value,
    });
  };

  const handleApplyFilters = () => {
    onApplyFilters(filters);
  };

  const handleResetFilters = () => {
    setFilters({
      status: '',
      licenseType: '',
      department: '',
      dateRange: '',
    });
    onResetFilters();
  };

  return (
    <div className="mb-6">
      <div className="flex flex-col md:flex-row gap-4">
        <form onSubmit={handleSearch} className="flex-grow">
          <div className="relative">
            <input
              type="text"
              placeholder="Search drivers by name, ID, or license number"
              className="w-full px-4 py-2 pl-10 rounded-md border border-input bg-background"
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
            />
            <Search
              className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground"
              size={18}
            />
          </div>
        </form>
        <button
          onClick={() => setFilterOpen(!filterOpen)}
          className="flex items-center justify-center gap-2 px-4 py-2 bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80"
        >
          <Filter size={18} />
          {filterOpen ? 'Hide Filters' : 'Show Filters'}
        </button>
      </div>

      {filterOpen && (
        <div className="mt-4 p-4 border border-border rounded-md bg-muted/10 animate-in fade-in-0 zoom-in-95 duration-150">
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-medium">Filter Drivers</h3>
            <button
              onClick={() => setFilterOpen(false)}
              className="text-muted-foreground hover:text-foreground"
            >
              <X size={18} />
            </button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium mb-1">Status</label>
              <select
                name="status"
                value={filters.status}
                onChange={handleFilterChange}
                className="w-full p-2 rounded-md border border-input bg-background"
              >
                <option value="">Any Status</option>
                <option value="available">Available</option>
                <option value="onTrip">On Trip</option>
                <option value="onLeave">On Leave</option>
                <option value="inactive">Inactive</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">License Type</label>
              <select
                name="licenseType"
                value={filters.licenseType}
                onChange={handleFilterChange}
                className="w-full p-2 rounded-md border border-input bg-background"
              >
                <option value="">Any License</option>
                <option value="A">Class A</option>
                <option value="B">Class B</option>
                <option value="C">Class C</option>
                <option value="CDL">CDL</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Department</label>
              <select
                name="department"
                value={filters.department}
                onChange={handleFilterChange}
                className="w-full p-2 rounded-md border border-input bg-background"
              >
                <option value="">Any Department</option>
                <option value="sales">Sales</option>
                <option value="delivery">Delivery</option>
                <option value="executive">Executive</option>
                <option value="support">Support</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">License Expiry</label>
              <select
                name="dateRange"
                value={filters.dateRange}
                onChange={handleFilterChange}
                className="w-full p-2 rounded-md border border-input bg-background"
              >
                <option value="">Any Date</option>
                <option value="30days">Expiring in 30 days</option>
                <option value="60days">Expiring in 60 days</option>
                <option value="90days">Expiring in 90 days</option>
                <option value="expired">Expired</option>
              </select>
            </div>
          </div>
          <div className="flex gap-2 justify-end">
            <button
              onClick={handleResetFilters}
              className="px-4 py-2 border border-input rounded-md hover:bg-accent hover:text-accent-foreground"
            >
              Reset
            </button>
            <button
              onClick={handleApplyFilters}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
            >
              Apply Filters
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default DriverSearch;
