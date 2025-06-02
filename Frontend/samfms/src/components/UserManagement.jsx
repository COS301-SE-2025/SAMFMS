import React, { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { useAuth, ROLES, PERMISSIONS } from './RBACUtils';
import { inviteUser, listUsers, updateUserPermissions, getRoles } from '../backend/API.js';

const UserManagement = () => {
  const { hasPermission, hasRole } = useAuth();
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Invite form state
  const [inviteForm, setInviteForm] = useState({
    full_name: '',
    email: '',
    role: 'driver',
    phoneNo: '',
  });
  const [showInviteForm, setShowInviteForm] = useState(false);

  // Only admin can access this component
  if (!hasPermission('users:manage') && !hasRole(ROLES.ADMIN)) {
    return (
      <div className="container mx-auto py-8">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          Access denied. Only administrators can manage users.
        </div>
      </div>
    );
  }

  useEffect(() => {
    loadUsers();
    loadRoles();
  }, []);

  const loadUsers = async () => {
    try {
      setLoading(true);
      const usersData = await listUsers();
      setUsers(usersData);
    } catch (err) {
      setError(`Failed to load users: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const loadRoles = async () => {
    try {
      const rolesData = await getRoles();
      setRoles(rolesData);
    } catch (err) {
      console.error('Failed to load roles:', err);
    }
  };

  const handleInviteSubmit = async e => {
    e.preventDefault();
    setError('');
    setSuccess('');

    try {
      setLoading(true);
      await inviteUser(inviteForm);
      setSuccess(`User ${inviteForm.full_name} has been invited successfully!`);
      setInviteForm({
        full_name: '',
        email: '',
        role: 'driver',
        phoneNo: '',
      });
      setShowInviteForm(false);
      loadUsers(); // Refresh user list
    } catch (err) {
      setError(`Failed to invite user: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleRoleChange = async (userId, newRole) => {
    setError('');
    setSuccess('');

    try {
      setLoading(true);
      await updateUserPermissions({
        user_id: userId,
        role: newRole,
      });
      setSuccess('User role updated successfully!');
      loadUsers(); // Refresh user list
    } catch (err) {
      setError(`Failed to update user role: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto py-8">
      <header className="mb-8">
        <h1 className="text-4xl font-bold">User Management</h1>
        <p className="text-muted-foreground">Manage system users and their permissions</p>
      </header>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {success && (
        <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">
          {success}
        </div>
      )}

      {/* Invite User Section */}
      <div className="mb-8">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-semibold">Invite New User</h2>
          <Button
            onClick={() => setShowInviteForm(!showInviteForm)}
            className="bg-primary hover:bg-primary/90"
          >
            {showInviteForm ? 'Cancel' : 'Invite User'}
          </Button>
        </div>

        {showInviteForm && (
          <div className="bg-card p-6 rounded-lg border border-border">
            <form onSubmit={handleInviteSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Full Name</label>
                  <input
                    type="text"
                    value={inviteForm.full_name}
                    onChange={e => setInviteForm({ ...inviteForm, full_name: e.target.value })}
                    className="w-full p-2 border rounded-md"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Email</label>
                  <input
                    type="email"
                    value={inviteForm.email}
                    onChange={e => setInviteForm({ ...inviteForm, email: e.target.value })}
                    className="w-full p-2 border rounded-md"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Role</label>
                  <select
                    value={inviteForm.role}
                    onChange={e => setInviteForm({ ...inviteForm, role: e.target.value })}
                    className="w-full p-2 border rounded-md"
                  >
                    {hasRole(ROLES.ADMIN) && <option value="fleet_manager">Fleet Manager</option>}
                    <option value="driver">Driver</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Phone Number (Optional)</label>
                  <input
                    type="tel"
                    value={inviteForm.phoneNo}
                    onChange={e => setInviteForm({ ...inviteForm, phoneNo: e.target.value })}
                    className="w-full p-2 border rounded-md"
                  />
                </div>
              </div>
              <div className="flex justify-end space-x-2">
                <Button type="button" variant="outline" onClick={() => setShowInviteForm(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={loading}>
                  {loading ? 'Inviting...' : 'Send Invitation'}
                </Button>
              </div>
            </form>
          </div>
        )}
      </div>

      {/* Users List */}
      <div>
        <h2 className="text-2xl font-semibold mb-4">Current Users</h2>
        {loading && !users.length ? (
          <div className="text-center py-8">Loading users...</div>
        ) : (
          <div className="bg-card rounded-lg border border-border overflow-hidden">
            <table className="w-full">
              <thead className="bg-muted/50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    User
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    Role
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {users.map(user => (
                  <tr key={user.id}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium">{user.full_name || 'Unknown'}</div>
                        <div className="text-sm text-muted-foreground">{user.email}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {hasRole(ROLES.ADMIN) && user.role !== 'admin' ? (
                        <select
                          value={user.role}
                          onChange={e => handleRoleChange(user.id, e.target.value)}
                          className="text-sm border rounded px-2 py-1"
                          disabled={loading}
                        >
                          <option value="fleet_manager">Fleet Manager</option>
                          <option value="driver">Driver</option>
                        </select>
                      ) : (
                        <span className="text-sm capitalize">{user.role.replace('_', ' ')}</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {user.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {user.role !== 'admin' && (
                        <div className="space-x-2">
                          <Button variant="outline" size="sm">
                            Edit Permissions
                          </Button>
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default UserManagement;
