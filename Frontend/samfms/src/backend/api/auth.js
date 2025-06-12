// auth.js - Authentication API endpoints and functions
const hostname = 'localhost:8000'; // Core service port
export const API_URL = `http://${hostname}`;

// Auth endpoints
export const AUTH_API = {
  login: `${API_URL}/auth/login`,
  signup: `${API_URL}/auth/signup`,
  logout: `${API_URL}/auth/logout`,
  me: `${API_URL}/auth/me`,
  users: `${API_URL}/auth/users`,
  changePassword: `${API_URL}/auth/change-password`,
  deleteAccount: `${API_URL}/auth/account`,
  updatePreferences: `${API_URL}/auth/update-preferences`,
  inviteUser: `${API_URL}/auth/invite-user`,
  updatePermissions: `${API_URL}/auth/update-permissions`,
  getRoles: `${API_URL}/auth/roles`,
  verifyPermission: `${API_URL}/auth/verify-permission`,
};

// Helper functions for auth management
export const getToken = () => {
  return localStorage.getItem('token');
};

export const getCurrentUser = () => {
  const user = localStorage.getItem('user');
  return user ? JSON.parse(user) : null;
};

export const isAuthenticated = () => {
  return !!localStorage.getItem('token');
};

export const logout = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
};

// Helper function to make authenticated API calls
export const authFetch = async (url, options = {}) => {
  const token = getToken();
  const headers = {
    ...options.headers,
    Authorization: `Bearer ${token}`,
  };

  return fetch(url, { ...options, headers });
};

// Auth API functions
export const signup = async (full_name, email, password, confirmPassword, phoneNo) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    throw new Error('Invalid email format');
  }

  if (password !== confirmPassword) {
    throw new Error('Passwords do not match');
  }

  const response = await fetch(`${API_URL}/auth/signup`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      full_name,
      email,
      password,
      phoneNo,
      // No role specified - will be assigned based on first user logic or require invitation
    }),
  });

  return response;
};

export const login = async (email, password) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    throw new Error('Invalid email format');
  }

  const response = await fetch(`${API_URL}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      email,
      password,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Login failed');
  }

  const data = await response.json();
  // Store token and user data with role and permissions
  localStorage.setItem('token', data.access_token);
  localStorage.setItem(
    'user',
    JSON.stringify({
      id: data.user_id,
      role: data.role,
      permissions: data.permissions,
      preferences: data.preferences,
    })
  );
  return data;
};

// Change Password
export const changePassword = async (currentPassword, newPassword) => {
  const token = getToken();
  if (!token) {
    throw new Error('No authentication token found');
  }

  const response = await fetch(AUTH_API.changePassword, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      current_password: currentPassword,
      new_password: newPassword,
    }),
  });

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

  const response = await fetch(AUTH_API.updatePreferences, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ preferences }),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to update preferences');
  }

  // Update user object in localStorage with new preferences
  const user = getCurrentUser();
  if (user) {
    user.preferences = preferences;
    localStorage.setItem('user', JSON.stringify(user));
  }

  return response.json();
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

export const listUsers = async () => {
  const token = getToken();
  if (!token) {
    throw new Error('No authentication token found');
  }

  const response = await fetch(AUTH_API.users, {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to fetch users');
  }

  return response.json();
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

export const getRoles = async () => {
  const response = await fetch(AUTH_API.getRoles, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to fetch roles');
  }

  return response.json();
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
    throw new Error('No authentication token found');
  }

  const response = await fetch(AUTH_API.me, {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to fetch user info');
  }

  return response.json();
};
