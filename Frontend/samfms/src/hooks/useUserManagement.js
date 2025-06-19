import { useState, useEffect, useCallback } from 'react';
import { listUsers, inviteUser, updateUserPermissions, getRoles } from '../backend/API';
import { useAuth, ROLES } from '../components/RBACUtils';

/**
 * Custom hook to handle user management functionality
 * This centralizes the user management logic and makes it reusable across components
 */
export const useUserManagement = () => {
  const { hasPermission, hasRole } = useAuth();
  const [users, setUsers] = useState([]);
  const [adminUsers, setAdminUsers] = useState([]);
  const [managerUsers, setManagerUsers] = useState([]);
  const [driverUsers, setDriverUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [roles, setRoles] = useState([]);

  // Function to load all users
  const loadUsers = useCallback(async () => {
    try {
      setLoading(true);
      setError('');

      const usersData = await listUsers();
      setUsers(usersData);

      // Filter users by role
      const admins = usersData.filter(user => user.role === ROLES.ADMIN);
      const managers = usersData.filter(user => user.role === ROLES.FLEET_MANAGER);
      const drivers = usersData.filter(user => user.role === ROLES.DRIVER);

      setAdminUsers(admins);
      setManagerUsers(managers);
      setDriverUsers(drivers);

      return usersData;
    } catch (err) {
      console.error('Error loading users:', err);
      setError(`Failed to load users: ${err.message || 'Unknown error'}`);
      return [];
    } finally {
      setLoading(false);
    }
  }, []);

  // Function to load available roles
  const loadRoles = useCallback(async () => {
    try {
      const rolesData = await getRoles();
      if (rolesData && rolesData.roles) {
        setRoles(rolesData.roles);
      }
      return rolesData;
    } catch (err) {
      console.error('Failed to load roles:', err);
      return null;
    }
  }, []);

  // Function to invite a new user
  const createUser = async userData => {
    try {
      setLoading(true);
      setError('');
      setSuccess('');

      const result = await inviteUser(userData);
      setSuccess(`User ${userData.full_name} has been invited successfully!`);
      await loadUsers(); // Refresh user list

      return result;
    } catch (err) {
      setError(`Failed to invite user: ${err.message || 'Unknown error'}`);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Function to update user role/permissions
  const updateUser = async (userId, data) => {
    try {
      setLoading(true);
      setError('');
      setSuccess('');

      const result = await updateUserPermissions({
        user_id: userId,
        ...data,
      });

      setSuccess('User updated successfully!');
      await loadUsers(); // Refresh user list

      return result;
    } catch (err) {
      setError(`Failed to update user: ${err.message || 'Unknown error'}`);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Function to remove/deactivate a user
  const removeUser = async userId => {
    try {
      setLoading(true);
      setError('');
      setSuccess('');

      await updateUserPermissions({
        user_id: userId,
        role: 'inactive',
        is_active: false,
      });

      setSuccess('User has been removed from the system.');
      await loadUsers(); // Refresh user list

      return true;
    } catch (err) {
      setError(`Failed to remove user: ${err.message || 'Unknown error'}`);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Load data on mount if user has permission
  useEffect(() => {
    if (hasPermission('users:manage') || hasRole(ROLES.ADMIN)) {
      loadUsers();
      loadRoles();
    }
  }, [hasPermission, hasRole, loadRoles, loadUsers]);

  return {
    users,
    adminUsers,
    managerUsers,
    driverUsers,
    roles,
    loading,
    error,
    success,
    setError,
    setSuccess,
    loadUsers,
    loadRoles,
    createUser,
    updateUser,
    removeUser,
    hasPermission,
    hasRole,
  };
};

export default useUserManagement;
