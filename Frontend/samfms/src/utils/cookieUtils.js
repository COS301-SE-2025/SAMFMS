/**
 * Cookie utilities for dashboard layout persistence
 */

// Set a cookie with optional expiration days
export const setCookie = (name, value, days = 30) => {
  try {
    const expires = new Date();
    expires.setTime(expires.getTime() + days * 24 * 60 * 60 * 1000);

    // Compress the value if it's too large
    let cookieValue = value;
    if (typeof value === 'object') {
      cookieValue = JSON.stringify(value);
    }

    // Check if the cookie value is too large (browsers typically limit cookies to 4KB)
    if (cookieValue.length > 3900) {
      console.warn('Cookie value is large, consider using compression or splitting');
    }

    document.cookie = `${name}=${encodeURIComponent(
      cookieValue
    )}; expires=${expires.toUTCString()}; path=/; SameSite=Lax`;
    return true;
  } catch (error) {
    console.error('Failed to set cookie:', error);
    return false;
  }
};

// Get a cookie value
export const getCookie = name => {
  try {
    const nameEQ = name + '=';
    const ca = document.cookie.split(';');

    for (let i = 0; i < ca.length; i++) {
      let c = ca[i];
      while (c.charAt(0) === ' ') c = c.substring(1, c.length);
      if (c.indexOf(nameEQ) === 0) {
        const value = decodeURIComponent(c.substring(nameEQ.length, c.length));

        // Try to parse as JSON, return as string if it fails
        try {
          return JSON.parse(value);
        } catch {
          return value;
        }
      }
    }
    return null;
  } catch (error) {
    console.error('Failed to get cookie:', error);
    return null;
  }
};

// Delete a cookie
export const deleteCookie = name => {
  try {
    document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/`;
    return true;
  } catch (error) {
    console.error('Failed to delete cookie:', error);
    return false;
  }
};

// Check if cookies are enabled
export const areCookiesEnabled = () => {
  try {
    const testName = '__test_cookie__';
    setCookie(testName, 'test', 1);
    const enabled = getCookie(testName) === 'test';
    deleteCookie(testName);
    return enabled;
  } catch {
    return false;
  }
};

// Get all cookies as an object
export const getAllCookies = () => {
  try {
    const cookies = {};
    document.cookie.split(';').forEach(cookie => {
      const [name, ...rest] = cookie.split('=');
      if (name && rest.length > 0) {
        const value = rest.join('=');
        try {
          cookies[name.trim()] = JSON.parse(decodeURIComponent(value));
        } catch {
          cookies[name.trim()] = decodeURIComponent(value);
        }
      }
    });
    return cookies;
  } catch (error) {
    console.error('Failed to get all cookies:', error);
    return {};
  }
};

// Dashboard-specific utilities
export const DASHBOARD_COOKIE_PREFIX = 'samfms_dashboard_';

export const saveDashboardLayout = (dashboardId, layoutData) => {
  const cookieName = `${DASHBOARD_COOKIE_PREFIX}${dashboardId}`;

  // Prepare the data with timestamp
  const dashboardData = {
    ...layoutData,
    lastSaved: new Date().toISOString(),
    version: '1.0',
  };

  try {
    return setCookie(cookieName, dashboardData, 365); // Save for 1 year
  } catch (error) {
    console.error('Failed to save dashboard layout to cookies:', error);

    // Fallback to localStorage if cookies fail
    try {
      localStorage.setItem(cookieName, JSON.stringify(dashboardData));
      console.log('Dashboard saved to localStorage as fallback');
      return true;
    } catch (fallbackError) {
      console.error('Fallback to localStorage also failed:', fallbackError);
      return false;
    }
  }
};

export const loadDashboardLayout = dashboardId => {
  const cookieName = `${DASHBOARD_COOKIE_PREFIX}${dashboardId}`;

  try {
    // Try to load from cookies first
    let data = getCookie(cookieName);

    // Fallback to localStorage if cookie doesn't exist
    if (!data) {
      const localStorageData = localStorage.getItem(cookieName);
      if (localStorageData) {
        data = JSON.parse(localStorageData);
        console.log('Dashboard loaded from localStorage fallback');
      }
    }

    // Validate the data structure
    if (data && typeof data === 'object') {
      // Check if data has required properties
      if (Array.isArray(data.widgets) && Array.isArray(data.layout)) {
        return data;
      } else if (data.widgets || data.layout) {
        console.warn('Dashboard data structure is incomplete:', data);
      }
    }

    return null;
  } catch (error) {
    console.error('Failed to load dashboard layout from cookies:', error);
    return null;
  }
};

export const deleteDashboardLayout = dashboardId => {
  const cookieName = `${DASHBOARD_COOKIE_PREFIX}${dashboardId}`;

  try {
    // Delete from both cookies and localStorage
    deleteCookie(cookieName);
    localStorage.removeItem(cookieName);
    return true;
  } catch (error) {
    console.error('Failed to delete dashboard layout:', error);
    return false;
  }
};

// Utility to migrate from localStorage to cookies
export const migrateDashboardTocookies = dashboardId => {
  const localStorageKey = `dashboard_${dashboardId}`;

  try {
    const localStorageData = localStorage.getItem(localStorageKey);
    if (localStorageData) {
      const data = JSON.parse(localStorageData);
      const success = saveDashboardLayout(dashboardId, data);

      if (success) {
        // Remove from localStorage after successful migration
        localStorage.removeItem(localStorageKey);
        console.log(`Dashboard ${dashboardId} migrated from localStorage to cookies`);
        return true;
      }
    }
    return false;
  } catch (error) {
    console.error('Failed to migrate dashboard to cookies:', error);
    return false;
  }
};
