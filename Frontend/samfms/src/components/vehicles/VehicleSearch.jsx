import React, { useState } from 'react';
import { Search } from 'lucide-react';
import VehicleFilters from './VehicleFilters';

const VehicleSearch = ({ filterOpen, setFilterOpen, onApplyFilters, onResetFilters, onSearch }) => {
  const [searchValue, setSearchValue] = useState('');

  const handleSearch = () => {
    onSearch(searchValue);
  };

  return (
    <div className="flex flex-col md:flex-row gap-4 mb-6">
      <div className="relative flex-grow">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <Search size={18} className="text-muted-foreground" />
        </div>
        <input
          type="text"
          value={searchValue}
          onChange={e => setSearchValue(e.target.value)}
          onKeyDown={e => {
            if (e.key === 'Enter') {
              handleSearch();
            }
          }}
          placeholder="Search vehicles..."
          className="pl-10 pr-4 py-2 w-full border border-border rounded-md bg-background"
        />
      </div>
      <VehicleFilters
        filterOpen={filterOpen}
        setFilterOpen={setFilterOpen}
        onApplyFilters={onApplyFilters}
        onResetFilters={onResetFilters}
      />
    </div>
  );
};

export default VehicleSearch;
