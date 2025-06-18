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
  createUserManually,
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

  // Manual user creation form state
  const [manualCreateForm, setManualCreateForm] = useState({
    full_name: '',
    email: '',
    role: 'driver',
    password: '',
    confirmPassword: '',
    phoneNo: '',
  });
  const [showManualCreateForm, setShowManualCreateForm] = useState(false);

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
  const handleManualCreateSubmit = async e => {
    e.preventDefault();
    setError('');
    setSuccess('');

    // Validation
    if (manualCreateForm.password !== manualCreateForm.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    try {
      setLoading(true); // Validate data before sending
      const userData = {
        full_name: manualCreateForm.full_name.trim(),
        email: manualCreateForm.email.trim(),
        role: manualCreateForm.role || 'driver',
        password: manualCreateForm.password,
        phoneNo: manualCreateForm.phoneNo ? manualCreateForm.phoneNo.trim() : undefined,
        details: {}, // Include empty details object
      };

      // Log for debugging
      console.log('Submitting user data:', userData);

      // Create user manually
      await createUserManually(userData);

      setSuccess(`User ${manualCreateForm.full_name} created successfully!`);

      // Reset form
      setManualCreateForm({
        full_name: '',
        email: '',
        role: 'driver',
        password: '',
        confirmPassword: '',
        phoneNo: '',
      });
      setShowManualCreateForm(false);

      // Refresh user list
      loadUsers();
    } catch (err) {
      setError(`Failed to create user: ${err.message}`);
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
      )}{' '}
      {/* User Actions Section */}
      <div className="mb-8">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-semibold">User Management Actions</h2>
          <div className="space-x-2">
            {/* Only admins can manually create users */}
            {hasRole(ROLES.ADMIN) && (
              <Button
                onClick={() => {
                  setShowManualCreateForm(!showManualCreateForm);
                  if (showInviteForm) setShowInviteForm(false);
                }}
                className="bg-green-600 hover:bg-green-700 text-white"
                disabled={loading}
              >
                {showManualCreateForm ? 'Cancel' : 'Manually Add User'}
              </Button>
            )}
            <Button
              onClick={() => {
                setShowInviteForm(!showInviteForm);
                if (showManualCreateForm) setShowManualCreateForm(false);
              }}
              className="bg-primary hover:bg-primary/90"
              disabled={loading}
            >
              {showInviteForm ? 'Cancel' : 'Invite User'}
            </Button>
          </div>
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

        {/* Manual User Creation Form */}
        {showManualCreateForm && (
          <div className="bg-card p-6 rounded-lg border border-border">
            <form onSubmit={handleManualCreateSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Full Name</label>
                  <input
                    type="text"
                    value={manualCreateForm.full_name}
                    onChange={e =>
                      setManualCreateForm({ ...manualCreateForm, full_name: e.target.value })
                    }
                    className="w-full p-2 border rounded-md"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Email</label>
                  <input
                    type="email"
                    value={manualCreateForm.email}
                    onChange={e =>
                      setManualCreateForm({ ...manualCreateForm, email: e.target.value })
                    }
                    className="w-full p-2 border rounded-md"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Password</label>
                  <input
                    type="password"
                    value={manualCreateForm.password}
                    onChange={e =>
                      setManualCreateForm({ ...manualCreateForm, password: e.target.value })
                    }
                    className="w-full p-2 border rounded-md"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Confirm Password</label>
                  <input
                    type="password"
                    value={manualCreateForm.confirmPassword}
                    onChange={e =>
                      setManualCreateForm({ ...manualCreateForm, confirmPassword: e.target.value })
                    }
                    className="w-full p-2 border rounded-md"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Role</label>
                  <select
                    value={manualCreateForm.role}
                    onChange={e =>
                      setManualCreateForm({ ...manualCreateForm, role: e.target.value })
                    }
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
                    value={manualCreateForm.phoneNo}
                    onChange={e =>
                      setManualCreateForm({ ...manualCreateForm, phoneNo: e.target.value })
                    }
                    className="w-full p-2 border rounded-md"
                  />
                </div>
              </div>
              <div className="flex justify-end space-x-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setShowManualCreateForm(false)}
                  disabled={loading}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={loading}>
                  {loading ? 'Creating...' : 'Create User'}
                </Button>
              </div>
            </form>
          </div>
        )}
      </div>{' '}
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
      )}{' '}
      {/* Invited Users Table */}
      {(hasRole(ROLES.ADMIN) || hasRole(ROLES.FLEET_MANAGER)) && invitedUsers.length > 0 && (
        <div className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">Pending Invitations</h2>
          <div className="bg-card rounded-lg border border-border overflow-hidden">
            <table className="w-full">
              <thead className="bg-muted/50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    Email
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    Role
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    Invited
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    Expires
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
                {invitedUsers.map(invitation => (
                  <tr key={invitation.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      {invitation.full_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-muted-foreground">
                      {invitation.email}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                        {invitation.role.replace('_', ' ').toUpperCase()}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-muted-foreground">
                      {new Date(invitation.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-muted-foreground">
                      {new Date(invitation.expires_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span
                        className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          invitation.is_expired
                            ? 'bg-red-100 text-red-800'
                            : 'bg-yellow-100 text-yellow-800'
                        }`}
                      >
                        {invitation.is_expired ? 'EXPIRED' : 'PENDING'}
                      </span>
                      {invitation.activation_attempts > 0 && (
                        <div className="text-xs text-muted-foreground mt-1">
                          {invitation.activation_attempts} attempts
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                      {!invitation.is_expired && invitation.can_resend && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleResendInvitation(invitation.email)}
                          disabled={loading}
                        >
                          Resend OTP
                        </Button>
                      )}
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => showRemoveConfirm(invitation.id, invitation.full_name)}
                        disabled={loading}
                      >
                        Cancel
                      </Button>
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
