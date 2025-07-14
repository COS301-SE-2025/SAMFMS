/**
 * Centralized HTTP Client for SAMFMS Frontend
 * Handles all API requests with automatic token management, retry logic, and error handling
 */
import { getToken, refreshAuthToken, logout } from '../api/auth';
import { buildApiUrl, API_CONFIG } from '../../config/apiConfig';

export class ApiError extends Error {
  constructor(message, status, statusText, errorData) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.statusText = statusText;
    this.errorData = errorData;
  }
}

class HttpClient {
  constructor() {
    this.defaultTimeout = API_CONFIG.timeout || 30000;
    this.maxRetries = API_CONFIG.retries || 3;
  }

  /**
   * Check if error indicates token expiration
   */
  isTokenExpiredError(error) {
    return (
      error.status === 401 ||
      error.message.includes('401') ||
      error.message.includes('Unauthorized') ||
      error.message.includes('Token expired') ||
      error.message.includes('Invalid token')
    );
  }

  /**
   * Handle API response and errors
   */
  async handleResponse(response) {
    if (!response.ok) {
      const contentType = response.headers.get('content-type');
      let errorData = {};

      try {
        if (contentType && contentType.includes('application/json')) {
          errorData = await response.json();
        } else {
          errorData = { message: (await response.text()) || 'Unknown error occurred' };
        }
      } catch (parseError) {
        errorData = { message: 'Failed to parse error response' };
      }

      const error = new ApiError(
        errorData.detail || errorData.message || 'Request failed',
        response.status,
        response.statusText,
        errorData
      );

      throw error;
    }

    // Handle successful responses
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return await response.json();
    }

    // For non-JSON responses (like DELETE operations)
    try {
      const text = await response.text();
      return text ? JSON.parse(text) : { success: true };
    } catch (e) {
      return { success: true };
    }
  }

  /**
   * Create fetch request with timeout
   */
  async fetchWithTimeout(url, options = {}, timeout = this.defaultTimeout) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      return response;
    } catch (error) {
      clearTimeout(timeoutId);
      if (error.name === 'AbortError') {
        throw new Error('Request timeout');
      }
      throw error;
    }
  }

  /**
   * Main request method with automatic token refresh and retry logic
   */
  async request(endpoint, options = {}, maxRetries = this.maxRetries) {
    let retries = 0;
    const url = endpoint.startsWith('http') ? endpoint : buildApiUrl(endpoint);

    while (retries <= maxRetries) {
      try {
        const token = getToken();
        
        // Prepare headers
        const headers = {
          'Content-Type': 'application/json',
          ...options.headers,
        };

        // Add authorization header if token exists
        if (token) {
          headers.Authorization = `Bearer ${token}`;
        }

        const requestOptions = {
          ...options,
          headers,
        };

        const response = await this.fetchWithTimeout(url, requestOptions);
        return await this.handleResponse(response);

      } catch (error) {
        // Check if error is due to token expiration
        if (this.isTokenExpiredError(error)) {
          if (retries < maxRetries) {
            try {
              // Attempt to refresh token
              await refreshAuthToken();
              retries++;
              continue; // Retry the request
            } catch (refreshError) {
              // Token refresh failed, redirect to login
              console.error('Token refresh failed:', refreshError);
              logout();
              throw new ApiError('Session expired. Please log in again.', 401, 'Unauthorized');
            }
          }
        }

        // For non-token errors, only retry on network/timeout errors
        if (retries < maxRetries && (
          error.message.includes('timeout') ||
          error.message.includes('network') ||
          error.message.includes('fetch')
        )) {
          retries++;
          // Add exponential backoff
          await new Promise(resolve => setTimeout(resolve, 1000 * retries));
          continue;
        }

        // Re-throw the error if retries exceeded or not retryable
        throw error;
      }
    }
  }

  /**
   * HTTP GET method
   */
  async get(endpoint, options = {}) {
    return this.request(endpoint, { ...options, method: 'GET' });
  }

  /**
   * HTTP POST method
   */
  async post(endpoint, data, options = {}) {
    return this.request(endpoint, {
      ...options,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  /**
   * HTTP PUT method
   */
  async put(endpoint, data, options = {}) {
    return this.request(endpoint, {
      ...options,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  /**
   * HTTP DELETE method
   */
  async delete(endpoint, options = {}) {
    return this.request(endpoint, { ...options, method: 'DELETE' });
  }

  /**
   * HTTP PATCH method
   */
  async patch(endpoint, data, options = {}) {
    return this.request(endpoint, {
      ...options,
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    });
  }
}

// Export singleton instance
export const httpClient = new HttpClient();

// Export class for testing or custom instances
export { HttpClient };
