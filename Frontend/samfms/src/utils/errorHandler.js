/**
 * Centralized Error Handling Utility for SAMFMS Frontend
 * Provides consistent error handling, retry logic, and user-friendly error messages
 */

// Standard error types
export const ERROR_TYPES = {
  NETWORK: 'NETWORK_ERROR',
  AUTH: 'AUTHENTICATION_ERROR',
  VALIDATION: 'VALIDATION_ERROR',
  NOT_FOUND: 'NOT_FOUND',
  SERVER: 'SERVER_ERROR',
  TIMEOUT: 'TIMEOUT_ERROR',
  UNKNOWN: 'UNKNOWN_ERROR',
};

// Default retry configuration
const DEFAULT_RETRY_CONFIG = {
  maxRetries: 3,
  retryDelay: 1000,
  retryMultiplier: 2,
  retryableErrors: [408, 429, 500, 502, 503, 504],
};

/**
 * Enhanced API error class with retry capabilities
 */
export class ApiError extends Error {
  constructor(message, status, code, details = null, retryable = false) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.details = details;
    this.retryable = retryable;
    this.timestamp = new Date().toISOString();
  }

  /**
   * Get user-friendly error message
   */
  getUserMessage() {
    const userMessages = {
      400: 'Invalid request. Please check your input and try again.',
      401: 'Authentication required. Please log in.',
      403: "Access denied. You don't have permission for this action.",
      404: 'The requested resource was not found.',
      408: 'Request timeout. Please try again.',
      429: 'Too many requests. Please wait and try again.',
      500: 'Server error. Please try again later.',
      502: 'Service temporarily unavailable. Please try again.',
      503: 'Service temporarily unavailable. Please try again.',
      504: 'Request timeout. Please try again.',
    };

    return userMessages[this.status] || this.message || 'An unexpected error occurred.';
  }

  /**
   * Check if error is retryable
   */
  isRetryable() {
    return this.retryable || DEFAULT_RETRY_CONFIG.retryableErrors.includes(this.status);
  }
}

/**
 * Parse and standardize error from API response
 */
export const parseApiError = error => {
  // Handle network errors
  if (!error.response) {
    return new ApiError(
      'Network error. Please check your connection.',
      0,
      ERROR_TYPES.NETWORK,
      { originalError: error.message },
      true
    );
  }

  const { status, data } = error.response;
  let message, code, details;

  // Parse error response format
  if (data && typeof data === 'object') {
    message = data.message || data.error || data.detail || 'An error occurred';
    code = data.error_code || data.code || _getErrorTypeFromStatus(status);
    details = data.details || data.errors || null;
  } else {
    message = typeof data === 'string' ? data : 'An error occurred';
    code = _getErrorTypeFromStatus(status);
    details = null;
  }

  const retryable = DEFAULT_RETRY_CONFIG.retryableErrors.includes(status);

  return new ApiError(message, status, code, details, retryable);
};

/**
 * Get error type from HTTP status code
 */
const _getErrorTypeFromStatus = status => {
  if (status >= 400 && status < 500) {
    if (status === 401) return ERROR_TYPES.AUTH;
    if (status === 404) return ERROR_TYPES.NOT_FOUND;
    if (status === 422) return ERROR_TYPES.VALIDATION;
    return ERROR_TYPES.VALIDATION;
  }
  if (status >= 500) return ERROR_TYPES.SERVER;
  if (status === 408) return ERROR_TYPES.TIMEOUT;
  return ERROR_TYPES.UNKNOWN;
};

/**
 * Retry wrapper for API calls
 */
export const withRetry = async (apiCall, retryConfig = {}) => {
  const config = { ...DEFAULT_RETRY_CONFIG, ...retryConfig };
  let lastError;

  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    try {
      const result = await apiCall();
      return result;
    } catch (error) {
      lastError = error instanceof ApiError ? error : parseApiError(error);

      // Don't retry if not retryable or on last attempt
      if (!lastError.isRetryable() || attempt === config.maxRetries) {
        throw lastError;
      }

      // Calculate delay for next retry
      const delay = config.retryDelay * Math.pow(config.retryMultiplier, attempt);
      console.warn(
        `API call failed (attempt ${attempt + 1}/${
          config.maxRetries + 1
        }). Retrying in ${delay}ms...`,
        lastError
      );

      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }

  throw lastError;
};

/**
 * Enhanced error handler for API responses
 */
export const handleApiResponse = response => {
  // Handle both direct data and wrapped responses
  if (response?.data) {
    // Check if response indicates success
    if (response.data.success === false) {
      throw new ApiError(
        response.data.message || 'Request failed',
        response.status || 400,
        response.data.error_code || ERROR_TYPES.SERVER,
        response.data.details
      );
    }
    return response.data;
  }
  return response;
};

/**
 * Global error boundary for unhandled errors
 */
export const handleGlobalError = (error, context = 'Unknown') => {
  const apiError = error instanceof ApiError ? error : parseApiError(error);

  console.error(`[${context}] Error:`, {
    message: apiError.message,
    status: apiError.status,
    code: apiError.code,
    details: apiError.details,
    timestamp: apiError.timestamp,
  });

  // You can integrate with error reporting service here
  // reportErrorToService(apiError, context);

  return apiError;
};

/**
 * Create standard error response for consistent handling
 */
export const createErrorResponse = (message, code = ERROR_TYPES.UNKNOWN, details = null) => {
  return {
    success: false,
    message,
    error_code: code,
    details,
    timestamp: new Date().toISOString(),
  };
};

/**
 * Validation helper for required fields
 */
export const validateRequiredFields = (data, requiredFields) => {
  if (!data || typeof data !== 'object') {
    throw new ApiError('Invalid data provided', 400, ERROR_TYPES.VALIDATION, {
      required: requiredFields,
    });
  }

  const missingFields = requiredFields.filter(
    field => data[field] === undefined || data[field] === null || data[field] === ''
  );

  if (missingFields.length > 0) {
    throw new ApiError(
      `Missing required fields: ${missingFields.join(', ')}`,
      400,
      ERROR_TYPES.VALIDATION,
      { missing: missingFields, required: requiredFields }
    );
  }
};

/**
 * Format error for user display
 */
export const formatErrorForUser = error => {
  const apiError = error instanceof ApiError ? error : parseApiError(error);

  return {
    message: apiError.getUserMessage(),
    type: apiError.code,
    canRetry: apiError.isRetryable(),
    details: apiError.details,
  };
};

export default {
  ApiError,
  parseApiError,
  withRetry,
  handleApiResponse,
  handleGlobalError,
  createErrorResponse,
  validateRequiredFields,
  formatErrorForUser,
  ERROR_TYPES,
};
