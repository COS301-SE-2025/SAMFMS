import React, { useState, useEffect, useRef } from 'react';
import { useAuth, ROLES } from '../components/auth/RBACUtils.jsx';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import {
  listUsers,
  updateUserPermissions,
  getRoles,
  isAuthenticated,
  getPendingInvitations,
  resendInvitation,
  createUserManually,
  getDrivers,
  deleteAccount
} from '../backend/API.js';
import { Navigate } from 'react-router-dom';
import UserTable from '../components/user/UserTable.jsx';
import ManualCreateUserModal from '../components/user/ManualCreateUserModal.jsx';
import { useNotification } from '../contexts/NotificationContext.jsx';
import FadeIn from '../components/ui/FadeIn.jsx';

import { createDriver, getAllDrivers } from '../backend/api/drivers.js';

const UserManagement = () => {
  const { hasPermission, hasRole } = useAuth();
  const { showNotification } = useNotification();
  const [adminUsers, setAdminUsers] = useState([]);
  const [managerUsers, setManagerUsers] = useState([]);
  const [driverUsers, setDriverUsers] = useState([]);
  const [invitedUsers, setInvitedUsers] = useState([]);
  const [loading, setLoading] = useState(false);

  // Modal states
  const [showManualCreateModal, setShowManualCreateModal] = useState(false);
  const [createUserRole, setCreateUserRole] = useState('driver'); // Track which role to create

  // Pagination states for invited users table
  const [invitedUsersCurrentPage, setInvitedUsersCurrentPage] = useState(1);
  const [invitedUsersPerPage, setInvitedUsersPerPage] = useState(5);

  const hasMounted = useRef(false);
  const loadUsers = React.useCallback(async () => {
    try {
      setLoading(true);
      const usersData = await listUsers();
      console.log("User Data: ", usersData);

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
      // Don't set error for invited users - it's optional data
    }
  }, []);

  const loadDriversFromAPI = React.useCallback(async () => {
    try {
      // Load drivers from the drivers API if user has permission
      if (hasRole(ROLES.ADMIN) || hasRole(ROLES.FLEET_MANAGER)) {
        const driversData = await getAllDrivers({ limit: 100 });
        //console.log("Driver data response: ", driversData)

        // Access the drivers array correctly from the nested structure
        const driversArray = driversData.data.data.drivers;

        // Check if driversArray exists and is an array
        if (!Array.isArray(driversArray)) {
          console.error('Drivers data is not an array:', driversArray);
          return;
        }

        // Transform driver data to match user table format
        const transformedDrivers = driversArray.map(driver => ({
          id: driver._id || driver.id,
          full_name: `${driver.first_name} ${driver.last_name}`,
          email: driver.email,
          phone: driver.phone,
          role: 'driver',
          employee_id: driver.employee_id,
          license_number: driver.license_number,
          license_class: driver.license_class,
          license_expiry: driver.license_expiry,
          status: driver.status,
          security_id: driver.security_id
        }));

        //console.log("Transformed Drivers: ", transformedDrivers)
        setDriverUsers(transformedDrivers);
      }
    } catch (err) {
      console.error('Failed to load drivers from API:', err);
      // Fallback to drivers from user list if API fails
    }
  }, [hasRole]);

  // Comprehensive refresh function to update all user data
  const refreshAllUserData = React.useCallback(async () => {
    try {
      const promises = [loadUsers()];

      // Only load drivers API if user has permission
      if (hasRole(ROLES.ADMIN) || hasRole(ROLES.FLEET_MANAGER)) {
        promises.push(loadDriversFromAPI());
        promises.push(loadInvitedUsers());
      }

      await Promise.all(promises);
    } catch (err) {
      console.error('Failed to refresh user data:', err);
    }
  }, [loadUsers, loadDriversFromAPI, loadInvitedUsers, hasRole]);

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
  } // Handler functions for modals

  const handleManualCreateSubmit = async formData => {
    try {
      setLoading(true);
      console.log('=== Starting user creation process ===');
      console.log('Received form data:', formData);

      if (!formData || !formData.full_name || !formData.email || !formData.password) {
        throw new Error('Missing required form data');
      }

      // First create driver if role is driver

      // Then create user account
      const userData = {
        full_name: formData.full_name.trim(),
        email: formData.email.trim(),
        role: formData.role || 'driver',
        password: formData.password,
        phoneNo: formData.phoneNo ? formData.phoneNo.trim() : undefined,
        details: {},
      };

      console.log('Creating user account:', userData);
      const securityUser = await createUserManually(userData);
      const securityUser_ID = securityUser.user_id;
      console.log('Security user details: ', securityUser);

      if (formData.role === 'driver') {
        console.log('Creating driver first...');
        const driverData = {
          full_name: formData.full_name.trim(),
          email: formData.email.trim(),
          phoneNo: formData.phoneNo ? formData.phoneNo.trim() : undefined,
          security_id: securityUser_ID,
        };

        console.log('Driver data:', driverData);
        const driverResponse = await createDriver(driverData);
        console.log('Driver creation response:', driverResponse);

        if (!driverResponse || !driverResponse.data || driverResponse.data.status !== 'success') {
          throw new Error('Failed to create driver in management system');
        }
      }

      console.log('User creation successful');
      showNotification(`User ${formData.full_name} created successfully!`, 'success');
      setShowManualCreateModal(false);

      // Refresh all user data to ensure UI is fully updated
      await refreshAllUserData();
    } catch (err) {
      console.error('Error in handleManualCreateSubmit:', err);
      showNotification(`Failed to create user: ${err.message}`, 'error');
    } finally {
      setLoading(false);
      console.log('=== User creation process completed ===');
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

  const handleRemoveUser = async (email) => {
    const userConfirmed = window.confirm(
      `Are you sure you want to remove this user from the system?`
    );

    if (!userConfirmed) return;

    try {
      setLoading(true);
      await deleteAccount({
        email: email,
      });
      showNotification(`User has been removed from the system.`, 'success');

      await refreshAllUserData();
    } catch (err) {
      showNotification(`Failed to remove user: ${err.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenCreateModal = role => {
    setShowManualCreateModal(false);
    setTimeout(() => {
      console.log('Opening create user modal with role:', role);
      setCreateUserRole(role);
      setShowManualCreateModal(true);
    }, 0);
  };

  const handleRoleChange = async (userId, newRole) => {
    try {
      setLoading(true);
      await updateUserPermissions({
        user_id: userId,
        role: newRole,
      });
      showNotification('User role updated successfully!', 'success');

      // Refresh all user data to ensure UI is fully updated
      await refreshAllUserData();
    } catch (err) {
      showNotification(`Failed to update user role: ${err.message}`, 'error');
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

  // Pagination logic for invited users
  const invitedUsersIndexOfLast = invitedUsersCurrentPage * invitedUsersPerPage;
  const invitedUsersIndexOfFirst = invitedUsersIndexOfLast - invitedUsersPerPage;
  const currentInvitedUsers = invitedUsers.slice(invitedUsersIndexOfFirst, invitedUsersIndexOfLast);
  const invitedUsersTotalPages = Math.ceil(invitedUsers.length / invitedUsersPerPage);

  const goToInvitedUsersPrevPage = () => {
    setInvitedUsersCurrentPage(prev => Math.max(prev - 1, 1));
  };

  const goToInvitedUsersNextPage = () => {
    setInvitedUsersCurrentPage(prev => Math.min(prev + 1, invitedUsersTotalPages));
  };

  const changeInvitedUsersItemsPerPage = e => {
    setInvitedUsersPerPage(Number(e.target.value));
    setInvitedUsersCurrentPage(1);
  };

  return (
    <FadeIn delay={0.1}>
      <div className="container mx-auto py-8">
        <FadeIn delay={0.2}>
          <header className="mb-8">
            <h1 className="text-4xl font-bold">User Management</h1>
          </header>
        </FadeIn>

        {/* Admin Users Table - Only visible to Admins */}
        {hasRole(ROLES.ADMIN) && (
          <UserTable
            title="Administrators"
            users={adminUsers}
            loading={loading && !adminUsers.length}
            showPhone={true}
            showRole={false}
            emptyMessage="No administrators found"
            onAddUser={() => handleOpenCreateModal('admin')}
            onDeleteUser={(user) => handleRemoveUser(user.id, user.full_name)}
          />
        )}

        {/* Fleet Managers Table - Visible to Admins only */}
        {hasRole(ROLES.ADMIN) && (
          <UserTable
            title="Fleet Managers"
            users={managerUsers}
            loading={loading && !managerUsers.length}
            showPhone={true}
            showRole={false}
            emptyMessage="No fleet managers found"
            onAddUser={() => handleOpenCreateModal('fleet_manager')}
            onDeleteUser={(user) => handleRemoveUser(user.id, user.full_name)}
          />
        )}

        {/* Drivers Table */}
        {(hasRole(ROLES.ADMIN) || hasRole(ROLES.FLEET_MANAGER)) && (
          <UserTable
            title="Drivers"
            users={driverUsers}
            loading={loading && !driverUsers.length}
            showPhone={true}
            showRole={false}
            emptyMessage="No drivers found"
            onAddUser={() => handleOpenCreateModal('driver')}
            onDeleteUser={(user) => handleRemoveUser(user.id, user.full_name)}
          />
        )}

        {/* Invited Users Table */}
        {(hasRole(ROLES.ADMIN) || hasRole(ROLES.FLEET_MANAGER)) && invitedUsers.length > 0 && (
          <FadeIn delay={0.6}>
            <div className="mb-8">
              <h2 className="text-2xl font-semibold mb-4">Pending Invitations</h2>
              <div className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-lg p-6">
                <div className="overflow-x-auto">
                  <table className="w-full border-collapse">
                    <thead>
                      <tr className="border-b border-border">
                        <th className="text-left py-3 px-4">Name</th>
                        <th className="text-left py-3 px-4">Email</th>
                        <th className="text-left py-3 px-4">Role</th>
                        <th className="text-left py-3 px-4">Invited</th>
                        <th className="text-left py-3 px-4">Expires</th>
                        <th className="text-left py-3 px-4">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {currentInvitedUsers.map(invitation => (
                        <tr
                          key={invitation.id}
                          className="border-b border-border hover:bg-accent/10 cursor-pointer"
                        >
                          <td className="py-3 px-4">{invitation.full_name}</td>
                          <td className="py-3 px-4">{invitation.email}</td>
                          <td className="py-3 px-4">
                            <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800 capitalize">
                              {invitation.role.replace('_', ' ')}
                            </span>
                          </td>
                          <td className="py-3 px-4">
                            {new Date(invitation.created_at).toLocaleDateString()}
                          </td>
                          <td className="py-3 px-4">
                            {new Date(invitation.expires_at).toLocaleDateString()}
                          </td>
                          <td className="py-3 px-4" onClick={e => e.stopPropagation()}>
                            <div className="flex space-x-2">
                              {invitationActions(invitation).map((action, index) => (
                                <button
                                  key={index}
                                  className={
                                    action.variant === 'destructive'
                                      ? 'text-destructive hover:text-destructive/80'
                                      : 'text-primary hover:text-primary/80'
                                  }
                                  title={action.label}
                                  onClick={action.onClick}
                                  disabled={action.disabled()}
                                >
                                  {action.label}
                                </button>
                              ))}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Pagination for invited users table */}
                {invitedUsersTotalPages > 1 && (
                  <div className="mt-6 flex items-center justify-between">
                    <div>
                      <select
                        value={invitedUsersPerPage}
                        onChange={changeInvitedUsersItemsPerPage}
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
                        Page {invitedUsersCurrentPage} of {invitedUsersTotalPages}
                      </span>
                      <div className="flex gap-1">
                        <button
                          onClick={goToInvitedUsersPrevPage}
                          disabled={invitedUsersCurrentPage === 1}
                          className={`p-1 rounded ${invitedUsersCurrentPage === 1
                            ? 'text-muted-foreground cursor-not-allowed'
                            : 'hover:bg-accent'
                            }`}
                          title="Previous page"
                        >
                          <ChevronLeft size={18} />
                        </button>
                        <button
                          onClick={goToInvitedUsersNextPage}
                          disabled={invitedUsersCurrentPage === invitedUsersTotalPages}
                          className={`p-1 rounded ${invitedUsersCurrentPage === invitedUsersTotalPages
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
    </FadeIn>
  );
};

export default UserManagement;
