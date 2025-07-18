/**
 * Authentication API Tests
 * Tests for auth.js API functions
 */
import { 
  login, 
  signup, 
  logout, 
  refreshAuthToken, 
  getCurrentUser, 
  getToken, 
  isAuthenticated,
  authFetch,
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
  updateUserProfile,
  uploadProfilePicture,
  AUTH_API
} from '../../backend/api/auth';
import { getCookie, setCookie, eraseCookie } from '../../lib/cookies';

// Mock the cookies module
jest.mock('../../lib/cookies');

describe('Authentication API', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    global.fetch.mockClear();
  });

  describe('Auth Endpoints', () => {
    test('should have correct API endpoints', () => {
      expect(AUTH_API.login).toContain('/auth/login');
      expect(AUTH_API.signup).toContain('/auth/register');
      expect(AUTH_API.logout).toContain('/auth/logout');
      expect(AUTH_API.refreshToken).toContain('/auth/refresh');
      expect(AUTH_API.me).toContain('/auth/me');
      expect(AUTH_API.users).toContain('/auth/users');
      expect(AUTH_API.changePassword).toContain('/auth/change-password');
      expect(AUTH_API.deleteAccount).toContain('/auth/account');
      expect(AUTH_API.updatePreferences).toContain('/auth/update-preferences');
      expect(AUTH_API.inviteUser).toContain('/auth/invite-user');
    });
  });

  describe('Token Management', () => {
    test('getToken should return token from cookies', () => {
      getCookie.mockReturnValue('mock-token');
      expect(getToken()).toBe('mock-token');
      expect(getCookie).toHaveBeenCalledWith('token');
    });

    test('getCurrentUser should return user from cookies', () => {
      const mockUser = { id: 1, email: 'test@example.com' };
      getCookie.mockImplementation((key) => {
        if (key === 'user') return JSON.stringify(mockUser);
        if (key === 'permissions') return JSON.stringify(['read', 'write']);
        if (key === 'preferences') return JSON.stringify({ theme: 'dark' });
        return null;
      });

      const user = getCurrentUser();
      expect(user).toEqual(mockUser);
      expect(getCookie).toHaveBeenCalledWith('user');
    });

    test('getCurrentUser should return null if no user in cookies', () => {
      getCookie.mockReturnValue(null);
      expect(getCurrentUser()).toBeNull();
    });

    test('isAuthenticated should return true if token exists', () => {
      getCookie.mockReturnValue('mock-token');
      expect(isAuthenticated()).toBe(true);
    });

    test('isAuthenticated should return false if no token', () => {
      getCookie.mockReturnValue(null);
      expect(isAuthenticated()).toBe(false);
    });
  });

  describe('Login', () => {
    test('should successfully login with valid credentials', async () => {
      const mockResponse = {
        success: true,
        data: {
          user: { id: 1, email: 'test@example.com' },
          token: 'mock-token',
          permissions: ['read', 'write'],
          preferences: { theme: 'dark' }
        }
      };

      global.mockFetch(mockResponse);

      const credentials = { email: 'test@example.com', password: 'password' };
      const result = await login(credentials);

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/login'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
          body: JSON.stringify(credentials),
        })
      );

      expect(result).toEqual(mockResponse);
      expect(setCookie).toHaveBeenCalledWith('token', 'mock-token');
      expect(setCookie).toHaveBeenCalledWith('user', JSON.stringify(mockResponse.data.user));
    });

    test('should handle login failure', async () => {
      const mockError = new Error('Invalid credentials');
      global.mockFetchError(mockError);

      const credentials = { email: 'test@example.com', password: 'wrong-password' };
      
      await expect(login(credentials)).rejects.toThrow('Invalid credentials');
    });
  });

  describe('Signup', () => {
    test('should successfully signup with valid data', async () => {
      const mockResponse = {
        success: true,
        data: {
          user: { id: 1, email: 'test@example.com' },
          token: 'mock-token'
        }
      };

      global.mockFetch(mockResponse);

      const signupData = {
        email: 'test@example.com',
        password: 'password',
        firstName: 'Test',
        lastName: 'User'
      };

      const result = await signup(signupData);

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/register'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
          body: JSON.stringify(signupData),
        })
      );

      expect(result).toEqual(mockResponse);
    });

    test('should handle signup failure', async () => {
      const mockError = new Error('Email already exists');
      global.mockFetchError(mockError);

      const signupData = {
        email: 'existing@example.com',
        password: 'password',
        firstName: 'Test',
        lastName: 'User'
      };

      await expect(signup(signupData)).rejects.toThrow('Email already exists');
    });
  });

  describe('Logout', () => {
    test('should successfully logout', async () => {
      const mockResponse = { success: true };
      global.mockFetch(mockResponse);
      getCookie.mockReturnValue('mock-token');

      const result = await logout();

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/logout'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Authorization': 'Bearer mock-token',
          }),
        })
      );

      expect(result).toEqual(mockResponse);
      expect(eraseCookie).toHaveBeenCalledWith('token');
      expect(eraseCookie).toHaveBeenCalledWith('user');
    });
  });

  describe('Authenticated Fetch', () => {
    test('should make authenticated request with token', async () => {
      const mockResponse = { data: 'test' };
      global.mockFetch(mockResponse);
      getCookie.mockReturnValue('mock-token');

      const result = await authFetch('/api/test');

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/test'),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer mock-token',
          }),
        })
      );

      expect(result).toEqual(mockResponse);
    });

    test('should handle request without token', async () => {
      getCookie.mockReturnValue(null);

      await expect(authFetch('/api/test')).rejects.toThrow('No authentication token found');
    });
  });

  describe('Password Change', () => {
    test('should successfully change password', async () => {
      const mockResponse = { success: true };
      global.mockFetch(mockResponse);
      getCookie.mockReturnValue('mock-token');

      const passwordData = {
        currentPassword: 'old-password',
        newPassword: 'new-password'
      };

      const result = await changePassword(passwordData);

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/change-password'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'Authorization': 'Bearer mock-token',
          }),
          body: JSON.stringify(passwordData),
        })
      );

      expect(result).toEqual(mockResponse);
    });
  });

  describe('User Management', () => {
    test('should list users successfully', async () => {
      const mockResponse = {
        success: true,
        data: [
          { id: 1, email: 'user1@example.com' },
          { id: 2, email: 'user2@example.com' }
        ]
      };

      global.mockFetch(mockResponse);
      getCookie.mockReturnValue('mock-token');

      const result = await listUsers();

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/users'),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer mock-token',
          }),
        })
      );

      expect(result).toEqual(mockResponse);
    });

    test('should create user manually', async () => {
      const mockResponse = {
        success: true,
        data: { id: 1, email: 'new@example.com' }
      };

      global.mockFetch(mockResponse);
      getCookie.mockReturnValue('mock-token');

      const userData = {
        email: 'new@example.com',
        firstName: 'New',
        lastName: 'User',
        role: 'user'
      };

      const result = await createUserManually(userData);

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/create-user'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'Authorization': 'Bearer mock-token',
          }),
          body: JSON.stringify(userData),
        })
      );

      expect(result).toEqual(mockResponse);
    });

    test('should check user existence', async () => {
      const mockResponse = { exists: true };
      global.mockFetch(mockResponse);

      const result = await checkUserExistence('test@example.com');

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/user-exists?email=test@example.com'),
        expect.objectContaining({
          method: 'GET',
        })
      );

      expect(result).toEqual(mockResponse);
    });
  });

  describe('Permissions and Roles', () => {
    test('should get roles successfully', async () => {
      const mockResponse = {
        success: true,
        data: ['admin', 'user', 'manager']
      };

      global.mockFetch(mockResponse);
      getCookie.mockReturnValue('mock-token');

      const result = await getRoles();

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/roles'),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer mock-token',
          }),
        })
      );

      expect(result).toEqual(mockResponse);
    });

    test('should verify permission', async () => {
      const mockResponse = { hasPermission: true };
      global.mockFetch(mockResponse);
      getCookie.mockReturnValue('mock-token');

      const result = await verifyPermission('read', 'vehicles');

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/verify-permission'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'Authorization': 'Bearer mock-token',
          }),
          body: JSON.stringify({ permission: 'read', resource: 'vehicles' }),
        })
      );

      expect(result).toEqual(mockResponse);
    });

    test('hasPermission should return boolean', () => {
      getCookie.mockImplementation((key) => {
        if (key === 'permissions') return JSON.stringify(['read', 'write']);
        return null;
      });

      expect(hasPermission('read')).toBe(true);
      expect(hasPermission('delete')).toBe(false);
    });

    test('hasRole should return boolean', () => {
      getCookie.mockImplementation((key) => {
        if (key === 'user') return JSON.stringify({ roles: ['admin', 'user'] });
        return null;
      });

      expect(hasRole('admin')).toBe(true);
      expect(hasRole('manager')).toBe(false);
    });

    test('hasAnyRole should return boolean', () => {
      getCookie.mockImplementation((key) => {
        if (key === 'user') return JSON.stringify({ roles: ['admin', 'user'] });
        return null;
      });

      expect(hasAnyRole(['admin', 'manager'])).toBe(true);
      expect(hasAnyRole(['manager', 'supervisor'])).toBe(false);
    });
  });

  describe('Profile Management', () => {
    test('should update user profile', async () => {
      const mockResponse = {
        success: true,
        data: { id: 1, firstName: 'Updated', lastName: 'User' }
      };

      global.mockFetch(mockResponse);
      getCookie.mockReturnValue('mock-token');

      const profileData = {
        firstName: 'Updated',
        lastName: 'User'
      };

      const result = await updateUserProfile(profileData);

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/profile'),
        expect.objectContaining({
          method: 'PUT',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'Authorization': 'Bearer mock-token',
          }),
          body: JSON.stringify(profileData),
        })
      );

      expect(result).toEqual(mockResponse);
    });

    test('should upload profile picture', async () => {
      const mockResponse = {
        success: true,
        data: { profilePictureUrl: 'https://example.com/picture.jpg' }
      };

      global.mockFetch(mockResponse);
      getCookie.mockReturnValue('mock-token');

      const formData = new FormData();
      formData.append('file', new Blob(['test'], { type: 'image/jpeg' }));

      const result = await uploadProfilePicture(formData);

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/upload-picture'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Authorization': 'Bearer mock-token',
          }),
          body: formData,
        })
      );

      expect(result).toEqual(mockResponse);
    });
  });

  describe('Token Refresh', () => {
    test('should refresh authentication token', async () => {
      const mockResponse = {
        success: true,
        data: { token: 'new-token' }
      };

      global.mockFetch(mockResponse);
      getCookie.mockReturnValue('old-token');

      const result = await refreshAuthToken();

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/refresh'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Authorization': 'Bearer old-token',
          }),
        })
      );

      expect(result).toEqual(mockResponse);
      expect(setCookie).toHaveBeenCalledWith('token', 'new-token');
    });
  });
});
