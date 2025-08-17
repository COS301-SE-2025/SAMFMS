# New Widget Additions

This document describes the three new widgets added to the widget library.

## 1. Maintenance Type Distribution Widget

**File**: `MaintenanceTypeDistributionWidget.jsx`  
**Type**: `WIDGET_TYPES.MAINTENANCE_TYPE_DISTRIBUTION`  
**Category**: `WIDGET_CATEGORIES.MAINTENANCE`

### Description

A horizontal bar chart showing maintenance costs broken down by maintenance type (e.g., oil change, brake service, tire replacement). Uses ApexCharts for interactive visualization.

### Features

- Interactive horizontal bar chart
- Shows top 10 maintenance types by cost
- Color-coded bars with cost labels
- Total cost summary at bottom
- Responsive design for mobile devices
- Configurable refresh interval, vehicle filter, and date range

### Configuration Options

- `refreshInterval`: Update frequency (60-3600 seconds, default: 300)
- `vehicleId`: Filter by specific vehicle (optional)
- `startDate`: Filter start date (optional)
- `endDate`: Filter end date (optional)

### Supported Sizes

- Medium, Large (default: Large)

---

## 2. Maintenance Overview Widget

**File**: `MaintenanceOverviewWidget.jsx`  
**Type**: `WIDGET_TYPES.MAINTENANCE_OVERVIEW`  
**Category**: `WIDGET_CATEGORIES.MAINTENANCE`

### Description

A donut chart providing an overview of upcoming vs overdue maintenance tasks. Shows key performance metrics with color-coded indicators.

### Features

- Interactive donut chart with ApexCharts
- Color-coded sections (Blue: Upcoming, Red: Overdue)
- Custom legend with count badges
- On-time performance percentage
- Total scheduled maintenance count
- Responsive design

### Configuration Options

- `refreshInterval`: Update frequency (60-3600 seconds, default: 300)
- `vehicleId`: Filter by specific vehicle (optional)
- `startDate`: Filter start date (optional)
- `endDate`: Filter end date (optional)

### Supported Sizes

- Small, Medium (default: Medium)

---

## 3. Tracking Map Widget

**File**: `TrackingMapWidget.jsx`  
**Type**: `WIDGET_TYPES.TRACKING_MAP`  
**Category**: `WIDGET_CATEGORIES.TRACKING`

### Description

An interactive map widget showing real-time vehicle locations with a collapsible sidebar for vehicle management. Based on the TrackingMapWithSidebar component.

### Features

- Interactive Leaflet map with OpenStreetMap tiles
- Collapsible sidebar with vehicle search
- Real-time vehicle markers with status indicators
- Vehicle popup information (speed, status, last update)
- Geofence visualization with circles
- Vehicle filtering and search functionality
- Summary statistics (active/inactive vehicles)
- Responsive design

### Configuration Options

- `refreshInterval`: Update frequency (10-300 seconds, default: 30)
- `defaultCenter`: Map center coordinates (default: Pretoria, SA)
- `defaultZoom`: Initial zoom level (1-20, default: 10)
- `height`: Widget height (default: '400px')

### Supported Sizes

- Large, XLarge (default: Large)

---

## Widget Registry Updates

The following constants have been added to `widgetRegistry.js`:

### New Widget Types

- `MAINTENANCE_TYPE_DISTRIBUTION: 'maintenance_type_distribution'`
- `MAINTENANCE_OVERVIEW: 'maintenance_overview'`
- `TRACKING_MAP: 'tracking_map'`

### New Widget Category

- `TRACKING: 'Tracking'`

## Usage

These widgets are automatically registered when importing from the widgets module:

```javascript
import '../components/widgets'; // Auto-registers all widgets
```

Or import individually:

```javascript
import {
  MaintenanceTypeDistributionWidget,
  MaintenanceOverviewWidget,
  TrackingMapWidget,
} from '../components/widgets';
```

## Dependencies

All widgets require:

- React 18+
- Lucide React (for icons)
- BaseWidget component
- Widget registry system

Additional dependencies by widget:

- **Chart widgets**: `react-apexcharts`
- **Map widget**: `react-leaflet`, `leaflet`
