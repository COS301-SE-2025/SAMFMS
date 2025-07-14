/**
 * Centralized Error Handling Service
 * Provides standardized error handling and processing across the application
 */

/**
 * Custom API Error class with additional context
 */
export class ApiError extends Error {
  constructor(message, status, statusText, errorData = {}) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.statusText = statusText;
    this.errorData = errorData;
    this.timestamp = new Date().toISOString();
  }

  /**
   * Check if this is a client error (4xx)
   */
  isClientError() {
    return this.status >= 400 && this.status < 500;
  }

  /**
   * Check if this is a server error (5xx)
   */
  isServerError() {
    return this.status >= 500;
  }

  /**
   * Check if this is a network error
   */
  isNetworkError() {
    return this.status === 0 || this.message.includes('network') || this.message.includes('fetch');
  }

  /**
   * Get user-friendly error message
   */
  getUserMessage() {
    if (this.isNetworkError()) {
      return 'Network connection error. Please check your internet connection.';
    }

    if (this.status === 401) {
      return 'Authentication required. Please log in again.';
    }

    if (this.status === 403) {
      return 'You do not have permission to perform this action.';
    }

    if (this.status === 404) {
      return 'The requested resource was not found.';
    }

    if (this.status === 429) {
      return 'Too many requests. Please try again later.';
    }

    if (this.isServerError()) {
      return 'Server error occurred. Please try again later.';
    }

    return this.message || 'An error occurred. Please try again.';
  }

  /**
   * Convert to plain object for logging
   */
  toJSON() {
    return {
      name: this.name,
      message: this.message,
      status: this.status,
      statusText: this.statusText,
      errorData: this.errorData,
      timestamp: this.timestamp,
      stack: this.stack,
    };
  }
}

/**
 * Check if error indicates token expiration
 */
export const isTokenExpiredError = error => {
  return (
    (error instanceof ApiError && error.status === 401) ||
    (error.message &&
      (error.message.includes('401') ||
        error.message.includes('Unauthorized') ||
        error.message.includes('Token expired') ||
        error.message.includes('Invalid token')))
  );
};

/**
 * Check if error is retryable (network/timeout errors)
 */
export const isRetryableError = error => {
  if (error instanceof ApiError) {
    return error.isNetworkError() || error.isServerError();
  }

  return (
    error.message &&
    (error.message.includes('timeout') ||
      error.message.includes('network') ||
      error.message.includes('fetch') ||
      error.message.includes('ECONNREFUSED') ||
      error.message.includes('ETIMEDOUT'))
  );
};

/**
 * Process API response and handle errors
 */
export const handleApiResponse = async response => {
  if (!response.ok) {
    const contentType = response.headers.get('content-type');
    let errorData = {};

    try {
      if (contentType && contentType.includes('application/json')) {
        errorData = await response.json();
      } else {
        const text = await response.text();
        errorData = { message: text || 'Unknown error occurred' };
      }
    } catch (parseError) {
      errorData = { message: 'Failed to parse error response' };
    }

    throw new ApiError(
      errorData.detail || errorData.message || 'Request failed',
      response.status,
      response.statusText,
      errorData
    );
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
};

/**
 * Log error with context for debugging
 */
export const logError = (error, context = {}) => {
  const errorInfo = {
    error:
      error instanceof ApiError
        ? error.toJSON()
        : {
            name: error.name,
            message: error.message,
            stack: error.stack,
          },
    context,
    timestamp: new Date().toISOString(),
  };

  if (process.env.NODE_ENV === 'development') {
    console.error('API Error:', errorInfo);
  }

  // In production, you might want to send this to a logging service
  // Example: logToService(errorInfo);

  return errorInfo;
};

/**
 * Create standardized error response for UI components
 */
export const createErrorResponse = (error, context = {}) => {
  logError(error, context);

  const apiError = error instanceof ApiError ? error : new ApiError(error.message);

  return {
    success: false,
    error: {
      message: apiError.getUserMessage(),
      code: apiError.status,
      details: apiError.errorData,
      isRetryable: isRetryableError(apiError),
    },
    timestamp: new Date().toISOString(),
  };
};

/**
 * Validation error class for client-side validation
 */
export class ValidationError extends Error {
  constructor(message, field, errors = {}) {
    super(message);
    this.name = 'ValidationError';
    this.field = field;
    this.errors = errors;
  }
}

/**
 * Network error class for connection issues
 */
export class NetworkError extends ApiError {
  constructor(message = 'Network connection error') {
    super(message, 0, 'Network Error');
    this.name = 'NetworkError';
  }
}

/**
 * Timeout error class for request timeouts
 */
export class TimeoutError extends ApiError {
  constructor(message = 'Request timeout', timeout = 30000) {
    super(message, 0, 'Timeout');
    this.name = 'TimeoutError';
    this.timeout = timeout;
  }
}
