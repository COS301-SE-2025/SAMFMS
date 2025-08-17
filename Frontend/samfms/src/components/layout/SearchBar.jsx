import React, { useState } from 'react';
import { Search, LogOut } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { logout } from '../../backend/API.js';

const SearchBar = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const navigate = useNavigate();

  const handleSearch = e => {
    e.preventDefault();
    // Implement search functionality here
    console.log('Searching for:', searchQuery);
    // You could navigate to search results page or filter content
  };

  // Handle logout
  const handleLogout = () => {
    logout();
    navigate('/logout');
  };

  return (
    <div className="px-3 pb-3">
      <form onSubmit={handleSearch} className="relative">
        <div className="relative">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            className="w-full rounded-md border border-input bg-background py-2 pl-9 pr-3 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
          />
        </div>

        {/* Logout button below search */}
        <button
          type="button"
          onClick={handleLogout}
          className="mt-3 flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm text-destructive hover:bg-destructive/10 transition-colors"
        >
          <LogOut size={16} />
          <span>Logout</span>
        </button>
      </form>
    </div>
  );
};

export default SearchBar;
