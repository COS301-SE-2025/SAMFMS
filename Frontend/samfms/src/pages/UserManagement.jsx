import React, {useState, useEffect, useRef} from 'react';
import {Button} from '../components/ui/button.jsx';
import {useAuth, ROLES} from '../components/RBACUtils.jsx';
import {
  listUsers,
  updateUserPermissions,
  getRoles,
  isAuthenticated,
  sendInvitation,
  getPendingInvitations,
  resendInvitation,
  createUserManually,
  getUserInfo,
} from '../backend/API.js';
import {Navigate} from 'react-router-dom';
import UserTable from '../components/UserTable.jsx';
import InviteUserModal from '../components/InviteUserModal.jsx';
import ManualCreateUserModal from '../components/ManualCreateUserModal.jsx';
import {useNotification} from '../contexts/NotificationContext.jsx';

const UserManagement = () => {
  const {hasPermission, hasRole} = useAuth();
  const {showNotification} = useNotification();
  const [adminUsers, setAdminUsers] = useState([]);
  const [managerUsers, setManagerUsers] = useState([]);
  const [driverUsers, setDriverUsers] = useState([]);
  const [invitedUsers, setInvitedUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);

  // Search and sort states
  const [adminSearch, setAdminSearch] = useState('');
  const [managerSearch, setManagerSearch] = useState('');
  const [driverSearch, setDriverSearch] = useState('');
  const [adminSort, setAdminSort] = useState({field: 'full_name', direction: 'asc'});
  const [managerSort, setManagerSort] = useState({field: 'full_name', direction: 'asc'});
  const [driverSort, setDriverSort] = useState({field: 'full_name', direction: 'asc'});

  // Modal states
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [showManualCreateModal, setShowManualCreateModal] = useState(false);
  const [createUserRole, setCreateUserRole] = useState('driver'); // Track which role to create

  const hasMounted = useRef(false);
  const loadUsers = React.useCallback(async () => {
    try {
      setLoading(true);
      const usersData = await listUsers();
      const currentUserInfo = await getUserInfo();
      setCurrentUser(currentUserInfo);

      // Filter users by role and add current user indicator
      const admins = usersData
        .filter(user => user.role === ROLES.ADMIN)
        .map(user => ({
          ...user,
          isCurrentUser:
            user.id === currentUserInfo?.user_id || user.email === currentUserInfo?.email,
        }));
      const managers = usersData
        .filter(user => user.role === ROLES.FLEET_MANAGER)
        .map(user => ({
          ...user,
          isCurrentUser:
            user.id === currentUserInfo?.user_id || user.email === currentUserInfo?.email,
        }));
      const drivers = usersData
        .filter(user => user.role === ROLES.DRIVER)
        .map(user => ({
          ...user,
          isCurrentUser:
            user.id === currentUserInfo?.user_id || user.email === currentUserInfo?.email,
        }));

      setAdminUsers(admins);
      setManagerUsers(managers);
      setDriverUsers(drivers);
    } catch (err) {
      showNotification(`Failed to load users: ${err.message}`, 'error');
    } finally {
      setLoading(false);
    }
  }, [showNotification]);

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
      showNotification('You need to be logged in to access this page.', 'error');
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
  }, [loadUsers, loadInvitedUsers, showNotification]);

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
  } // Handler functions for modals
  const handleInviteSubmit = async formData => {
    try {
      setLoading(true);
      await sendInvitation(formData);
      showNotification(
        `Invitation sent to ${formData.email}! They will receive an OTP to complete registration.`,
        'success'
      );
      setShowInviteModal(false);
      // Refresh data
      loadUsers();
      loadInvitedUsers();
    } catch (err) {
      showNotification(`Failed to send invitation: ${err.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };
  const handleManualCreateSubmit = async formData => {
    try {
      setLoading(true);

      // Debug: Log the received form data
      console.log('Received form data:', formData);

      // Validate that we have the required fields
      if (!formData || !formData.full_name || !formData.email || !formData.password) {
        console.error('Missing required form data:', formData);
        showNotification(
          'Missing required form data. Please fill in all required fields.',
          'error'
        );
        return;
      }

      const userData = {
        full_name: formData.full_name.trim(),
        email: formData.email.trim(),
        role: formData.role || 'driver',
        password: formData.password,
        phoneNo: formData.phoneNo ? formData.phoneNo.trim() : undefined,
        details: {},
      };

      console.log('Sending user data:', userData);
      await createUserManually(userData);
      showNotification(`User ${formData.full_name} created successfully!`, 'success');
      setShowManualCreateModal(false);
      // Refresh user list
      loadUsers();
    } catch (err) {
      console.error('Error in handleManualCreateSubmit:', err);
      showNotification(`Failed to create user: ${err.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleResendInvitation = async email => {
    try {
      setLoading(true);
      await resendInvitation(email);
      showNotification(`Invitation resent to ${email}!`, 'success');
      loadInvitedUsers();
    } catch (err) {
      showNotification(`Failed to resend invitation: ${err.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };
  const handleRoleChange = async (userId, newRole) => {
    try {
      setLoading(true);
      await updateUserPermissions({
        user_id: userId,
        role: newRole,
      });
      showNotification('User role updated successfully!', 'success');
      loadUsers();
    } catch (err) {
      showNotification(`Failed to update user role: ${err.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveUser = async (userId, userName) => {
    const userConfirmed = window.confirm(
      `Are you sure you want to remove ${userName} from the system?`
    );

    if (!userConfirmed) return;

    try {
      setLoading(true);
      await updateUserPermissions({
        user_id: userId,
        role: 'inactive',
        is_active: false,
      });
      showNotification(`User has been removed from the system.`, 'success');
      loadUsers();
    } catch (err) {
      showNotification(`Failed to remove user: ${err.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  // Handle opening manual create modal with specific role
  const handleOpenCreateModal = role => {
    setCreateUserRole(role);
    setShowManualCreateModal(true);
  };

  // Search and sort utility functions
  const filterAndSortUsers = (users, searchTerm, sortConfig) => {
    let filtered = users;

    // Apply search filter
    if (searchTerm) {
      filtered = users.filter(
        user =>
          user.full_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
          user.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
          user.phoneNo?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Apply sort
    filtered.sort((a, b) => {
      const aValue = a[sortConfig.field] || '';
      const bValue = b[sortConfig.field] || '';

      if (sortConfig.direction === 'asc') {
        return aValue.toString().localeCompare(bValue.toString());
      } else {
        return bValue.toString().localeCompare(aValue.toString());
      }
    });

    return filtered;
  };

  const handleSort = (field, currentSort, setSortFunction) => {
    const newDirection =
      currentSort.field === field && currentSort.direction === 'asc' ? 'desc' : 'asc';
    setSortFunction({field, direction: newDirection});
  };

  // Get filtered and sorted users
  const filteredAdmins = filterAndSortUsers(adminUsers, adminSearch, adminSort);
  const filteredManagers = filterAndSortUsers(managerUsers, managerSearch, managerSort);
  const filteredDrivers = filterAndSortUsers(driverUsers, driverSearch, driverSort);

  // Handle role change with current user protection
  const canChangeRole = user => {
    return !user.isCurrentUser;
  };

  return (
    <div className="relative container mx-auto py-8">
      {/* Background pattern */}
      <div
        className="absolute inset-0 z-0 opacity-10 pointer-events-none"
        style={{
          backgroundImage: 'url("/logo/logo_icon_dark.svg")',
          backgroundSize: '200px',
          backgroundRepeat: 'repeat',
          filter: 'blur(1px)',
        }}
        aria-hidden="true"
      />

      <div className="relative overflow-hidden">

        <div className="relative z-10">

          <header className="mb-8">
            <h1 className="text-4xl font-bold">User Management</h1>
          </header>{' '}
          {/* Action Buttons */}
          <div className="mb-8">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-2xl font-semibold">User Management Actions</h2>
              <div className="space-x-2">
                <Button
                  onClick={() => setShowInviteModal(true)}
                  className="bg-primary hover:bg-primary/90"
                  disabled={loading}
                >
                  Invite User
                </Button>
              </div>
            </div>
          </div>{' '}
          {/* Admin Users Table */}
          {hasRole(ROLES.ADMIN) && (
            <UserTable
              title="Administrators"
              users={filteredAdmins}
              loading={loading && !adminUsers.length}
              emptyMessage="No administrators found"
              actions={[
                {
                  label: 'Remove Admin',
                  variant: 'destructive',
                  onClick: user => handleRemoveUser(user.id, user.full_name),
                  disabled: () => loading,
                },
              ]}
              search={adminSearch}
              setSearch={setAdminSearch}
              sort={adminSort}
              onSortChange={field => handleSort(field, adminSort, setAdminSort)}
              showAddButton={true}
              onAddUser={() => handleOpenCreateModal('admin')}
            />
          )}
          {/* Fleet Managers Table */}
          {hasRole(ROLES.ADMIN) && (
            <UserTable
              title="Fleet Managers"
              users={filteredManagers}
              loading={loading && !managerUsers.length}
              emptyMessage="No fleet managers found"
              actions={[
                {
                  label: 'Promote to Admin',
                  variant: 'outline',
                  onClick: user => handleRoleChange(user.id, 'admin'),
                  disabled: () => loading,
                  visible: user => canChangeRole(user),
                },
                {
                  label: 'Remove',
                  variant: 'destructive',
                  onClick: user => handleRemoveUser(user.id, user.full_name),
                  disabled: () => loading,
                },
              ]}
              search={managerSearch}
              setSearch={setManagerSearch}
              sort={managerSort}
              onSortChange={field => handleSort(field, managerSort, setManagerSort)}
              showAddButton={true}
              onAddUser={() => handleOpenCreateModal('fleet_manager')}
            />
          )}
          {/* Drivers Table */}
          <UserTable
            title="Drivers"
            users={filteredDrivers}
            loading={loading && !driverUsers.length}
            emptyMessage="No drivers found"
            showActions={hasRole(ROLES.ADMIN) || hasRole(ROLES.FLEET_MANAGER)}
            actions={[
              ...(hasRole(ROLES.ADMIN)
                ? [
                  {
                    label: 'Promote to Manager',
                    variant: 'outline',
                    onClick: user => handleRoleChange(user.id, 'fleet_manager'),
                    disabled: () => loading,
                    visible: user => canChangeRole(user),
                  },
                ]
                : []),
              {
                label: 'Remove',
                variant: 'destructive',
                onClick: user => handleRemoveUser(user.id, user.full_name),
                disabled: () => loading,
              },
            ]}
            search={driverSearch}
            setSearch={setDriverSearch}
            sort={driverSort}
            onSortChange={field => handleSort(field, driverSort, setDriverSort)}
            showAddButton={hasRole(ROLES.ADMIN) || hasRole(ROLES.FLEET_MANAGER)}
            onAddUser={() => handleOpenCreateModal('driver')}
          />
          {/* Pending Invitations Table */}
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
                            onClick={() => handleRemoveUser(invitation.id, invitation.full_name)}
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
          {/* Modals */}
          <InviteUserModal
            isOpen={showInviteModal}
            onClose={() => setShowInviteModal(false)}
            onSubmit={handleInviteSubmit}
            loading={loading}
          />{' '}
          <ManualCreateUserModal
            isOpen={showManualCreateModal}
            onClose={() => setShowManualCreateModal(false)}
            onSubmit={handleManualCreateSubmit}
            loading={loading}
            preselectedRole={createUserRole}
          />
        </div>
      </div>
    </div>
  );
};

export default UserManagement;
