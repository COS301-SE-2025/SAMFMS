// ============================================================================
// LEGACY API FILE - BACKWARD COMPATIBILITY LAYER
// ============================================================================
// This file provides backward compatibility for existing imports.
// New code should import directly from the modular API files in ./api/
//
// Migration Guide:
// - Instead of: import { getVehicles } from '../backend/API'
// - Use: import { getVehicles } from '../backend/api/vehicles'
// - Or: import { getVehicles } from '../backend/api'
// ============================================================================

// Re-export all authentication-related functionality
export {
  API_URL,
  AUTH_API as API,
  getToken,
  getCurrentUser,
  isAuthenticated,
  authFetch,
  login,
  signup,
  logout,
  logoutFromAllDevices,
  refreshAuthToken,
  changePassword,
  deleteAccount,
  updatePreferences,
  inviteUser,
  createUserManually,
  listUsers,
  updateUserPermissions,
  getRoles,
  verifyPermission,
  hasPermission,
  hasRole,
  hasAnyRole,
  getUserInfo,
  checkUserExistence,
  clearUserExistenceCache,
  updateUserProfile,
  uploadProfilePicture,
  clearUsersCache,
  clearRolesCache,
  clearAllAuthCache,
  fetchWithTimeout,
} from './api/auth';

// Re-export analytics functions
export {
  getTotalVehicles,
  getFleetUtilization,
  getVehicleUsage,
  getAssignmentMetrics,
  getMaintenanceAnalytics,
  getDriverPerformance,
  getCostAnalytics,
  getStatusBreakdown,
  getIncidentStatistics,
  getDepartmentLocationAnalytics,
} from './api/analytics';

// Re-export vehicle management functions
export {
  createVehicle,
  getVehicles,
  getVehicle,
  updateVehicle,
  deleteVehicle,
  searchVehicles,
} from './api/vehicles';

// Re-export driver management functions
export {
  createDriver,
  getDrivers,
  getDriver,
  updateDriver,
  deleteDriver,
  searchDrivers,
} from './api/drivers';

// Re-export assignment management functions
export {
  getVehicleAssignments,
  createVehicleAssignment,
  updateVehicleAssignment,
  deleteVehicleAssignment,
} from './api/assignments';

// Re-export invitation management functions
export {
  sendInvitation,
  getPendingInvitations,
  resendInvitation,
  cancelInvitation,
  verifyInvitationOTP,
  completeUserRegistration,
} from './api/invitations';

// Re-export plugin functions
export {
  getPlugins,
  startPlugin,
  stopPlugin,
  updatePluginRoles,
  getAllPlugins,
  getPluginStatus,
  testCoreService,
  syncPluginStatus,
  debugDockerAccess,
  addSblock,
  removeSblock,
} from './api/plugins';

// Legacy endpoint constants for backward compatibility
import { API_URL } from './api/auth';
import { buildApiUrl } from '../config/apiConfig';

export const DRIVER_API = {
  drivers: `${API_URL}/drivers`,
  createDriver: `${API_URL}/drivers`,
  getDriver: id => `${API_URL}/drivers/${id}`,
  updateDriver: id => `${API_URL}/drivers/${id}`,
  deleteDriver: id => `${API_URL}/drivers/${id}`,
  searchDrivers: query => `${API_URL}/drivers/search/${query}`,
};

export const VEHICLE_API = {
  vehicles: `${API_URL}/vehicles`,
  createVehicle: `${API_URL}/vehicles`,
  getVehicle: id => `${API_URL}/vehicles/${id}`,
  updateVehicle: id => `${API_URL}/vehicles/${id}`,
  deleteVehicle: id => `${API_URL}/vehicles/${id}`,
  searchVehicles: query => `${API_URL}/vehicles/search/${query}`,
};

export const VEHICLE_ASSIGNMENT_API = {
  assignments: `${API_URL}/vehicle-assignments`,
  createAssignment: `${API_URL}/vehicle-assignments`,
  getAssignment: id => `${API_URL}/vehicle-assignments/${id}`,
  updateAssignment: id => `${API_URL}/vehicle-assignments/${id}`,
  deleteAssignment: id => `${API_URL}/vehicle-assignments/${id}`,
};

export const PLUGIN_API = {
  plugins: `${API_URL}/service_presence`,
};

// ============================================================================
// DEPRECATED FUNCTIONS - Use modular API instead
// ============================================================================
// These functions are kept for backward compatibility but are deprecated.
// They now simply call the new modular API functions.
// ============================================================================

console.warn('DEPRECATED: Using legacy API.js file. Please migrate to modular API imports.');
