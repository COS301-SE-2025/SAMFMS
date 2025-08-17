import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth, ROLES } from '../auth/RBACUtils';

const RoleBasedRoute = ({
  adminComponent: AdminComponent,
  driverComponent: DriverComponent,
  ...props
}) => {
  const { hasRole } = useAuth();

  if (hasRole(ROLES.DRIVER)) {
    return DriverComponent ? (
      <DriverComponent {...props} />
    ) : (
      <Navigate to="/driver-home" replace />
    );
  }

  return AdminComponent ? <AdminComponent {...props} /> : <Navigate to="/dashboard" replace />;
};

export default RoleBasedRoute;
