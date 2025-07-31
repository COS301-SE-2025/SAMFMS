import React, { useMemo } from 'react';
import { hasPermission, hasRole, hasAnyRole, getCurrentUser } from '../backend/API.js';

// HOC for permission-based rendering
export const withPermission = permission => Component => {
  return props => {
    if (!hasPermission(permission)) {
      return null;
    }
    return <Component {...props} />;
  };
};

// HOC for role-based rendering
export const withRole = role => Component => {
  return props => {
    if (!hasRole(role)) {
      return null;
    }
    return <Component {...props} />;
  };
};

// HOC for multiple roles
export const withAnyRole = roles => Component => {
  return props => {
    if (!hasAnyRole(roles)) {
      return null;
    }
    return <Component {...props} />;
  };
};

// Component for conditional rendering based on permissions
export const PermissionGuard = ({ permission, children, fallback = null }) => {
  if (!hasPermission(permission)) {
    return fallback;
  }
  return children;
};

// Component for conditional rendering based on roles
export const RoleGuard = ({ role, children, fallback = null }) => {
  if (!hasRole(role)) {
    return fallback;
  }
  return children;
};

// Component for conditional rendering based on multiple roles
export const AnyRoleGuard = ({ roles, children, fallback = null }) => {
  if (!hasAnyRole(roles)) {
    return fallback;
  }
  return children;
};

// Hook for accessing current user's role and permissions
export const useAuth = () => {
  const user = getCurrentUser();

  // Memoize the auth functions to prevent unnecessary re-renders
  return useMemo(
    () => ({
      user,
      hasPermission: permission => hasPermission(permission),
      hasRole: role => hasRole(role),
      hasAnyRole: roles => hasAnyRole(roles),
      isAdmin: () => hasRole('admin'),
      isFleetManager: () => hasRole('fleet_manager'),
      isDriver: () => hasRole('driver'),
    }),
    [user]
  ); // Only recreate when user changes
};

// Constants for common permission checks
export const PERMISSIONS = {
  // Vehicle permissions
  VEHICLES_READ: 'vehicles:read',
  VEHICLES_WRITE: 'vehicles:write',
  VEHICLES_DELETE: 'vehicles:delete',
  VEHICLES_READ_ASSIGNED: 'vehicles:read_assigned',

  // Driver permissions
  DRIVERS_READ: 'drivers:read',
  DRIVERS_WRITE: 'drivers:write',
  DRIVERS_DELETE: 'drivers:delete',
  DRIVERS_READ_OWN: 'drivers:read_own',

  // Assignment permissions
  ASSIGNMENTS_READ: 'assignments:read',
  ASSIGNMENTS_WRITE: 'assignments:write',
  ASSIGNMENTS_DELETE: 'assignments:delete',

  // Report permissions
  REPORTS_READ: 'reports:read',
  ANALYTICS_READ: 'analytics:read',

  // Usage permissions
  USAGE_READ: 'usage:read',
  USAGE_WRITE: 'usage:write',

  // Status permissions
  STATUS_READ: 'status:read',
  STATUS_WRITE: 'status:write',

  // Profile permissions
  PROFILE_READ: 'profile:read',
  PROFILE_WRITE: 'profile:write',

  // Trip permissions
  TRIPS_READ_OWN: 'trips:read_own',
  TRIPS_WRITE_OWN: 'trips:write_own',

  // Maintenance permissions
  MAINTENANCE_READ_ASSIGNED: 'maintenance:read_assigned',
};

// Constants for roles
export const ROLES = {
  ADMIN: 'admin',
  FLEET_MANAGER: 'fleet_manager',
  DRIVER: 'driver',
};

const RBACUtils = {
  withPermission,
  withRole,
  withAnyRole,
  PermissionGuard,
  RoleGuard,
  AnyRoleGuard,
  useAuth,
  PERMISSIONS,
  ROLES,
};

export default RBACUtils;
