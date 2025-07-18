// auth.js - Authentication API endpoints and functions
import { setCookie, getCookie, eraseCookie } from '../../lib/cookies';

// Determine the API hostname depending on environment
export const getApiHostname = () => {
  // Use environment variable if available (set in docker-compose or .env)
  const apiBaseUrl = process.env.REACT_APP_API_BASE_URL;
  
  if (apiBaseUrl) {
    console.log('Using API_BASE_URL from environment:', apiBaseUrl);
    return apiBaseUrl;
  }

  // Fallback logic for development
  if (typeof window !== 'undefined') {
    const protocol = window.location.protocol;
    const host = window.location.hostname;
    
    // For production/staging with HTTPS
    if (protocol === 'https:') {
      return `https://${host}/api`;
    }
    
    // For local development
    const CORE_SERVICE_PORT = process.env.REACT_APP_CORE_PORT || '21011';
    if (host === 'localhost' || host === '127.0.0.1') {
      return `http://localhost:${CORE_SERVICE_PORT}`;
    } else {
      return `http://${host}:${CORE_SERVICE_PORT}`;
    }
  }

  // Default fallback
  return 'http://localhost:21011';
};

const hostname = getApiHostname();
export const API_URL = hostname;

// Debug logging
console.log('API Configuration:');
console.log('- REACT_APP_API_BASE_URL:', process.env.REACT_APP_API_BASE_URL);
console.log('- API_URL:', API_URL);
console.log('- hostname:', hostname);

// Auth endpoints
export const AUTH_API = {
  login: `${API_URL}/auth/login`,
  signup: `${API_URL}/auth/signup`,
  logout: `${API_URL}/auth/logout`,
  refreshToken: `${API_URL}/auth/refresh`,
  me: `${API_URL}/auth/me`,
  users: `${API_URL}/auth/users`,
  changePassword: `${API_URL}/auth/change-password`,
  deleteAccount: `${API_URL}/auth/account`,
  updatePreferences: `${API_URL}/auth/update-preferences`,
  inviteUser: `${API_URL}/auth/invite-user`,
  createUser: `${API_URL}/auth/create-user`, // New endpoint for manual user creation
  updatePermissions: `${API_URL}/auth/update-permissions`,
  getRoles: `${API_URL}/auth/roles`,
  verifyPermission: `${API_URL}/auth/verify-permission`,
  userExists: `${API_URL}/auth/user-exists`,
  updateProfile: `${API_URL}/auth/update-profile`,
  uploadProfilePicture: `${API_URL}/auth/upload-profile-picture`,
};

// Helper functions for auth management
export const getToken = () => {
  return getCookie('token');
};

export const getCurrentUser = () => {
  const user = getCookie('user');
  const permissions = getCookie('permissions');
  const preferences = getCookie('preferences');

  if (!user) return null;

  const userData = JSON.parse(user);

  // Add permissions and preferences if available
  if (permissions) {
    userData.permissions = JSON.parse(permissions);
  }

  if (preferences) {
    userData.preferences = JSON.parse(preferences);
  }

  return userData;
};

export const isAuthenticated = () => {
  return !!getCookie('token');
};

export const logout = async () => {
  const token = getToken();

  // Stop token refresh timer
  try {
    const { stopTokenRefresh } = await import('../../utils/tokenManager');
    stopTokenRefresh();
  } catch (error) {
    console.error('Failed to stop token refresh:', error);
  }

  // Call server-side logout if we have a token
  if (token) {
    try {
      await fetchWithTimeout(
        AUTH_API.logout,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
        5000
      );
    } catch (error) {
      console.error('Server logout failed:', error);
      // Continue with client-side logout even if server call fails
    }
  }

  // Clear client-side storage completely
  eraseCookie('token');
  eraseCookie('refresh_token');
  eraseCookie('user');
  eraseCookie('permissions');
  eraseCookie('preferences');

  // Clear any localStorage items that might contain auth data
  try {
    localStorage.removeItem('authToken');
    localStorage.removeItem('userData');
    localStorage.removeItem('permissions');
    localStorage.removeItem('preferences');
  } catch (error) {
    console.error('Failed to clear localStorage:', error);
  }

  // Clear sessionStorage as well
  try {
    sessionStorage.clear();
  } catch (error) {
    console.error('Failed to clear sessionStorage:', error);
  }

  // Dispatch logout event for other components
  window.dispatchEvent(
    new CustomEvent('authLogout', {
      detail: { reason: 'user_initiated' },
    })
  );
};

// Enhanced logout with server-side call
export const logoutFromAllDevices = async () => {
  const token = getToken();

  if (token) {
    try {
      await fetchWithTimeout(
        `${API_URL}/auth/logout-all`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
        5000
      );
    } catch (error) {
      console.error('Server logout-all failed:', error);
    }
  }

  // Clear client-side storage
  eraseCookie('token');
  eraseCookie('refresh_token');
  eraseCookie('user');
  eraseCookie('permissions');
  eraseCookie('preferences');
};

// Function to refresh the authentication token
// This will be called automatically when a 401 error is received during an API call
// It can also be called proactively to refresh a token before it expires
export const refreshAuthToken = async () => {
  try {
    const refreshToken = getCookie('refresh_token');

    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await fetchWithTimeout(
      AUTH_API.refreshToken,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
      },
      5000
    );

    if (!response.ok) {
      throw new Error('Failed to refresh token');
    }

    const data = await response.json();

    // Update tokens in cookies with shorter expiry for access token
    setCookie('token', data.access_token, 1 / 96); // 15 minutes (1/96 of a day)

    if (data.refresh_token) {
      setCookie('refresh_token', data.refresh_token, 7); // 7 days
    }

    // Update user data
    setCookie(
      'user',
      JSON.stringify({
        id: data.user_id,
        role: data.role,
      }),
      1
    );

    setCookie('permissions', JSON.stringify(data.permissions), 1);

    return data.access_token;
  } catch (error) {
    console.error('Token refresh failed:', error);
    // On refresh failure, log the user out
    await logout();
    throw error;
  }
};

// Helper function to make authenticated API calls with token refresh capability
export const authFetch = async (url, options = {}) => {
  let token = getToken();

  if (!token) {
    throw new Error('No authentication token found');
  }

  // Construct full URL if relative path is provided
  const fullUrl = url.startsWith('http') ? url : `${API_URL}${url}`;

  const headers = {
    ...options.headers,
    Authorization: `Bearer ${token}`,
  };

  try {
    // First attempt with current token
    const response = await fetchWithTimeout(fullUrl, { ...options, headers }, 8000);

    // If unauthorized, try to refresh token and retry
    if (response.status === 401) {
      try {
        // Try to refresh the token
        token = await refreshAuthToken();

        // Retry with new token
        const newHeaders = {
          ...options.headers,
          Authorization: `Bearer ${token}`,
        };

        return fetchWithTimeout(fullUrl, { ...options, headers: newHeaders }, 8000);
      } catch (refreshError) {
        console.error('Auth refresh failed:', refreshError);
        // If refresh fails, redirect to login
        window.location.href = '/login';
        throw new Error('Authentication expired. Please log in again.');
      }
    }

    return response;
  } catch (error) {
    console.error('Auth fetch error:', error);
    throw error;
  }
};

// Auth API functions
export const signup = async (full_name, email, password, confirmPassword, phoneNo) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    throw new Error('Invalid email format');
  }

  if (password !== confirmPassword) {
    throw new Error('Passwords do not match');
  } // Define default preferences
  const defaultPreferences = {
    theme: 'light',
    animations: 'true',
    email_alerts: 'true',
    push_notifications: 'true',
    two_factor: 'false',
    activity_log: 'true',
    session_timeout: '30 minutes',
  };

  try {
    console.log('Attempting signup for email:', email);
    const response = await fetchWithTimeout(
      `${API_URL}/auth/signup`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          full_name,
          email,
          password,
          phoneNo,
          preferences: defaultPreferences,
          // No role specified - will be assigned based on first user logic or require invitation
        }),
      },
      10000
    ); // Longer timeout for signup operation

    if (response.ok) {
      const data = await response.json();
      console.log('Signup response data:', data);

      // Store tokens with consistent expiry times
      setCookie('token', data.access_token, 1 / 96); // 15 minutes to match backend

      // Store refresh token if available
      if (data.refresh_token) {
        setCookie('refresh_token', data.refresh_token, 7); // 7 days for refresh token
      }
      setCookie(
        'user',
        JSON.stringify({
          id: data.user_id,
          email: email,
          role: data.role,
        }),
        1 // 1 day for user data
      );

      // Store permissions and preferences if available
      if (data.permissions) {
        console.log('Storing permissions in cookie:', data.permissions);
        setCookie('permissions', JSON.stringify(data.permissions), 1); // 1 day
      }

      if (data.preferences) {
        console.log('Storing preferences in cookie:', data.preferences);
        setCookie('preferences', JSON.stringify(data.preferences), 1); // 1 day
      } else {
        // If no preferences returned, store defaults
        console.log('No preferences in response, storing defaults');
        setCookie('preferences', JSON.stringify(defaultPreferences), 1);
      }

      // Start automatic token refresh
      const { startTokenRefresh } = await import('../../utils/tokenManager');
      startTokenRefresh();

      // Clear user existence cache after successful signup
      clearUserExistenceCache();

      return data;
    }

    return response;
  } catch (error) {
    console.error('Signup error:', error);
    throw error; // Rethrow to let the UI handle it
  }
};

export const login = async (email, password) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    throw new Error('Invalid email format');
  }

  try {
    console.log('Attempting login with email:', email);
    const response = await fetchWithTimeout(
      `${API_URL}/auth/login`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email,
          password,
        }),
      },
      10000
    ); // Longer timeout for login operation

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Login failed');
    }
    const data = await response.json();
    console.log('Login response data:', data);

    // Store tokens with consistent expiry times
    setCookie('token', data.access_token, 1 / 96); // 15 minutes to match backend
    console.log('Token stored:', data.access_token ? 'Yes' : 'No');
    console.log('Token cookie check:', getCookie('token') ? 'Found' : 'Not found');

    // Store refresh token if available
    if (data.refresh_token) {
      setCookie('refresh_token', data.refresh_token, 7); // 7 days for refresh token
    }

    // Store user data for 24 hours
    setCookie(
      'user',
      JSON.stringify({
        id: data.user_id,
        email: email,
        role: data.role,
      }),
      1 // 1 day
    );
    setCookie('permissions', JSON.stringify(data.permissions), 1); // 1 day
    setCookie('preferences', JSON.stringify(data.preferences), 1); // 1 day

    // Start automatic token refresh
    const { startTokenRefresh } = await import('../../utils/tokenManager');
    startTokenRefresh();

    return data;
  } catch (error) {
    console.error('Login error:', error);
    throw error; // Rethrow to let the UI handle it
  }
};

// Change Password
export const changePassword = async (currentPassword, newPassword) => {
  const token = getToken();
  if (!token) {
    throw new Error('No authentication token found');
  }

  const response = await fetchWithTimeout(
    AUTH_API.changePassword,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        current_password: currentPassword,
        new_password: newPassword,
      }),
    },
    10000 // 10 second timeout
  );

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to change password');
  }

  return response.json();
};

// Delete Account
export const deleteAccount = async () => {
  const token = getToken();
  if (!token) {
    throw new Error('No authentication token found');
  }

  const response = await fetch(AUTH_API.deleteAccount, {
    method: 'DELETE',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to delete account');
  }

  // Clear local storage on successful account deletion
  logout();
  return response.json();
};

// Update Preferences
export const updatePreferences = async preferences => {
  const token = getToken();
  if (!token) {
    throw new Error('No authentication token found');
  }

  try {
    console.log('Sending preferences update request:', preferences);
    console.log('API URL:', AUTH_API.updatePreferences);

    const response = await fetchWithTimeout(
      AUTH_API.updatePreferences,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ preferences }),
      },
      10000 // 10 second timeout
    );

    console.log('Response status:', response.status);
    console.log('Response ok:', response.ok);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
      console.error('Error response data:', errorData);
      throw new Error(errorData.detail || 'Failed to update preferences');
    }

    const result = await response.json();
    console.log('Success response:', result);

    // Only update cookie if backend operation was successful and returned preferences
    if (result && result.preferences) {
      setCookie('preferences', JSON.stringify(result.preferences), 30);
    } else {
      // Fallback: update cookie with sent preferences if no preferences returned
      setCookie('preferences', JSON.stringify(preferences), 30);
    }

    return result;
  } catch (error) {
    console.error('Error updating preferences:', error);
    throw error;
  }
};

// Update User Profile
export const updateUserProfile = async userData => {
  const token = getToken();
  if (!token) {
    throw new Error('No authentication token found');
  }

  try {
    const response = await fetchWithTimeout(
      AUTH_API.updateProfile,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(userData),
      },
      10000
    ); // 10 second timeout

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to update profile');
    }

    // Update user data in cookies
    const currentUser = getCurrentUser();
    const updatedUser = { ...currentUser, ...userData };
    setCookie('user', JSON.stringify(updatedUser), 30);

    return response.json();
  } catch (error) {
    console.error('Profile update error:', error);
    throw error;
  }
};

// Upload Profile Picture
export const uploadProfilePicture = async file => {
  const token = getToken();
  if (!token) {
    throw new Error('No authentication token found');
  }

  try {
    const formData = new FormData();
    formData.append('profile_picture', file);

    const response = await fetchWithTimeout(
      AUTH_API.uploadProfilePicture,
      {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      },
      20000
    ); // 20 second timeout for file uploads

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to upload profile picture');
    }
    const data = await response.json();

    // Update profile picture URL in user data cookie
    const currentUser = getCurrentUser();
    if (currentUser && data.profile_picture_url) {
      // Create a new object to ensure the cookie is updated
      const updatedUser = {
        ...currentUser,
        profile_picture_url: data.profile_picture_url,
      };
      // Update the cookie with the refreshed data
      setCookie('user', JSON.stringify(updatedUser), 30);
    }

    return data;
  } catch (error) {
    console.error('Profile picture upload error:', error);
    throw error;
  }
};

// Admin Functions for User Management
export const inviteUser = async userData => {
  const token = getToken();
  if (!token) {
    throw new Error('No authentication token found');
  }

  const response = await fetch(AUTH_API.inviteUser, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(userData),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to invite user');
  }

  return response.json();
};

/**
 * Manually create a new user (Admin only)
 * @param {Object} userData - The user data object
 * @param {string} userData.full_name - Full name of the user
 * @param {string} userData.email - Email address
 * @param {string} userData.role - User role (admin, fleet_manager, driver)
 * @param {string} userData.password - Initial password
 * @param {string} [userData.phoneNo] - Phone number (optional)
 * @returns {Promise<Object>} - Response with user creation status
 */
export const createUserManually = async userData => {
  const token = getToken();
  if (!token) {
    throw new Error('No authentication token found');
  }

  try {
    // Ensure userData has all required fields and proper format
    const sanitizedData = {
      full_name: userData.full_name,
      email: userData.email,
      role: userData.role || 'driver',
      password: userData.password,
      phoneNo: userData.phoneNo || null,
      details: userData.details || {},
    }; // Log the request data for debugging
    console.log('Creating user with data:', sanitizedData);
    console.log('Sending request to:', AUTH_API.createUser);
    console.log('Request headers:', {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    });
    console.log('Request body:', JSON.stringify(sanitizedData));

    const response = await fetch(AUTH_API.createUser, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(sanitizedData),
    });

    console.log('Response status:', response.status);
    console.log('Response ok:', response.ok);

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to create user');
    }

    return response.json();
  } catch (error) {
    console.error('Error creating user:', error);
    throw error;
  }
};

// Cache for users data
let usersCache = null;
let usersCacheTimestamp = null;
const USERS_CACHE_TTL = 2 * 60 * 1000; // 2 minutes cache (shorter than roles since users data changes more frequently)

export const listUsers = async () => {
  // Return cached data if available and not expired
  const now = Date.now();
  if (usersCache && usersCacheTimestamp && now - usersCacheTimestamp < USERS_CACHE_TTL) {
    return Promise.resolve(usersCache);
  }

  // Use authFetch to automatically handle token and refresh if needed
  const response = await authFetch(AUTH_API.users, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(errorData.detail || 'Failed to fetch users');
  }

  // Cache the result
  const data = await response.json();
  usersCache = data;
  usersCacheTimestamp = now;

  return data;
};

export const updateUserPermissions = async userData => {
  const token = getToken();
  if (!token) {
    throw new Error('No authentication token found');
  }

  const response = await fetch(AUTH_API.updatePermissions, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(userData),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to update user permissions');
  }

  return response.json();
};

// Cache for roles data
let rolesCache = null;
let rolesCacheTimestamp = null;
const ROLES_CACHE_TTL = 5 * 60 * 1000; // 5 minutes cache

export const getRoles = async () => {
  // Return cached data if available and not expired
  const now = Date.now();
  if (rolesCache && rolesCacheTimestamp && now - rolesCacheTimestamp < ROLES_CACHE_TTL) {
    return Promise.resolve(rolesCache);
  }

  // Use authFetch to automatically handle token and refresh if needed
  const response = await authFetch(AUTH_API.getRoles, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(
      `Internal server error: ${response.status}: ${errorData.detail || 'Not authenticated'}`
    );
  }

  // Cache the result
  const data = await response.json();
  rolesCache = data;
  rolesCacheTimestamp = now;

  return data;
};

export const verifyPermission = async permission => {
  const token = getToken();
  if (!token) {
    throw new Error('No authentication token found');
  }

  const response = await fetch(AUTH_API.verifyPermission, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ permission }),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to verify permission');
  }

  return response.json();
};

// RBAC Helper Functions
export const hasPermission = permission => {
  const user = getCurrentUser();
  if (!user || !user.permissions) return false;

  return user.permissions.includes(permission) || user.permissions.includes('*');
};

export const hasRole = role => {
  const user = getCurrentUser();
  if (!user) return false;

  return user.role === role;
};

export const hasAnyRole = roles => {
  const user = getCurrentUser();
  if (!user) return false;

  return roles.includes(user.role);
};

// Get Current User Info
export const getUserInfo = async () => {
  const token = getToken();
  if (!token) {
    console.warn('No authentication token found, using cookie data');
    return getCurrentUser() || {};
  }

  try {
    console.log('Fetching user info from:', AUTH_API.me);
    const response = await fetchWithTimeout(
      AUTH_API.me,
      {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      },
      10000
    ); // Increase timeout to 10 seconds

    if (!response.ok) {
      console.warn(`Failed to fetch user info: ${response.status}`);
      throw new Error('Failed to fetch user info from API');
    }
    const data = await response.json();
    console.log('Got user data:', data);

    // Normalize data structure - ensure user_id exists for backward compatibility
    if (data.id && !data.user_id) {
      data.user_id = data.id;
    }

    return data;
  } catch (error) {
    console.error('Error getting user info:', error);
    // If we can't get user info from API, use the data from cookies
    const cookieUser = getCurrentUser();
    if (cookieUser) {
      console.log('Using cookie data instead:', cookieUser);
      return cookieUser;
    }
    // Return empty object to prevent further errors
    return {};
  }
};

// Utility function to create fetch requests with timeout
export const fetchWithTimeout = async (url, options = {}, timeout = 5000) => {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeout);

  // Only log in development mode to reduce noise
  const isDevMode = process.env.NODE_ENV === 'development';

  try {
    // Log the request in development
    if (isDevMode && !url.includes('/roles') && !url.includes('/users')) {
      // Skip logging for roles and users endpoints
      console.log(`Fetching ${url}...`);
    }

    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    clearTimeout(id); // Log response status
    if (isDevMode && !url.includes('/roles') && !url.includes('/users')) {
      // Skip logging for roles and users endpoints
      console.log(`${url} responded with status: ${response.status}`);
    }

    return response;
  } catch (error) {
    clearTimeout(id);
    console.error(`Request to ${url} failed:`, error);

    // Enhance error message for common issues
    if (error.name === 'AbortError') {
      throw new Error(`Request to ${url} timed out after ${timeout}ms`);
    } else if (error.message && error.message.includes('Failed to fetch')) {
      throw new Error(
        `Network error when connecting to ${url}. The service may be down or unreachable.`
      );
    }

    throw error;
  }
};

// Check if there are any users in the system (for signup flow)
// Use a module-level variable to cache the result and prevent duplicate API calls
let userExistenceCache = null;
let userExistenceCacheExpiry = 0;
const CACHE_TTL = 5 * 60 * 1000; // 5 minute cache

// Function to clear the user existence cache - useful for forcing a fresh check
export const clearUserExistenceCache = () => {
  userExistenceCache = null;
  userExistenceCacheExpiry = 0;
};

export const checkUserExistence = async (forceRefresh = false) => {
  // Return cached value if it's still valid and not forced to refresh
  const now = Date.now();
  if (!forceRefresh && userExistenceCache !== null && now < userExistenceCacheExpiry) {
    console.log('Using cached user existence result:', userExistenceCache);
    return userExistenceCache;
  }

  try {
    console.log('Checking if users exist in the system...');
    // Try to make a request to check if users exist in the system
    const response = await fetchWithTimeout(
      AUTH_API.userExists,
      {
        method: 'GET',
      },
      3000
    ).catch(error => {
      console.log('Failed to check user existence through user-exists endpoint', error);
      return { ok: false };
    });

    if (response.ok) {
      const data = await response.json();
      console.log('User existence response:', data);

      // Cache the result
      userExistenceCache = data.userExists;
      userExistenceCacheExpiry = now + CACHE_TTL;

      return data.userExists;
    } // If the dedicated endpoint doesn't exist, try a different approach
    try {
      // Try to directly check if there are any users by querying users endpoint
      console.log('Trying alternative approach - checking for users directly');
      const checkUsersResponse = await fetchWithTimeout(
        `${API_URL}/auth/users/count`,
        {
          method: 'GET',
        },
        3000
      ).catch(error => {
        console.log('User count endpoint failed:', error);
        return { ok: false };
      });

      if (checkUsersResponse.ok) {
        const data = await checkUsersResponse.json();
        console.log('User count response:', data);
        const usersExist = data.count > 0;

        // Cache the result
        userExistenceCache = usersExist;
        userExistenceCacheExpiry = now + CACHE_TTL;
        return usersExist;
      }

      // If that fails, fall back to checking if login endpoint exists
      console.log('Trying fallback - checking login endpoint');
      const loginEndpointResponse = await fetchWithTimeout(
        `${API_URL}/auth/login`,
        {
          method: 'OPTIONS',
        },
        3000
      ).catch(() => ({ status: 0 }));

      console.log('Login endpoint check status:', loginEndpointResponse.status);

      // If the login endpoint exists but returns 405 Method Not Allowed,
      // we can't determine if users exist - we need to check another way
      if (loginEndpointResponse.status === 405) {
        // For 405 responses, we'll use environment to make a best guess
        const isLocalhost =
          window.location.hostname === 'localhost' ||
          window.location.hostname === '127.0.0.1' ||
          window.location.hostname.includes('192.168.');

        console.log(
          "Login endpoint exists but can't determine user existence. Using environment guess. Localhost?",
          isLocalhost
        );

        // For localhost development, default to assuming no users exist
        // This makes it easier for developers to test initial setup flows
        const result = !isLocalhost;

        // Cache the result with shorter expiry since it's a guess
        userExistenceCache = result;
        userExistenceCacheExpiry = now + 60 * 1000; // 1 minute cache for guesses
        return result;
      }
    } catch (e) {
      console.log('Error checking auth endpoints:', e);
    }

    // Final fallback - check environment to give best UX
    // In development/localhost, default to assuming no users (to make signup easier)
    // In production, default to assuming users exist (more secure)
    const isLocalhost =
      window.location.hostname === 'localhost' ||
      window.location.hostname === '127.0.0.1' ||
      window.location.hostname.includes('192.168.');

    console.log('Using environment-based fallback. Localhost?', isLocalhost);

    // For localhost development, we'll default to "no users" to enable signup
    // For production deployment, we'll default to "users exist" for security
    const result = !isLocalhost; // false for localhost (no users), true otherwise (users exist)

    // Cache the result
    userExistenceCache = result;
    userExistenceCacheExpiry = now + CACHE_TTL;

    return result;
  } catch (error) {
    console.error('Error in checkUserExistence:', error);
    // If all checks fail, err on the side of caution and assume users exist
    userExistenceCache = true;
    userExistenceCacheExpiry = now + CACHE_TTL;
    return true;
  }
};

// Cache clearing functions
export const clearUsersCache = () => {
  usersCache = null;
  usersCacheTimestamp = null;
};

export const clearRolesCache = () => {
  rolesCache = null;
  rolesCacheTimestamp = null;
};

export const clearAllAuthCache = () => {
  clearUsersCache();
  clearRolesCache();
};
