# Dashboard Widget Development Guide

## Overview

The SAMFMS dashboard system provides a flexible, extensible widget-based interface for displaying fleet management information. This guide covers everything needed to develop, configure, and maintain dashboard widgets.

## Architecture

### Core Components

1. **DashboardContext** - Global state management for dashboard configuration
2. **DashboardCanvas** - Main layout engine using react-grid-layout
3. **BaseWidget** - Common widget wrapper with standard functionality
4. **WidgetRegistry** - Secure registration and management of widget types
5. **WidgetDataManager** - Centralized API management with caching and throttling

### Widget Lifecycle

```
Registration → Instantiation → Data Loading → Rendering → Updates → Cleanup
```

## Creating a New Widget

### 1. Basic Widget Structure

```jsx
import React, { useState, useEffect } from 'react';
import { BaseWidget } from '../dashboard/BaseWidget';
import { registerWidget, WIDGET_TYPES, WIDGET_CATEGORIES } from '../../utils/widgetRegistry';
import { createWidgetDataFetcher } from '../../utils/widgetDataManager';

const MyCustomWidget = ({ id, config = {} }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Create data fetcher with retry logic and caching
  const fetchData = createWidgetDataFetcher(
    'my_custom_widget',
    async config => {
      // Your API call here
      const response = await fetch('/api/my-data');
      return response.json();
    },
    {
      cacheTTL: 60000, // 1 minute cache
      maxRetries: 3,
      throttleDelay: 2000,
    }
  );

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        setError(null);
        const result = await fetchData(id, config);
        setData(result.data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    loadData();

    // Set up refresh interval
    const refreshInterval = (config.refreshInterval || 30) * 1000;
    const interval = setInterval(loadData, refreshInterval);
    return () => clearInterval(interval);
  }, [config, id, fetchData]);

  return (
    <BaseWidget id={id} title={config.title || 'My Custom Widget'} loading={loading} error={error}>
      {/* Your widget content here */}
      <div className="widget-content">
        {data && (
          <div>
            <h4>Data loaded successfully</h4>
            <pre>{JSON.stringify(data, null, 2)}</pre>
          </div>
        )}
      </div>
    </BaseWidget>
  );
};

// Register the widget
registerWidget(WIDGET_TYPES.MY_CUSTOM_WIDGET, MyCustomWidget, {
  title: 'My Custom Widget',
  description: 'A custom widget that displays my data',
  category: WIDGET_CATEGORIES.GENERAL,
  defaultSize: { w: 4, h: 3 },
  minSize: { w: 2, h: 2 },
  maxSize: { w: 8, h: 6 },
  configSchema: {
    title: { type: 'string', default: 'My Custom Widget' },
    refreshInterval: { type: 'number', default: 30, min: 5, max: 3600 },
  },
});

export default MyCustomWidget;
```

### 2. Widget Registration

Add your widget type to the `WIDGET_TYPES` constant:

```javascript
export const WIDGET_TYPES = {
  // ... existing types
  MY_CUSTOM_WIDGET: 'my_custom_widget',
};
```

### 3. Widget Import

Add your widget to the index file:

```javascript
// src/components/widgets/index.js
import './MyCustomWidget';
```

## Best Practices

### Security

1. **Input Validation**: Always validate and sanitize user inputs
2. **XSS Prevention**: Use proper escaping for dynamic content
3. **API Security**: Validate API responses and handle errors gracefully
4. **Configuration**: Sanitize widget configurations to prevent injection

### Performance

1. **Data Caching**: Use the centralized data manager for caching
2. **Memory Management**: Always clean up intervals and subscriptions
3. **Lazy Loading**: Load data only when needed
4. **Throttling**: Use request throttling for high-frequency updates

### Accessibility

1. **ARIA Labels**: Provide meaningful labels for screen readers
2. **Keyboard Navigation**: Support keyboard interaction in edit mode
3. **Focus Management**: Handle focus properly in modals and dialogs
4. **Color Contrast**: Ensure adequate color contrast for readability

### Error Handling

1. **Graceful Degradation**: Show meaningful error messages
2. **Retry Logic**: Implement exponential backoff for failed requests
3. **Fallback Data**: Use cached data when possible
4. **User Feedback**: Provide clear feedback for all states

## Configuration Schema

Define configuration options for your widget:

```javascript
configSchema: {
  title: {
    type: 'string',
    default: 'Widget Title',
    label: 'Widget Title',
    description: 'The title displayed in the widget header',
    validation: {
      required: true,
      maxLength: 50
    }
  },
  refreshInterval: {
    type: 'number',
    default: 30,
    label: 'Refresh Interval (seconds)',
    description: 'How often to refresh the widget data',
    validation: {
      min: 5,
      max: 3600
    }
  },
  showChart: {
    type: 'boolean',
    default: true,
    label: 'Show Chart',
    description: 'Whether to display the chart view'
  },
  chartType: {
    type: 'select',
    default: 'line',
    label: 'Chart Type',
    options: [
      { value: 'line', label: 'Line Chart' },
      { value: 'bar', label: 'Bar Chart' },
      { value: 'pie', label: 'Pie Chart' }
    ],
    dependsOn: 'showChart'
  }
}
```

## Data Management

### Using the Data Manager

```javascript
import { fetchWidgetData, createWidgetDataFetcher } from '../../utils/widgetDataManager';

// Simple data fetch
const data = await fetchWidgetData('cache-key', () => apiCall(), {
  cacheTTL: 30000,
  useCache: true,
  useThrottle: true,
});

// Widget-specific fetcher
const fetchWidgetData = createWidgetDataFetcher('widget-type', apiCallFunction, defaultOptions);
```

### Error Handling Patterns

```javascript
try {
  const result = await fetchData(id, config);
  setData(result.data);
  setError(null);
} catch (err) {
  console.error('Widget data fetch failed:', err);
  setError('Failed to load data. Please try again.');
  // Optionally keep existing data on error
} finally {
  setLoading(false);
}
```

## Testing Your Widget

### 1. Unit Testing

```javascript
import { render, screen, waitFor } from '@testing-library/react';
import { DashboardProvider } from '../../contexts/DashboardContext';
import MyCustomWidget from './MyCustomWidget';

test('renders widget with data', async () => {
  render(
    <DashboardProvider>
      <MyCustomWidget id="test-widget" config={{ title: 'Test Widget' }} />
    </DashboardProvider>
  );

  expect(screen.getByText('Test Widget')).toBeInTheDocument();
  await waitFor(() => {
    expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
  });
});
```

### 2. Integration Testing

Test your widget within the dashboard context to ensure proper integration.

### 3. Manual Testing

1. Add widget to dashboard
2. Test configuration changes
3. Test responsive behavior
4. Test error scenarios
5. Test accessibility features

## Troubleshooting

### Common Issues

1. **Widget Not Rendering**: Check registration and import
2. **Data Not Loading**: Verify API endpoint and error handling
3. **Layout Issues**: Check size constraints and CSS conflicts
4. **Memory Leaks**: Ensure proper cleanup of intervals/subscriptions

### Debug Tools

1. React Developer Tools
2. Browser Network tab for API calls
3. Console logs for widget lifecycle events
4. Dashboard context state inspection

## Migration Guide

### From Legacy Widgets

1. Wrap existing component with `BaseWidget`
2. Implement proper error handling
3. Add configuration schema
4. Use centralized data management
5. Add accessibility features
6. Update registration metadata

## Advanced Topics

### Custom Configuration UI

For complex widgets, you can create custom configuration components:

```javascript
const CustomConfigModal = ({ config, onSave, onClose }) => {
  // Custom configuration interface
  return (
    <div className="custom-config-modal">
      {/* Custom form fields */}
    </div>
  );
};

// Use in BaseWidget
<BaseWidget
  configComponent={CustomConfigModal}
  // ... other props
>
```

### Widget Communication

Widgets can communicate through the dashboard context or custom event system:

```javascript
// Subscribe to dashboard-wide events
useEffect(() => {
  const handleDashboardEvent = event => {
    // Handle event
  };

  window.addEventListener('dashboard:update', handleDashboardEvent);
  return () => window.removeEventListener('dashboard:update', handleDashboardEvent);
}, []);
```

## Contributing

1. Follow the coding standards
2. Add comprehensive tests
3. Update documentation
4. Submit pull request with clear description
5. Ensure accessibility compliance

For questions or support, please refer to the project's main README or contact the development team.
