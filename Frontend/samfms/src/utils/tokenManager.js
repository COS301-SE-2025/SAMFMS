import {getToken} from '../backend/api/auth';
import {getCookie, setCookie, deleteCookie} from '../lib/cookies';

// Token refresh configuration
const TOKEN_REFRESH_BUFFER = 2 * 60 * 1000; // 2 minutes before expiry
const API_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:21004';

class TokenManager {
  constructor() {
    this.refreshTimer = null;
    this.isRefreshing = false;
    this.failedRefreshCount = 0;
    this.maxRefreshAttempts = 3;
  }

  /**
   * Start automatic token refresh
   */
  startTokenRefresh() {
    this.stopTokenRefresh(); // Clear any existing timer

    const token = getToken();
    if (!token) {
      return;
    }

    try {
      // Decode token to get expiry time
      const payload = JSON.parse(atob(token.split('.')[1]));
      const expiryTime = payload.exp * 1000; // Convert to milliseconds
      const currentTime = Date.now();
      const timeUntilRefresh = expiryTime - currentTime - TOKEN_REFRESH_BUFFER;

      if (timeUntilRefresh > 0) {
        this.refreshTimer = setTimeout(() => {
          this.refreshToken();
        }, timeUntilRefresh);

        console.log(`Token refresh scheduled in ${Math.round(timeUntilRefresh / 1000)} seconds`);
      } else {
        // Token is already close to expiry or expired
        this.refreshToken();
      }
    } catch (error) {
      console.error('Failed to schedule token refresh:', error);
    }
  }

  /**
   * Stop automatic token refresh
   */
  stopTokenRefresh() {
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
      this.refreshTimer = null;
    }
  }

  /**
   * Refresh the access token using refresh token
   */
  async refreshToken() {
    if (this.isRefreshing) {
      return;
    }

    this.isRefreshing = true;

    try {
      const refreshToken = getCookie('refresh_token');
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      const response = await fetch(`${API_URL}/auth/refresh-token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${refreshToken}`,
        },
      });

      if (response.ok) {
        const data = await response.json();

        // Update tokens
        setCookie('token', data.access_token, 1 / 96); // 15 minutes
        if (data.refresh_token) {
          setCookie('refresh_token', data.refresh_token, 7); // 7 days
        }

        // Reset failure count
        this.failedRefreshCount = 0;

        // Schedule next refresh
        this.startTokenRefresh();

        console.log('Token refreshed successfully');

        // Dispatch custom event for other components to react
        window.dispatchEvent(
          new CustomEvent('tokenRefreshed', {
            detail: {access_token: data.access_token},
          })
        );
      } else {
        throw new Error('Token refresh failed');
      }
    } catch (error) {
      console.error('Token refresh failed:', error);
      this.failedRefreshCount++;

      if (this.failedRefreshCount >= this.maxRefreshAttempts) {
        // Too many failed attempts, force logout
        this.handleRefreshFailure();
      } else {
        // Retry after a delay
        setTimeout(() => {
          this.refreshToken();
        }, 5000 * this.failedRefreshCount); // Exponential backoff
      }
    } finally {
      this.isRefreshing = false;
    }
  }

  /**
   * Handle refresh failure by forcing logout
   */
  handleRefreshFailure() {
    console.log('Token refresh failed multiple times, forcing logout'); // Clear all auth data
    deleteCookie('token');
    deleteCookie('refresh_token');
    deleteCookie('user');
    deleteCookie('permissions');
    deleteCookie('preferences');

    // Stop refresh timer
    this.stopTokenRefresh();

    // Dispatch logout event
    window.dispatchEvent(
      new CustomEvent('authLogout', {
        detail: {reason: 'token_refresh_failed'},
      })
    );

    // Redirect to login
    window.location.href = '/';
  }

  /**
   * Check if token needs refresh
   */
  shouldRefreshToken() {
    const token = getToken();
    if (!token) {
      return false;
    }

    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const expiryTime = payload.exp * 1000;
      const currentTime = Date.now();
      return expiryTime - currentTime <= TOKEN_REFRESH_BUFFER;
    } catch (error) {
      console.error('Error checking token expiry:', error);
      return false;
    }
  }

  /**
   * Get time until token expiry
   */
  getTimeUntilExpiry() {
    const token = getToken();
    if (!token) {
      return 0;
    }

    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const expiryTime = payload.exp * 1000;
      const currentTime = Date.now();
      return Math.max(0, expiryTime - currentTime);
    } catch (error) {
      console.error('Error getting token expiry time:', error);
      return 0;
    }
  }
}

// Singleton instance
const tokenManager = new TokenManager();

export default tokenManager;

// Utility functions for external use
export const startTokenRefresh = () => tokenManager.startTokenRefresh();
export const stopTokenRefresh = () => tokenManager.stopTokenRefresh();
export const refreshToken = () => tokenManager.refreshToken();
export const shouldRefreshToken = () => tokenManager.shouldRefreshToken();
export const getTimeUntilExpiry = () => tokenManager.getTimeUntilExpiry();
