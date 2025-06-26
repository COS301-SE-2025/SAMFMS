import React, { useState } from 'react';
import { Search } from 'lucide-react';

const DriverSearch = ({ onSearch }) => {
  const [searchTerm, setSearchTerm] = useState('');

  const handleSearch = e => {
    e.preventDefault();
    onSearch(searchTerm);
  };

  return (
    <form onSubmit={handleSearch} className="w-full max-w-xs">
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
  );
};

export default DriverSearch;
