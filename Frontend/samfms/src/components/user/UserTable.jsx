import React, { useState, useEffect } from 'react';
import { Button } from '../ui/button';
import { Plus, Search, ChevronUp, ChevronDown, ChevronLeft, ChevronRight } from 'lucide-react';
import FadeIn from '../ui/FadeIn';

const UserTable = ({
  title,
  users,
  loading,
  showActions = true,
  showRole = false,
  emptyMessage = 'No users found',
  actions = [],
  search = '',
  setSearch,
  sort = { field: 'full_name', direction: 'asc' },
  onSortChange,
  onAddUser,
  showAddButton = true,
}) => {
  const [filteredUsers, setFilteredUsers] = useState(users);
  const [searchField, setSearchField] = useState(search);
  const [currentPage, setCurrentPage] = useState(1);
  const [usersPerPage] = useState(10); // Show 10 users per page

  useEffect(() => {
    setFilteredUsers(users);
    setCurrentPage(1); // Reset to first page when users change
  }, [users]);

  // Calculate pagination values
  const indexOfLastUser = currentPage * usersPerPage;
  const indexOfFirstUser = indexOfLastUser - usersPerPage;
  const currentUsers = filteredUsers.slice(indexOfFirstUser, indexOfLastUser);
  const totalPages = Math.ceil(filteredUsers.length / usersPerPage);

  if (loading && !users.length) {
    return (
      <div className="mb-8">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-semibold">{title}</h2>
          {showAddButton && onAddUser && (
            <Button
              onClick={onAddUser}
              size="sm"
              className="h-8 w-8 rounded-md p-0" /* Made square instead of rounded-full */
              title={`Add ${title.slice(0, -1)}`}
            >
              <Plus className="h-4 w-4" />
            </Button>
          )}
        </div>
        <div className="text-center py-8">Loading {title.toLowerCase()}...</div>
      </div>
    );
  }

  const getSortIcon = field => {
    if (sort.field !== field) return null;
    return sort.direction === 'asc' ? (
      <ChevronUp className="inline-block h-4 w-4 ml-1" />
    ) : (
      <ChevronDown className="inline-block h-4 w-4 ml-1" />
    );
  };

  const handleHeaderClick = field => {
    if (onSortChange) {
      onSortChange(field);
    }
  };

  const handleSearchChange = async e => {
    console.log('Changing search query:', e.target.value);
    const query = e.target.value;
    setSearchField(query);
    setCurrentPage(1); // Reset to first page when searching
    if (!query.trim()) {
      setFilteredUsers(users);
      return;
    }
    const lowerQuery = query.toLowerCase();
    setFilteredUsers(
      users.filter(
        user =>
          (user.full_name && user.full_name.toLowerCase().includes(lowerQuery)) ||
          (user.email && user.email.toLowerCase().includes(lowerQuery))
      )
    );
  };

  return (
    <FadeIn delay={0.2}>
      <div className="mb-8">
        {/* Search Bar and Square Plus Button */}
        <FadeIn delay={0.3}>
          <div className="mb-4 flex items-center gap-4">
            <h2 className="text-2xl font-semibold">{title}</h2>
            <div className="relative w-80">
              {' '}
              {/* Fixed width for shorter search bar */}
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
              <input
                type="text"
                placeholder={`Search ${title.toLowerCase()}...`}
                value={searchField}
                onChange={handleSearchChange}
                className="w-full pl-10 pr-4 py-2 border border-border rounded-md bg-background text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
              />
            </div>

            <button
              onClick={onAddUser}
              type="button"
              className="bg-green-600 hover:bg-green-700 text-white rounded-md p-2 flex items-center justify-center transition-colors flex-shrink-0 w-10 h-10" /* Made square with fixed dimensions */
              title={`Add ${title.slice(0, -1)}`}
            >
              <Plus className="h-5 w-5" />
            </button>
          </div>
        </FadeIn>

        <FadeIn delay={0.4}>
          <div className="bg-card rounded-lg border border-border overflow-hidden">
            <table className="w-full">
              <thead className="bg-muted/50">
                <tr>
                  <th
                    className={`px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider ${
                      onSortChange ? 'cursor-pointer hover:bg-muted/70' : ''
                    }`}
                    onClick={() => handleHeaderClick('full_name')}
                  >
                    Name {getSortIcon('full_name')}
                  </th>
                  <th
                    className={`px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider ${
                      onSortChange ? 'cursor-pointer hover:bg-muted/70' : ''
                    }`}
                    onClick={() => handleHeaderClick('email')}
                  >
                    Email {getSortIcon('email')}
                  </th>
                  {showRole && (
                    <th
                      className={`px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider ${
                        onSortChange ? 'cursor-pointer hover:bg-muted/70' : ''
                      }`}
                      onClick={() => handleHeaderClick('role')}
                    >
                      Role {getSortIcon('role')}
                    </th>
                  )}
                  {/* Removed actions column */}
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {filteredUsers.length === 0 ? (
                  <tr>
                    <td
                      colSpan={
                        (showRole ? 1 : 0) + 2 // Name, Email (removed Phone)
                      }
                      className="px-6 py-4 text-center text-muted-foreground"
                    >
                      {emptyMessage}
                    </td>
                  </tr>
                ) : (
                  currentUsers.map((user /* Use currentUsers for pagination */) => (
                    <tr key={user.id || user.email} className="hover:bg-muted/30">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-foreground">
                          {user.full_name || 'Unknown'}
                          {user.isCurrentUser && (
                            <span className="ml-2 text-xs text-blue-600 font-semibold">(you)</span>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-muted-foreground">{user.email}</div>
                      </td>
                      {/* Removed phone column */}
                      {showRole && (
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800 capitalize">
                            {user.role?.replace('_', ' ') || 'N/A'}
                          </span>
                        </td>
                      )}
                      {/* Removed actions cell */}
                    </tr>
                  ))
                )}
              </tbody>
            </table>

            {/* Pagination Controls */}
            {totalPages > 1 && (
              <div className="px-6 py-4 border-t border-border flex items-center justify-between">
                <div className="text-sm text-muted-foreground">
                  Showing {indexOfFirstUser + 1} to{' '}
                  {Math.min(indexOfLastUser, filteredUsers.length)} of {filteredUsers.length}{' '}
                  entries
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                    disabled={currentPage === 1}
                    variant="outline"
                    size="sm"
                    className="h-8 w-8 p-0"
                    title="Previous page"
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </Button>

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
                      <Button
                        key={pageNumber}
                        onClick={() => setCurrentPage(pageNumber)}
                        variant={currentPage === pageNumber ? 'default' : 'outline'}
                        size="sm"
                        className="h-8 w-8 p-0"
                        title={`Go to page ${pageNumber}`}
                      >
                        {pageNumber}
                      </Button>
                    );
                  })}

                  <Button
                    onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                    disabled={currentPage === totalPages}
                    variant="outline"
                    size="sm"
                    className="h-8 w-8 p-0"
                    title="Next page"
                  >
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            )}
          </div>
        </FadeIn>
      </div>
    </FadeIn>
  );
};

export default UserTable;
