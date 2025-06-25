import React from 'react';
import { Search } from 'lucide-react';

const VehicleSearch = ({ onSearch }) => {
  return (
    <div className="relative w-full">
      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
        <Search size={18} className="text-muted-foreground" />
      </div>
      <input
        type="text"
        placeholder="Search vehicles..."
        className="pl-10 pr-4 py-2 w-full border border-border rounded-md bg-background"
        onChange={e => onSearch(e.target.value)}
      />
    </div>
  );
};

export default VehicleSearch;
