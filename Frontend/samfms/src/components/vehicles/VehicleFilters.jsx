import React, { useState } from 'react';
import { Filter, ChevronDown, X } from 'lucide-react';

const VehicleFilters = ({ filterOpen, setFilterOpen, onApplyFilters, onResetFilters }) => {
  const [filters, setFilters] = useState({
    status: '',
    make: '',
    year: '',
    department: '',
    fuelType: '',
  });

  const handleChange = e => {
    const { name, value } = e.target;
    setFilters(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleApply = () => {
    onApplyFilters(filters);
    setFilterOpen(false);
  };

  const handleReset = () => {
    setFilters({
      status: '',
      make: '',
      year: '',
      department: '',
      fuelType: '',
    });
    onResetFilters();
    setFilterOpen(false);
  };

  return (
    <div className="relative">
      <button
        onClick={() => setFilterOpen(!filterOpen)}
        className="flex items-center gap-2 px-4 py-2 border border-border rounded-md bg-background hover:bg-accent transition"
      >
        <Filter size={18} />
        <span>Filter</span>
        <ChevronDown size={16} />
      </button>
      {filterOpen && (
        <div className="absolute right-0 mt-1 w-80 p-4 bg-card rounded-md shadow-lg border border-border z-10">
          <div className="flex justify-between items-center mb-3">
            <h3 className="font-medium">Filter Vehicles</h3>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setFilterOpen(false)}
                className="text-muted-foreground hover:text-foreground"
              >
                <X size={16} />
              </button>
            </div>
          </div>
          <div className="space-y-3">
            <div>
              <label className="text-sm font-medium block mb-1">Status</label>
              <select
                className="w-full border border-border rounded-md bg-background p-2"
                name="status"
                value={filters.status}
                onChange={handleChange}
              >
                <option value="">All Statuses</option>
                <option value="active">Active</option>
                <option value="maintenance">Maintenance</option>
                <option value="inactive">Inactive</option>
              </select>
            </div>
            <div>
              <label className="text-sm font-medium block mb-1">Make</label>
              <select
                className="w-full border border-border rounded-md bg-background p-2"
                name="make"
                value={filters.make}
                onChange={handleChange}
              >
                <option value="">All Makes</option>
                <option value="Toyota">Toyota</option>
                <option value="Ford">Ford</option>
                <option value="Honda">Honda</option>
                <option value="Volkswagen">Volkswagen</option>
                <option value="BMW">BMW</option>
                <option value="Mercedes">Mercedes</option>
                <option value="Nissan">Nissan</option>
              </select>
            </div>
            <div>
              <label className="text-sm font-medium block mb-1">Year</label>
              <select
                className="w-full border border-border rounded-md bg-background p-2"
                name="year"
                value={filters.year}
                onChange={handleChange}
              >
                <option value="">All Years</option>
                <option value="2025">2025</option>
                <option value="2024">2024</option>
                <option value="2023">2023</option>
                <option value="2022">2022</option>
                <option value="2021">2021</option>
                <option value="2020">2020</option>
              </select>
            </div>
            <div>
              <label className="text-sm font-medium block mb-1">Fuel Type</label>
              <select
                className="w-full border border-border rounded-md bg-background p-2"
                name="fuelType"
                value={filters.fuelType}
                onChange={handleChange}
              >
                <option value="">All Fuel Types</option>
                <option value="gasoline">Gasoline</option>
                <option value="diesel">Diesel</option>
                <option value="hybrid">Hybrid</option>
                <option value="electric">Electric</option>
              </select>
            </div>
            <div className="pt-2 flex justify-between">
              <button onClick={handleReset} className="text-sm text-muted-foreground">
                Reset Filters
              </button>
              <button
                onClick={handleApply}
                className="bg-primary text-primary-foreground px-3 py-1 rounded-md text-sm"
              >
                Apply Filters
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default VehicleFilters;
