const hostname = 'localhost:21004';

export const API_URL = `http://${hostname}`;

export const API = {
  login: `${API_URL}/auth/login`,
  signup: `${API_URL}/auth/signup`,
  logout: `${API_URL}/auth/logout`,
  me: `${API_URL}/auth/me`,
  users: `${API_URL}/auth/users`,
  changePassword: `${API_URL}/auth/change-password`,
  deleteAccount: `${API_URL}/auth/account`,
  inviteUser: `${API_URL}/auth/invite-user`,
  updatePermissions: `${API_URL}/auth/update-permissions`,
  getRoles: `${API_URL}/auth/roles`,
  verifyPermission: `${API_URL}/auth/verify-permission`,
};

export const signup = async (
  full_name: string,
  email: string,
  password: string,
  confirmPassword: string,
  phoneNo?: string
): Promise<Response | Error> => {
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

export const login = async (email: string, password: string): Promise<any> => {
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
    })
  );
  return data;
};

export const forgotPassword = async (email: string): Promise<any> => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    throw new Error('Invalid email format');
  }
  return email;
  const response = await fetch(`${API_URL}/auth/login`, {//change to forgot password for util
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      email,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Forgot password failed');
  }

  const data = await response.json();

  return data;
};

export const logout = (): void => {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
};

export const getCurrentUser = (): any => {
  const user = localStorage.getItem('user');
  return user ? JSON.parse(user) : null;
};

export const isAuthenticated = (): boolean => {
  return !!localStorage.getItem('token');
};

export const getToken = (): string | null => {
  return localStorage.getItem('token');
};

// Helper function to make authenticated API calls
export const authFetch = async (url: string, options: RequestInit = {}): Promise<Response> => {
  const token = getToken();
  const headers = {
    ...options.headers,
    Authorization: `Bearer ${token}`,
  };

  return fetch(url, { ...options, headers });
};
