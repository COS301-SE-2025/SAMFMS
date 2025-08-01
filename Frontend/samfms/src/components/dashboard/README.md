# Customizable Dashboard System

## Overview

This implementation provides a flexible, customizable dashboard system for the SAMFMS application. Users can add, remove, configure, and arrange widgets to create personalized dashboards that suit their specific needs.

## Architecture

### Core Components

1. **DashboardContext** (`src/contexts/DashboardContext.jsx`)

   - Manages dashboard state using React Context and useReducer
   - Handles widget management, layout changes, and edit mode
   - Provides auto-save functionality to localStorage

2. **Widget Registry** (`src/utils/widgetRegistry.js`)

   - Central registry for all available widgets
   - Defines widget types, categories, and metadata
   - Provides registration system for new widgets

3. **BaseWidget** (`src/components/dashboard/BaseWidget.jsx`)

   - Abstract base component for all widgets
   - Provides common functionality (settings, removal, drag handle)
   - Handles loading states and error display

4. **DashboardCanvas** (`src/components/dashboard/DashboardCanvas.jsx`)

   - Main dashboard container that renders widgets
   - Uses CSS Grid for responsive layout
   - Will be enhanced with react-grid-layout for advanced drag/drop

5. **WidgetLibrary** (`src/components/dashboard/WidgetLibrary.jsx`)

   - Modal interface for browsing and adding widgets
   - Supports search and category filtering
   - Displays widget metadata and allows instant addition

6. **DashboardToolbar** (`src/components/dashboard/DashboardToolbar.jsx`)
   - Dashboard controls (edit mode, add widgets, clear all)
   - Toggle between view and edit modes
   - Provides dashboard management actions

## Available Widgets

### Maintenance Widgets

- **MaintenanceSummaryWidget**: Overview cards showing total records, overdue items, upcoming maintenance, and costs
- **MaintenanceRecordsWidget**: List of recent maintenance activities
- **MaintenanceAlertsWidget**: Priority-based maintenance notifications
- **MaintenanceCostAnalyticsWidget**: Cost breakdown and trend analysis

### Vehicle Widgets

- **VehicleStatusWidget**: Fleet status overview (total, active, maintenance, idle)

### General Widgets

- **StatsCardWidget**: Configurable statistics card for any metric

## Usage

### Accessing the Dashboard

Navigate to `/dashboard` in the application to access the customizable dashboard. This is now the main dashboard page with full customization capabilities.

### Edit Mode

1. Click "Edit Dashboard" to enter edit mode
2. In edit mode, you can:
   - Add new widgets using the "Add Widget" button
   - Remove widgets using the X button on each widget
   - Configure widgets using the settings button
   - Clear all widgets using "Clear All"

### Adding Widgets

1. Enter edit mode
2. Click "Add Widget" to open the Widget Library
3. Browse or search for desired widgets
4. Click the + button to add a widget to your dashboard

### Configuring Widgets

1. Enter edit mode
2. Click the settings icon on any widget
3. Modify configuration options (title, refresh interval, etc.)
4. Save changes

## Creating New Widgets

### Step 1: Create Widget Component

Create a new widget component following this pattern:

```jsx
import React, { useState, useEffect } from 'react';
import { BaseWidget } from '../dashboard/BaseWidget';
import { registerWidget, WIDGET_TYPES, WIDGET_CATEGORIES } from '../../utils/widgetRegistry';

const MyCustomWidget = ({ id, config = {} }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Fetch data logic here
    const fetchData = async () => {
      try {
        setLoading(true);
        // Your API calls here
        setData(result);
      } catch (err) {
        setError('Failed to load data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();

    // Set up refresh interval
    const interval = setInterval(fetchData, (config.refreshInterval || 60) * 1000);
    return () => clearInterval(interval);
  }, [config.refreshInterval]);

  return (
    <BaseWidget
      id={id}
      title={config.title || 'My Widget'}
      config={config}
      loading={loading}
      error={error}
    >
      {/* Your widget content here */}
    </BaseWidget>
  );
};

// Register the widget
registerWidget('my_custom_widget', MyCustomWidget, {
  title: 'My Custom Widget',
  description: 'Description of what this widget does',
  category: WIDGET_CATEGORIES.GENERAL,
  defaultSize: { w: 2, h: 2 },
  minSize: { w: 1, h: 1 },
  maxSize: { w: 4, h: 4 },
  icon: <MyIcon size={20} />,
  configSchema: {
    title: { type: 'string', default: 'My Widget' },
    refreshInterval: { type: 'number', default: 60, min: 30 },
  },
});

export default MyCustomWidget;
```

### Step 2: Register Widget Type

Add your widget type to `WIDGET_TYPES` in `widgetRegistry.js`:

```javascript
export const WIDGET_TYPES = {
  // ... existing types
  MY_CUSTOM_WIDGET: 'my_custom_widget',
};
```

### Step 3: Import in Index

Add your widget import to `src/components/widgets/index.js`:

```javascript
import './MyCustomWidget';
export { default as MyCustomWidget } from './MyCustomWidget';
```

## Data Integration

Widgets follow the same patterns as existing maintenance components:

1. **API Integration**: Use existing API services (`maintenanceAPI`, `getVehicles`, etc.)
2. **Error Handling**: Consistent error states and user feedback
3. **Loading States**: Proper loading indicators
4. **Auto-refresh**: Configurable refresh intervals
5. **Data Transformation**: Handle various API response formats

## Styling

The system uses:

- **Tailwind CSS**: For responsive design and theming
- **Dark Mode Support**: Automatic theme switching
- **Consistent Design Language**: Matches existing SAMFMS components
- **Responsive Grid**: Mobile-friendly layout

## Future Enhancements

1. **Advanced Grid Layout**: Integration with react-grid-layout for drag/drop
2. **Widget Templates**: Pre-configured dashboard templates
3. **User Sharing**: Share dashboard configurations between users
4. **Export/Import**: Save and load dashboard configurations
5. **Real-time Updates**: WebSocket integration for live data
6. **Chart Widgets**: Integration with charting libraries
7. **Filter Integration**: Global filters affecting multiple widgets

## Technical Notes

- **State Management**: Uses React Context with useReducer for predictable state updates
- **Performance**: Widgets manage their own refresh cycles to avoid unnecessary re-renders
- **Persistence**: Dashboard configurations are saved to localStorage
- **Error Boundaries**: Isolated error handling prevents widget failures from breaking the dashboard
- **TypeScript Ready**: Architecture supports TypeScript integration

## Example Configuration

The demo dashboard includes:

- Maintenance summary with key metrics
- Vehicle status overview
- Recent maintenance records
- Maintenance alerts
- Configurable statistics cards

This provides a comprehensive starting point that can be customized based on user needs and role-based access requirements.
