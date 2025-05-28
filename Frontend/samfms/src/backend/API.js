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
