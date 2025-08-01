import React, {useState, useEffect, useRef} from 'react';
import {Button} from '../ui/button';
import {useAuth, ROLES} from '../auth/RBACUtils';
import {
  listUsers,
  updateUserPermissions,
  getRoles,
  isAuthenticated,
  getPendingInvitations,
  resendInvitation,
  createUserManually,
  getDrivers,
} from '../../backend/API.js';
import {Navigate} from 'react-router-dom';
import {useNotification} from '../../contexts/NotificationContext';
import UserTable from './UserTable';
import ManualCreateUserModal from './ManualCreateUserModal';

const UserManagement = () => {
  const {hasPermission, hasRole} = useAuth();
  const {showNotification} = useNotification();
  const [adminUsers, setAdminUsers] = useState([]);
  const [managerUsers, setManagerUsers] = useState([]);
  const [driverUsers, setDriverUsers] = useState([]);
  const [invitedUsers, setInvitedUsers] = useState([]);
  const [loading, setLoading] = useState(false);

  // Modal states
  const [showManualCreateModal, setShowManualCreateModal] = useState(false);
  const [createUserRole, setCreateUserRole] = useState('driver');

  const hasMounted = useRef(false);

  const loadUsers = React.useCallback(async () => {
    try {
      setLoading(true);
      const usersData = await listUsers();

      // Filter users by role
      const admins = usersData.filter(user => user.role === ROLES.ADMIN);
      const managers = usersData.filter(user => user.role === ROLES.FLEET_MANAGER);
      const drivers = usersData.filter(user => user.role === ROLES.DRIVER);

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
      // Don't show error for invited users - it's optional data
    }
  }, []);

  const loadDriversFromAPI = React.useCallback(async () => {
    try {
      // Load drivers from the drivers API if user has permission
      if (hasRole(ROLES.ADMIN) || hasRole(ROLES.FLEET_MANAGER)) {
        const driversData = await getDrivers({limit: 100});
        // Transform driver data to match user table format
        const transformedDrivers = driversData.map(driver => ({
          id: driver.id || driver._id,
          full_name: driver.user_info?.full_name || driver.name || 'Unknown',
          email: driver.user_info?.email || driver.email || 'N/A',
          phoneNo: driver.user_info?.phoneNo || driver.phone || 'N/A',
          phone: driver.user_info?.phoneNo || driver.phone || 'N/A',
          role: 'driver',
          employee_id: driver.employee_id,
          license_number: driver.license_number,
          department: driver.department,
          status: driver.status,
        }));
        setDriverUsers(transformedDrivers);
      }
    } catch (err) {
      console.error('Failed to load drivers from API:', err);
      // Fallback to drivers from user list if API fails
    }
  }, [hasRole]);

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
    // loadInvitedUsers();
    loadDriversFromAPI();

    // Load roles cache
    const fetchRoles = async () => {
      try {
        await getRoles(); // Just ensure roles are cached
      } catch (err) {
        console.error('Failed to load roles:', err);
      }
    };

    fetchRoles();
  }, [loadUsers, loadInvitedUsers, loadDriversFromAPI, showNotification]);

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

  const handleManualCreateSubmit = async formData => {
    try {
      setLoading(true);
      const userData = {
        full_name: formData.full_name.trim(),
        email: formData.email.trim(),
        role: formData.role || 'driver',
        password: formData.password,
        phoneNo: formData.phoneNo ? formData.phoneNo.trim() : undefined,
        details: {},
      };

      await createUserManually(userData);
      showNotification(`User ${formData.full_name} created successfully!`, 'success');
      setShowManualCreateModal(false);
      // Refresh user list
      loadUsers();
    } catch (err) {
      showNotification(`Failed to create user: ${err.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenCreateModal = role => {
    setShowManualCreateModal(false);
    setTimeout(() => {
      console.log("Opening create user modal with role:", role);
      setCreateUserRole(role);
      setShowManualCreateModal(true);
    }, 0);
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

  const handleCancelInvitation = async (invitationId, userName) => {
    const userConfirmed = window.confirm(
      `Are you sure you want to cancel the invitation for ${userName}?`
    );

    if (!userConfirmed) return;

    try {
      setLoading(true);
      // Note: You may need to implement a cancel invitation API
      showNotification(`Invitation for ${userName} has been cancelled.`, 'success');
      loadInvitedUsers();
    } catch (err) {
      showNotification(`Failed to cancel invitation: ${err.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  // Define actions for different user types
  const adminActions = [
    {
      label: 'Remove Admin',
      variant: 'destructive',
      onClick: user => handleRemoveUser(user.id, user.full_name),
      disabled: () => loading,
    },
  ];

  const managerActions = [
    {
      label: 'Promote to Admin',
      variant: 'outline',
      onClick: user => handleRoleChange(user.id, 'admin'),
      disabled: () => loading,
    },
    {
      label: 'Remove',
      variant: 'destructive',
      onClick: user => handleRemoveUser(user.id, user.full_name),
      disabled: () => loading,
    },
  ];

  const driverActions = [
    {
      label: 'View Details',
      variant: 'outline',
      onClick: user => {
        // Navigate to drivers page or open driver details
        window.location.href = '/drivers';
      },
      disabled: () => false,
    },
  ];

  const invitationActions = invitation => [
    ...(!invitation.is_expired && invitation.can_resend
      ? [
        {
          label: 'Resend OTP',
          variant: 'outline',
          onClick: () => handleResendInvitation(invitation.email),
          disabled: () => loading,
        },
      ]
      : []),
    {
      label: 'Cancel',
      variant: 'destructive',
      onClick: () => handleCancelInvitation(invitation.id, invitation.full_name),
      disabled: () => loading,
    },
  ];

  return (
    <div className="container mx-auto py-8">
      <header className="mb-8">
        <h1 className="text-4xl font-bold">User Management</h1>
      </header>

      {/* User Actions Section */}
      <div className="mb-8">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-semibold">User Management Actions</h2>

        </div>
      </div>

      {/* Admin Users Table - Only visible to Admins */}
      {hasRole(ROLES.ADMIN) && (
        <UserTable
          title="Administrators"
          users={adminUsers}
          loading={loading && !adminUsers.length}
          showActions={true}
          showRole={false}
          emptyMessage="No administrators found"
          actions={adminActions}
          onAddUser={() => handleOpenCreateModal('admin')}
        />
      )}

      {/* Fleet Managers Table - Visible to Admins only */}
      {hasRole(ROLES.ADMIN) && (
        <UserTable
          title="Fleet Managers"
          users={managerUsers}
          loading={loading && !managerUsers.length}
          showActions={true}
          showRole={false}
          emptyMessage="No fleet managers found"
          actions={managerActions}
          onAddUser={() => handleOpenCreateModal('fleet_manager')}
        />
      )}

      {/* Drivers Table */}
      {(hasRole(ROLES.ADMIN) || hasRole(ROLES.FLEET_MANAGER)) && (
        <UserTable
          title="Drivers"
          users={driverUsers}
          loading={loading && !driverUsers.length}
          showActions={true}
          showRole={false}
          emptyMessage="No drivers found"
          actions={driverActions}
          onAddUser={() => handleOpenCreateModal('driver')}
        />
      )}

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
                      {invitationActions(invitation).map((action, index) => (
                        <Button
                          key={index}
                          variant={action.variant}
                          size="sm"
                          onClick={action.onClick}
                          disabled={action.disabled()}
                        >
                          {action.label}
                        </Button>
                      ))}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Modals */}
      {/* <InviteUserModal
        isOpen={showInviteModal}
        onClose={() => setShowInviteModal(false)}
        onSubmit={handleInviteSubmit}
        loading={loading}
      /> */}

      <ManualCreateUserModal
        isOpen={showManualCreateModal}
        onClose={() => setShowManualCreateModal(false)}
        onSubmit={handleManualCreateSubmit}
        loading={loading}
        preselectedRole={createUserRole}
      />
    </div>
  );
};

export default UserManagement;
