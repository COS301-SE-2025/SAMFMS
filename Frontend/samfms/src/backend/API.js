const hostname = 'localhost:8000';

export const API_URL = `http://${hostname}`;

export const API = {
  login: `${API_URL}/login`,
  signup: `${API_URL}/signup`,
  logout: `${API_URL}/logout`,
  me: `${API_URL}/me`,
  users: `${API_URL}/users`,
  changePassword: `${API_URL}/change-password`,
  deleteAccount: `${API_URL}/account`,
  updatePreferences: `${API_URL}/update-preferences`,
};

export const signup = async (full_name, email, password, confirmPassword, phoneNo, role) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    throw new Error('Invalid email format');
  }

  if (password !== confirmPassword) {
    throw new Error('Passwords do not match');
  }

  const response = await fetch(`${API_URL}/signup`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      full_name,
      email,
      password,
      phoneNo,
      role: role || 'user',
    }),
  });

  return response;
};

export const login = async (email, password) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    throw new Error('Invalid email format');
  }

  const response = await fetch(`${API_URL}/login`, {
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
  // Store token in localStorage
  localStorage.setItem('token', data.access_token);
  localStorage.setItem('user', JSON.stringify(data.user));
  return data;
};

export const logout = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
};

export const getCurrentUser = () => {
  const user = localStorage.getItem('user');
  return user ? JSON.parse(user) : null;
};

export const isAuthenticated = () => {
  return !!localStorage.getItem('token');
};

export const getToken = () => {
  return localStorage.getItem('token');
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

// Driver API endpoints
export const DRIVER_API = {
  drivers: `${API_URL}/drivers`,
  createDriver: `${API_URL}/drivers`,
  getDriver: id => `${API_URL}/drivers/${id}`,
  updateDriver: id => `${API_URL}/drivers/${id}`,
  deleteDriver: id => `${API_URL}/drivers/${id}`,
  searchDrivers: query => `${API_URL}/drivers/search/${query}`,
};

// Driver API functions
export const createDriver = async driverData => {
  const token = getToken();
  if (!token) {
    throw new Error('No authentication token found');
  }

  const response = await fetch(DRIVER_API.createDriver, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(driverData),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to create driver');
  }

  return response.json();
};

export const getDrivers = async (params = {}) => {
  const token = getToken();
  if (!token) {
    throw new Error('No authentication token found');
  }

  const queryParams = new URLSearchParams();
  if (params.skip) queryParams.append('skip', params.skip);
  if (params.limit) queryParams.append('limit', params.limit);
  if (params.status_filter) queryParams.append('status_filter', params.status_filter);
  if (params.department_filter) queryParams.append('department_filter', params.department_filter);

  const url = `${DRIVER_API.drivers}${queryParams.toString() ? '?' + queryParams.toString() : ''}`;

  const response = await fetch(url, {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to fetch drivers');
  }

  return response.json();
};

export const getDriver = async driverId => {
  const token = getToken();
  if (!token) {
    throw new Error('No authentication token found');
  }

  const response = await fetch(DRIVER_API.getDriver(driverId), {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to fetch driver');
  }

  return response.json();
};

export const updateDriver = async (driverId, updateData) => {
  const token = getToken();
  if (!token) {
    throw new Error('No authentication token found');
  }

  const response = await fetch(DRIVER_API.updateDriver(driverId), {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(updateData),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to update driver');
  }

  return response.json();
};

export const deleteDriver = async driverId => {
  const token = getToken();
  if (!token) {
    throw new Error('No authentication token found');
  }

  const response = await fetch(DRIVER_API.deleteDriver(driverId), {
    method: 'DELETE',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to delete driver');
  }

  return response.json();
};

export const searchDrivers = async query => {
  const token = getToken();
  if (!token) {
    throw new Error('No authentication token found');
  }

  const response = await fetch(DRIVER_API.searchDrivers(encodeURIComponent(query)), {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to search drivers');
  }

  return response.json();
};
