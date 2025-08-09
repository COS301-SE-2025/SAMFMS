/**
 * Centralized API management utility for dashboard widgets
 * Provides throttling, caching, and standardized error handling
 */

// Simple in-memory cache with TTL
class APICache {
  constructor() {
    this.cache = new Map();
    this.timers = new Map();
  }

  set(key, value, ttl = 30000) {
    // Clear existing timer if any
    if (this.timers.has(key)) {
      clearTimeout(this.timers.get(key));
    }

    this.cache.set(key, value);

    // Set expiration timer
    const timer = setTimeout(() => {
      this.cache.delete(key);
      this.timers.delete(key);
    }, ttl);

    this.timers.set(key, timer);
  }

  get(key) {
    return this.cache.get(key);
  }

  has(key) {
    return this.cache.has(key);
  }

  delete(key) {
    if (this.timers.has(key)) {
      clearTimeout(this.timers.get(key));
      this.timers.delete(key);
    }
    return this.cache.delete(key);
  }

  clear() {
    this.timers.forEach(timer => clearTimeout(timer));
    this.timers.clear();
    this.cache.clear();
  }
}

// Global API cache instance
const apiCache = new APICache();

// Request throttling utility
class RequestThrottler {
  constructor() {
    this.pendingRequests = new Map();
  }

  async throttleRequest(key, requestFn, delay = 1000) {
    // If there's already a pending request for this key, return it
    if (this.pendingRequests.has(key)) {
      return this.pendingRequests.get(key);
    }

    // Create new request promise
    const requestPromise = new Promise((resolve, reject) => {
      setTimeout(async () => {
        try {
          const result = await requestFn();
          resolve(result);
        } catch (error) {
          reject(error);
        } finally {
          this.pendingRequests.delete(key);
        }
      }, delay);
    });

    this.pendingRequests.set(key, requestPromise);
    return requestPromise;
  }
}

const requestThrottler = new RequestThrottler();

/**
 * Standardized API wrapper for widget data fetching
 * @param {string} cacheKey - Unique cache key for the request
 * @param {Function} apiCall - Function that makes the API call
 * @param {Object} options - Configuration options
 * @param {number} options.cacheTTL - Cache time-to-live in milliseconds
 * @param {number} options.throttleDelay - Throttle delay in milliseconds
 * @param {boolean} options.useCache - Whether to use caching
 * @param {boolean} options.useThrottle - Whether to use throttling
 * @returns {Promise} Promise that resolves with API data
 */
export const fetchWidgetData = async (cacheKey, apiCall, options = {}) => {
  const {
    cacheTTL = 30000, // 30 seconds default cache
    throttleDelay = 1000, // 1 second throttle
    useCache = true,
    useThrottle = true,
  } = options;

  try {
    // Check cache first
    if (useCache && apiCache.has(cacheKey)) {
      return apiCache.get(cacheKey);
    }

    // Make API call with optional throttling
    let result;
    if (useThrottle) {
      result = await requestThrottler.throttleRequest(cacheKey, apiCall, throttleDelay);
    } else {
      result = await apiCall();
    }

    // Validate and normalize the result
    const normalizedResult = normalizeAPIResponse(result);

    // Cache the result
    if (useCache) {
      apiCache.set(cacheKey, normalizedResult, cacheTTL);
    }

    return normalizedResult;
  } catch (error) {
    console.error(`API call failed for ${cacheKey}:`, error);

    // Return cached data if available, even if stale
    if (useCache && apiCache.has(cacheKey)) {
      console.warn(`Returning stale cached data for ${cacheKey}`);
      return apiCache.get(cacheKey);
    }

    // Rethrow error if no cached fallback
    throw new Error(`Failed to fetch data: ${error.message}`);
  }
};

/**
 * Normalize API response to ensure consistent data structure
 * @param {*} response - Raw API response
 * @returns {Object} Normalized response
 */
export const normalizeAPIResponse = response => {
  if (!response) {
    return { data: null, error: null, status: 'empty' };
  }

  // Handle different response formats
  if (response.data !== undefined) {
    return {
      data: response.data,
      error: response.error || null,
      status: response.status || 'success',
    };
  }

  // If response is direct data
  return {
    data: response,
    error: null,
    status: 'success',
  };
};

/**
 * Create a widget-specific data fetcher with retry logic
 * @param {string} widgetType - Type of widget (for cache key generation)
 * @param {Function} apiCall - API call function
 * @param {Object} defaultOptions - Default options for this widget type
 * @returns {Function} Widget data fetcher function
 */
export const createWidgetDataFetcher = (widgetType, apiCall, defaultOptions = {}) => {
  return async (widgetId, config = {}, options = {}) => {
    const finalOptions = { ...defaultOptions, ...options };
    const cacheKey = `${widgetType}_${widgetId}_${JSON.stringify(config)}`;

    // Retry logic
    const maxRetries = finalOptions.maxRetries || 3;
    let lastError;

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        return await fetchWidgetData(cacheKey, () => apiCall(config), finalOptions);
      } catch (error) {
        lastError = error;

        if (attempt < maxRetries) {
          // Exponential backoff
          const backoffDelay = Math.min(1000 * Math.pow(2, attempt - 1), 10000);
          await new Promise(resolve => setTimeout(resolve, backoffDelay));
        }
      }
    }

    throw lastError;
  };
};

/**
 * Preload data for multiple widgets
 * @param {Array} widgets - Array of widget configurations
 * @param {Object} fetchers - Map of widget type to fetcher functions
 */
export const preloadWidgetData = async (widgets, fetchers) => {
  const preloadPromises = widgets.map(async widget => {
    const fetcher = fetchers[widget.type];
    if (fetcher) {
      try {
        await fetcher(widget.id, widget.config, { useCache: true });
      } catch (error) {
        console.warn(`Failed to preload data for widget ${widget.id}:`, error);
      }
    }
  });

  await Promise.allSettled(preloadPromises);
};

/**
 * Clear cache for specific widget or all widgets
 * @param {string} widgetId - Optional widget ID to clear specific cache
 */
export const clearWidgetCache = (widgetId = null) => {
  if (widgetId) {
    // Clear cache entries that contain the widget ID
    for (const [key] of apiCache.cache.entries()) {
      if (key.includes(widgetId)) {
        apiCache.delete(key);
      }
    }
  } else {
    apiCache.clear();
  }
};

// Export cache instance for advanced usage
export { apiCache };
