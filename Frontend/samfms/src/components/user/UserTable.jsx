import React, { useState, useEffect } from 'react';
import { Plus, Search, ArrowUp, ArrowDown, ChevronLeft, ChevronRight } from 'lucide-react';
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
  const [usersPerPage, setUsersPerPage] = useState(5);

  useEffect(() => {
    setFilteredUsers(users);
    setCurrentPage(1);
  }, [users]);

  // Calculate pagination values
  const indexOfLastUser = currentPage * usersPerPage;
  const indexOfFirstUser = indexOfLastUser - usersPerPage;
  const currentUsers = filteredUsers.slice(indexOfFirstUser, indexOfLastUser);
  const totalPages = Math.ceil(filteredUsers.length / usersPerPage);

  if (loading && !users.length) {
    return (
      <FadeIn delay={0.2}>
        <div className="mb-8">
          <div className="flex flex-col md:flex-row justify-between items-center mb-6 gap-4">
            <h2 className="text-xl font-semibold">{title}</h2>
            {showAddButton && onAddUser && (
              <div className="flex items-center gap-4">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
                  <input
                    type="text"
                    placeholder={`Search ${title.toLowerCase()}...`}
                    disabled
                    className="pl-10 pr-4 py-2 border border-border rounded-md bg-background text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
                  />
                </div>
                <button
                  onClick={onAddUser}
                  type="button"
                  className="bg-green-600 text-white p-3 rounded-md hover:bg-green-700 transition-colors"
                  title={`Add ${title.slice(0, -1)}`}
                >
                  <Plus size={18} />
                </button>
              </div>
            )}
          </div>
          <div className="text-center py-8">Loading {title.toLowerCase()}...</div>
        </div>
      </FadeIn>
    );
  }

  const getSortIcon = field => {
    if (sort.field !== field) return null;
    return sort.direction === 'asc' ? (
      <ArrowUp className="inline ml-1" size={14} />
    ) : (
      <ArrowDown className="inline ml-1" size={14} />
    );
  };

  const handleHeaderClick = field => {
    if (onSortChange) {
      onSortChange(field);
    }
  };

  const handleSearchChange = async e => {
    const query = e.target.value;
    setSearchField(query);
    setCurrentPage(1);
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

  const goToNextPage = () => {
    setCurrentPage(prev => Math.min(prev + 1, totalPages));
  };

  const goToPrevPage = () => {
    setCurrentPage(prev => Math.max(prev - 1, 1));
  };

  const changeItemsPerPage = e => {
    setUsersPerPage(Number(e.target.value));
    setCurrentPage(1);
  };

  return (
    <FadeIn delay={0.2}>
      <div className="mb-8">
        {/* Header layout matching vehicles table */}
        <div className="flex flex-col md:flex-row justify-between items-center mb-6 gap-4">
          <h2 className="text-xl font-semibold">{title}</h2>
          <div className="flex items-center gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
              <input
                type="text"
                placeholder={`Search ${title.toLowerCase()}...`}
                value={searchField}
                onChange={handleSearchChange}
                className="pl-10 pr-4 py-2 border border-border rounded-md bg-background text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
              />
            </div>
            {showAddButton && onAddUser && (
              <button
                onClick={onAddUser}
                type="button"
                className="bg-green-600 text-white p-3 rounded-md hover:bg-green-700 transition-colors"
                title={`Add ${title.slice(0, -1)}`}
              >
                <Plus size={18} />
              </button>
            )}
          </div>
        </div>

        {/* Table exactly matching vehicles table */}
        <div className="bg-card rounded-lg shadow-md p-6 border border-border">
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="border-b border-border">
                  <th
                    className={`text-left py-3 px-4 ${
                      onSortChange ? 'cursor-pointer hover:bg-accent/10' : ''
                    }`}
                    onClick={() => handleHeaderClick('full_name')}
                  >
                    Name {getSortIcon('full_name')}
                  </th>
                  <th
                    className={`text-left py-3 px-4 ${
                      onSortChange ? 'cursor-pointer hover:bg-accent/10' : ''
                    }`}
                    onClick={() => handleHeaderClick('email')}
                  >
                    Email {getSortIcon('email')}
                  </th>
                  {showRole && (
                    <th
                      className={`text-left py-3 px-4 ${
                        onSortChange ? 'cursor-pointer hover:bg-accent/10' : ''
                      }`}
                      onClick={() => handleHeaderClick('role')}
                    >
                      Role {getSortIcon('role')}
                    </th>
                  )}
                  {showActions && actions.length > 0 && (
                    <th className="text-left py-3 px-4">Actions</th>
                  )}
                </tr>
              </thead>
              <tbody>
                {filteredUsers.length === 0 ? (
                  <tr>
                    <td
                      colSpan={2 + (showRole ? 1 : 0) + (showActions && actions.length > 0 ? 1 : 0)}
                      className="px-4 py-8 text-center text-muted-foreground"
                    >
                      {emptyMessage}
                    </td>
                  </tr>
                ) : (
                  currentUsers.map(user => (
                    <tr
                      key={user.id || user.email}
                      className="border-b border-border hover:bg-accent/10 cursor-pointer"
                    >
                      <td className="py-3 px-4">
                        <div className="text-sm font-medium text-foreground">
                          {user.full_name || 'Unknown'}
                          {user.isCurrentUser && (
                            <span className="ml-2 text-xs text-blue-600 font-semibold">(you)</span>
                          )}
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <div className="text-sm text-muted-foreground">{user.email}</div>
                      </td>
                      {showRole && (
                        <td className="py-3 px-4">
                          <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800 capitalize">
                            {user.role?.replace('_', ' ') || 'N/A'}
                          </span>
                        </td>
                      )}
                      {showActions && actions.length > 0 && (
                        <td className="py-3 px-4" onClick={e => e.stopPropagation()}>
                          <div className="flex space-x-2">
                            {actions.map((action, index) => (
                              <button
                                key={index}
                                className={action.className || 'text-primary hover:text-primary/80'}
                                title={action.title}
                                onClick={() => action.onClick(user)}
                              >
                                {action.icon}
                              </button>
                            ))}
                          </div>
                        </td>
                      )}
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination exactly matching vehicles table */}
          {totalPages > 1 && (
            <div className="mt-6 flex items-center justify-between">
              <div>
                <select
                  value={usersPerPage}
                  onChange={changeItemsPerPage}
                  className="border border-border rounded-md bg-background py-1 pl-2 pr-8"
                >
                  <option value="5">5 per page</option>
                  <option value="10">10 per page</option>
                  <option value="20">20 per page</option>
                  <option value="50">50 per page</option>
                </select>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">
                  Page {currentPage} of {totalPages}
                </span>
                <div className="flex gap-1">
                  <button
                    onClick={goToPrevPage}
                    disabled={currentPage === 1}
                    className={`p-1 rounded ${
                      currentPage === 1
                        ? 'text-muted-foreground cursor-not-allowed'
                        : 'hover:bg-accent'
                    }`}
                    title="Previous page"
                  >
                    <ChevronLeft size={18} />
                  </button>
                  <button
                    onClick={goToNextPage}
                    disabled={currentPage === totalPages}
                    className={`p-1 rounded ${
                      currentPage === totalPages
                        ? 'text-muted-foreground cursor-not-allowed'
                        : 'hover:bg-accent'
                    }`}
                    title="Next page"
                  >
                    <ChevronRight size={18} />
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </FadeIn>
  );
};

export default UserTable;
