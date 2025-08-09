import React, { Suspense, lazy } from 'react';

/**
 * Lazy loading utility for dashboard widgets
 * Provides code splitting and dynamic loading capabilities
 */

// Cache for lazy-loaded components
const lazyComponentCache = new Map();

/**
 * Create a lazy-loaded widget component with error boundaries
 * @param {Function} importFn - Dynamic import function
 * @param {string} widgetName - Name of the widget for debugging
 * @returns {React.Component} Lazy-loaded component
 */
export const createLazyWidget = (importFn, widgetName = 'Unknown Widget') => {
  // Check cache first
  if (lazyComponentCache.has(importFn)) {
    return lazyComponentCache.get(importFn);
  }

  const LazyComponent = lazy(() =>
    importFn().catch(error => {
      console.error(`Failed to load widget ${widgetName}:`, error);
      // Return a fallback component instead of crashing
      return {
        default: ({ id, config }) => (
          <div className="bg-card border border-border rounded-lg p-4 h-full flex items-center justify-center">
            <div className="text-center">
              <div className="text-destructive mb-2">⚠️</div>
              <p className="text-sm text-destructive">Failed to load widget</p>
              <p className="text-xs text-muted-foreground mt-1">{widgetName}</p>
            </div>
          </div>
        ),
      };
    })
  );

  // Add display name for debugging
  LazyComponent.displayName = `Lazy(${widgetName})`;

  // Cache the component
  lazyComponentCache.set(importFn, LazyComponent);

  return LazyComponent;
};

/**
 * Widget loading fallback component
 * @param {Object} props - Component props
 * @param {string} props.widgetName - Name of the widget being loaded
 */
export const WidgetLoadingFallback = ({ widgetName = 'Widget' }) => (
  <div className="bg-card border border-border rounded-lg shadow-sm overflow-hidden h-full flex flex-col">
    <div className="flex items-center justify-between p-3 border-b border-border bg-card/50 flex-shrink-0">
      <h3 className="font-medium text-card-foreground truncate">Loading {widgetName}...</h3>
    </div>
    <div className="p-4 flex items-center justify-center flex-grow">
      <div
        className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"
        aria-hidden="true"
      ></div>
      <span className="ml-3 text-muted-foreground">Loading widget...</span>
    </div>
  </div>
);

/**
 * HOC that wraps a widget with lazy loading and suspense
 * @param {Function} importFn - Dynamic import function
 * @param {Object} options - Configuration options
 * @param {string} options.widgetName - Name of the widget
 * @param {React.Component} options.fallback - Custom fallback component
 * @returns {React.Component} Wrapped component
 */
export const withLazyLoading = (importFn, options = {}) => {
  const { widgetName = 'Widget', fallback } = options;
  const LazyWidget = createLazyWidget(importFn, widgetName);

  return props => (
    <Suspense fallback={fallback || <WidgetLoadingFallback widgetName={widgetName} />}>
      <LazyWidget {...props} />
    </Suspense>
  );
};

/**
 * Preload a widget component for better perceived performance
 * @param {Function} importFn - Dynamic import function
 * @returns {Promise} Promise that resolves when component is loaded
 */
export const preloadWidget = async importFn => {
  try {
    await importFn();
    console.log('Widget preloaded successfully');
  } catch (error) {
    console.warn('Widget preload failed:', error);
  }
};

/**
 * Preload multiple widgets in batches to avoid overwhelming the browser
 * @param {Array} importFunctions - Array of import functions
 * @param {number} batchSize - Number of widgets to load per batch
 * @param {number} delay - Delay between batches in milliseconds
 * @returns {Promise} Promise that resolves when all widgets are loaded
 */
export const preloadWidgetBatch = async (importFunctions, batchSize = 3, delay = 100) => {
  const batches = [];

  for (let i = 0; i < importFunctions.length; i += batchSize) {
    batches.push(importFunctions.slice(i, i + batchSize));
  }

  for (const batch of batches) {
    await Promise.allSettled(batch.map(importFn => preloadWidget(importFn)));

    // Add delay between batches to prevent browser overload
    if (delay > 0) {
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
};

/**
 * Hook to manage widget lazy loading state
 * @param {Function} importFn - Dynamic import function
 * @returns {Object} Loading state and preload function
 */
export const useLazyWidget = importFn => {
  const [isPreloaded, setIsPreloaded] = React.useState(false);
  const [isLoading, setIsLoading] = React.useState(false);

  const preload = React.useCallback(async () => {
    if (isPreloaded) return;

    setIsLoading(true);
    try {
      await preloadWidget(importFn);
      setIsPreloaded(true);
    } catch (error) {
      console.error('Failed to preload widget:', error);
    } finally {
      setIsLoading(false);
    }
  }, [importFn, isPreloaded]);

  return { isPreloaded, isLoading, preload };
};

// Export cache utilities for advanced usage
export const clearLazyWidgetCache = () => {
  lazyComponentCache.clear();
};

export const getLazyWidgetCacheSize = () => {
  return lazyComponentCache.size;
};
