import React, { useState, useEffect, useRef } from 'react';
import { Button } from './ui/button';
import { useAuth, ROLES } from './RBACUtils';
import {
  listUsers,
  updateUserPermissions,
  getRoles,
  isAuthenticated,
  sendInvitation,
  getPendingInvitations,
  resendInvitation,
} from '../backend/API.js';
import { Navigate } from 'react-router-dom';

const UserManagement = () => {
  const { hasPermission, hasRole } = useAuth();
  const [adminUsers, setAdminUsers] = useState([]);
  const [managerUsers, setManagerUsers] = useState([]);
  const [invitedUsers, setInvitedUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Invite form state - updated for new invitation flow
  const [inviteForm, setInviteForm] = useState({
    full_name: '',
    email: '',
    role: 'driver',
    phoneNo: '',
  });
  const [showInviteForm, setShowInviteForm] = useState(false);

  const hasMounted = useRef(false);

  const loadUsers = React.useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      const usersData = await listUsers();

      // Filter users by role
      const admins = usersData.filter(user => user.role === ROLES.ADMIN);
      const managers = usersData.filter(user => user.role === ROLES.FLEET_MANAGER);

      setAdminUsers(admins);
      setManagerUsers(managers);
    } catch (err) {
      setError(`Failed to load users: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }, []); // No dependencies needed - listUsers is stable from API

  const loadInvitedUsers = React.useCallback(async () => {
    try {
      const invitationsData = await getPendingInvitations();
      setInvitedUsers(invitationsData.invitations || []);
    } catch (err) {
      console.error('Failed to load invited users:', err);
      // Don't set error for invited users - it's optional data
    }
  }, []);

  useEffect(() => {
    // Check authentication status first
    if (!isAuthenticated()) {
      setError('You need to be logged in to access this page.');
      return;
    }

    // Only run this effect once on mount
    if (hasMounted.current) {
      return;
    }
    hasMounted.current = true;

    // Load data
    loadUsers();
    loadInvitedUsers();

    // Load roles cache
    const fetchRoles = async () => {
      try {
        await getRoles(); // Just ensure roles are cached
      } catch (err) {
        console.error('Failed to load roles:', err);
      }
    };
    fetchRoles();
  }, [loadUsers, loadInvitedUsers]); // Depend on both loadUsers and loadInvitedUsers

  // Fleet managers should be redirected to the drivers page
  if (hasRole(ROLES.FLEET_MANAGER)) {
    return <Navigate to="/drivers" />;
  }

  // Only admin can access this component
  if (!hasPermission('users:manage') && !hasRole(ROLES.ADMIN)) {
    return (
      <div className="container mx-auto py-8">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          Access denied. You don't have permission to access this page.
        </div>
      </div>
    );
  }
  const handleInviteSubmit = async e => {
    e.preventDefault();
    setError('');
    setSuccess('');

    try {
      setLoading(true);

      // Use new invitation flow
      await sendInvitation(inviteForm);
      setSuccess(
        `Invitation sent to ${inviteForm.email}! They will receive an OTP to complete registration.`
      );

      setInviteForm({
        full_name: '',
        email: '',
        role: 'driver',
        phoneNo: '',
      });
      setShowInviteForm(false);
      // Refresh both active users and invited users
      loadUsers();
      loadInvitedUsers();
    } catch (err) {
      setError(`Failed to send invitation: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleResendInvitation = async email => {
    setError('');
    setSuccess('');

    try {
      setLoading(true);
      await resendInvitation(email);
      setSuccess(`Invitation resent to ${email}!`);
      loadInvitedUsers(); // Refresh invited users list
    } catch (err) {
      setError(`Failed to resend invitation: ${err.message}`);
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

  const showRemoveConfirm = (userId, userName) => {
    // Using a simpler approach for confirmation
    const userConfirmed = window.confirm(
      `Are you sure you want to remove ${userName} from the system?`
    );

    if (userConfirmed) {
      handleRemoveUser(userId);
    }
  };

  const handleRemoveUser = async userId => {
    setError('');
    setSuccess('');

    try {
      setLoading(true);
      // Set the user's status to inactive
      await updateUserPermissions({
        user_id: userId,
        role: 'inactive', // This will be handled server-side to deactivate the account
        is_active: false,
      });
      setSuccess(`User has been removed from the system.`);
      loadUsers(); // Refresh user list
    } catch (err) {
      setError(`Failed to remove user: ${err.message}`);
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
            disabled={loading}
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
                    {hasRole(ROLES.ADMIN) && <option value="admin">Administrator</option>}
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
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setShowInviteForm(false)}
                  disabled={loading}
                >
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
      {/* Admin Users Table - Only visible to Admins */}
      {hasRole(ROLES.ADMIN) && (
        <div className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">Administrators</h2>
          {loading && !adminUsers.length ? (
            <div className="text-center py-8">Loading administrators...</div>
          ) : (
            <div className="bg-card rounded-lg border border-border overflow-hidden">
              <table className="w-full">
                <thead className="bg-muted/50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                      Admin User
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                      Email
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
                  {adminUsers.length === 0 ? (
                    <tr>
                      <td colSpan="4" className="px-6 py-4 text-center">
                        No administrators found
                      </td>
                    </tr>
                  ) : (
                    adminUsers.map(user => (
                      <tr key={user.id}>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium">{user.full_name || 'Unknown'}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-muted-foreground">{user.email}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span
                            className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                              user.is_active
                                ? 'bg-green-100 text-green-800'
                                : 'bg-red-100 text-red-800'
                            }`}
                          >
                            {user.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <div className="space-x-2">
                            {' '}
                            <Button
                              variant="destructive"
                              size="sm"
                              onClick={() => showRemoveConfirm(user.id, user.full_name)}
                              disabled={loading}
                            >
                              Remove Admin
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
      {/* Fleet Managers Table - Visible to Admins only */}
      {hasRole(ROLES.ADMIN) && (
        <div className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">Fleet Managers</h2>
          {loading && !managerUsers.length ? (
            <div className="text-center py-8">Loading fleet managers...</div>
          ) : (
            <div className="bg-card rounded-lg border border-border overflow-hidden">
              <table className="w-full">
                <thead className="bg-muted/50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                      Manager
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                      Email
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
                  {managerUsers.length === 0 ? (
                    <tr>
                      <td colSpan="4" className="px-6 py-4 text-center">
                        No fleet managers found
                      </td>
                    </tr>
                  ) : (
                    managerUsers.map(user => (
                      <tr key={user.id}>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium">{user.full_name || 'Unknown'}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-muted-foreground">{user.email}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span
                            className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                              user.is_active
                                ? 'bg-green-100 text-green-800'
                                : 'bg-red-100 text-red-800'
                            }`}
                          >
                            {user.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <div className="space-x-2">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleRoleChange(user.id, 'admin')}
                              disabled={loading}
                            >
                              Promote to Admin
                            </Button>
                            <Button
                              variant="destructive"
                              size="sm"
                              disabled={loading}
                              onClick={() => showRemoveConfirm(user.id, user.full_name)}
                            >
                              Remove
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
      {/* Invited Users Table - Visible to Admins only */}
      {hasRole(ROLES.ADMIN) && (
        <div className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">Invited Users</h2>
          {loading && !invitedUsers.length ? (
            <div className="text-center py-8">Loading invited users...</div>
          ) : (
            <div className="bg-card rounded-lg border border-border overflow-hidden">
              <table className="w-full">
                <thead className="bg-muted/50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                      User
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                      Email
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
                  {invitedUsers.length === 0 ? (
                    <tr>
                      <td colSpan="5" className="px-6 py-4 text-center">
                        No invited users found
                      </td>
                    </tr>
                  ) : (
                    invitedUsers.map(user => (
                      <tr key={user.id}>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium">{user.full_name || 'Unknown'}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-muted-foreground">{user.email}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm">{user.role}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span
                            className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                              user.is_active
                                ? 'bg-green-100 text-green-800'
                                : 'bg-red-100 text-red-800'
                            }`}
                          >
                            {user.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <div className="space-x-2">
                            <Button
                              variant="destructive"
                              size="sm"
                              onClick={() => showRemoveConfirm(user.id, user.full_name)}
                              disabled={loading}
                            >
                              Remove Invitation
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={async () => {
                                setLoading(true);
                                try {
                                  await resendInvitation(user.id);
                                  setSuccess(`Invitation resent to ${user.email}`);
                                  loadInvitedUsers(); // Refresh invited users list
                                } catch (err) {
                                  setError(`Failed to resend invitation: ${err.message}`);
                                } finally {
                                  setLoading(false);
                                }
                              }}
                              disabled={loading}
                            >
                              Resend Invitation
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Invited Users Table */}
      {(hasRole(ROLES.ADMIN) || hasRole(ROLES.FLEET_MANAGER)) && invitedUsers.length > 0 && (
        <div className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">Pending Invitations</h2>
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Email
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Role
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Invited
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Expires
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {invitedUsers.map(invitation => (
                  <tr key={invitation.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {invitation.full_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {invitation.email}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                        {invitation.role.replace('_', ' ').toUpperCase()}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(invitation.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(invitation.expires_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <span
                        className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          invitation.is_expired
                            ? 'bg-red-100 text-red-800'
                            : 'bg-yellow-100 text-yellow-800'
                        }`}
                      >
                        {invitation.is_expired ? 'EXPIRED' : 'PENDING'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      {!invitation.is_expired && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleResendInvitation(invitation.email)}
                          disabled={loading}
                        >
                          Resend OTP
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserManagement;
