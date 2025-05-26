import React from 'react';
import { Filter, ChevronDown, X } from 'lucide-react';

const VehicleFilters = ({ filterOpen, setFilterOpen, onApplyFilters, onResetFilters }) => {
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
              <button className="text-xs text-primary">Save Filter</button>
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
              <select className="w-full border border-border rounded-md bg-background p-2">
                <option value="">All Statuses</option>
                <option value="active">Active</option>
                <option value="maintenance">Maintenance</option>
                <option value="out-of-service">Out of Service</option>
              </select>
            </div>
            <div>
              <label className="text-sm font-medium block mb-1">Year</label>
              <select className="w-full border border-border rounded-md bg-background p-2">
                <option value="">All Years</option>
                <option value="2023">2023</option>
                <option value="2022">2022</option>
                <option value="2021">2021</option>
              </select>
            </div>
            <div>
              <label className="text-sm font-medium block mb-1">Department</label>
              <select className="w-full border border-border rounded-md bg-background p-2">
                <option value="">All Departments</option>
                <option value="sales">Sales</option>
                <option value="delivery">Delivery</option>
                <option value="executive">Executive</option>
                <option value="support">Support</option>
                <option value="construction">Construction</option>
              </select>
            </div>
            <div>
              <label className="text-sm font-medium block mb-1">Fuel Type</label>
              <select className="w-full border border-border rounded-md bg-background p-2">
                <option value="">All Fuel Types</option>
                <option value="gasoline">Gasoline</option>
                <option value="diesel">Diesel</option>
                <option value="hybrid">Hybrid</option>
                <option value="electric">Electric</option>
              </select>
            </div>
            <div>
              <label className="text-sm font-medium block mb-1">Tags</label>
              <div className="flex flex-wrap gap-1 mb-2">
                <span className="bg-primary/10 text-primary text-xs px-2 py-1 rounded-full flex items-center">
                  Executive <X size={12} className="ml-1 cursor-pointer" />
                </span>
                <span className="bg-primary/10 text-primary text-xs px-2 py-1 rounded-full flex items-center">
                  Sales <X size={12} className="ml-1 cursor-pointer" />
                </span>
              </div>
              <div className="relative">
                <input
                  className="w-full border border-border rounded-md bg-background p-2"
                  placeholder="Add tag..."
                />
              </div>
            </div>
            <div className="pt-2 flex justify-between">
              <button onClick={onResetFilters} className="text-sm text-muted-foreground">
                Reset Filters
              </button>
              <button
                onClick={onApplyFilters}
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
