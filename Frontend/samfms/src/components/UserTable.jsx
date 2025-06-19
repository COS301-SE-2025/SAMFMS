import React from 'react';
import { Button } from './ui/button';
import { Plus, Search, ChevronUp, ChevronDown } from 'lucide-react';

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
  showAddButton = false,
}) => {
  if (loading && !users.length) {
    return (
      <div className="mb-8">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-semibold">{title}</h2>
          {showAddButton && onAddUser && (
            <Button
              onClick={onAddUser}
              size="sm"
              className="h-8 w-8 rounded-full p-0"
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

  return (
    <div className="mb-8">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-semibold">{title}</h2>
        {showAddButton && onAddUser && (
          <Button
            onClick={onAddUser}
            size="sm"
            className="h-8 w-8 rounded-full p-0"
            title={`Add ${title.slice(0, -1)}`}
          >
            <Plus className="h-4 w-4" />
          </Button>
        )}
      </div>

      {/* Search Bar */}
      {setSearch && (
        <div className="mb-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
            <input
              type="text"
              placeholder={`Search ${title.toLowerCase()}...`}
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-border rounded-md bg-background text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
            />
          </div>
        </div>
      )}

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
              <th
                className={`px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider ${
                  onSortChange ? 'cursor-pointer hover:bg-muted/70' : ''
                }`}
                onClick={() => handleHeaderClick('phoneNo')}
              >
                Phone {getSortIcon('phoneNo')}
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
              {showActions && (
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Actions
                </th>
              )}
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {users.length === 0 ? (
              <tr>
                <td
                  colSpan={showActions && showRole ? '5' : showActions || showRole ? '4' : '3'}
                  className="px-6 py-4 text-center text-muted-foreground"
                >
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              users.map(user => (
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
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-muted-foreground">
                      {user.phoneNo || user.phone || 'N/A'}
                    </div>
                  </td>
                  {showRole && (
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800 capitalize">
                        {user.role?.replace('_', ' ') || 'N/A'}
                      </span>
                    </td>
                  )}
                  {showActions && (
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <div className="flex space-x-2">
                        {actions.map((action, index) => {
                          // Check if action should be visible for this user
                          const isVisible = action.visible ? action.visible(user) : true;
                          if (!isVisible) return null;

                          return (
                            <Button
                              key={index}
                              variant={action.variant || 'outline'}
                              size="sm"
                              onClick={() => action.onClick(user)}
                              disabled={action.disabled?.(user)}
                            >
                              {action.label}
                            </Button>
                          );
                        })}
                      </div>
                    </td>
                  )}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default UserTable;
