import React, {useState, useEffect, useCallback, useMemo} from 'react';
import {BaseWidget} from '../dashboard/BaseWidget';
import {registerWidget, WIDGET_TYPES, WIDGET_CATEGORIES} from '../../utils/widgetRegistry';
import {MapContainer, TileLayer, Marker, Popup, Circle, LayerGroup} from 'react-leaflet';
import {Search, Navigation, Menu, Map as MapIcon} from 'lucide-react';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import {getVehicles} from '../../backend/api/vehicles';
import {listGeofences} from '../../backend/api/geofences';

// Fix for marker icons in React-Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
});

// Custom vehicle icon
const createVehicleIcon = status => {
  const color = status === 'active' ? '#22c55e' : status === 'inactive' ? '#ef4444' : '#f59e0b';
  return L.divIcon({
    html: `<div style="background-color: ${color}; width: 20px; height: 20px; border-radius: 50%; border: 2px solid white; display: flex; align-items: center; justify-content: center;">
             <svg width="12" height="12" viewBox="0 0 24 24" fill="white">
               <path d="M5 11l4-4v3h5.28c.35 0 .72.22.72.72v4.56c0 .5-.37.72-.72.72H9v3l-4-4z"/>
             </svg>
           </div>`,
    className: 'custom-vehicle-marker',
    iconSize: [20, 20],
    iconAnchor: [10, 10],
  });
};

const TrackingMapWidget = ({id, config = {}}) => {
  const [vehicles, setVehicles] = useState([]);
  const [geofences, setGeofences] = useState([]);
  const [selectedVehicle, setSelectedVehicle] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // Map configuration with useMemo to prevent dependency changes
  const defaultCenter = useMemo(
    () => config.defaultCenter || [-25.7479, 28.2293],
    [config.defaultCenter]
  ); // Pretoria, South Africa
  const defaultZoom = config.defaultZoom || 10;

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const [vehiclesResponse, geofencesResponse] = await Promise.all([
        getVehicles().catch(() => ({data: {data: {vehicles: []}}})),
        listGeofences().catch(() => ({data: []})),
      ]);

      // Handle nested response structure
      const vehiclesData =
        vehiclesResponse?.data?.data?.vehicles ||
        vehiclesResponse?.vehicles ||
        vehiclesResponse?.data?.vehicles ||
        [];

      const geofencesData = Array.isArray(geofencesResponse?.data)
        ? geofencesResponse.data
        : Array.isArray(geofencesResponse)
          ? geofencesResponse
          : [];

      // Add mock GPS coordinates for demonstration
      const vehiclesWithCoords = (Array.isArray(vehiclesData) ? vehiclesData : []).map(vehicle => ({
        ...vehicle,
        latitude: vehicle.latitude || defaultCenter[0] + (Math.random() - 0.5) * 0.1,
        longitude: vehicle.longitude || defaultCenter[1] + (Math.random() - 0.5) * 0.1,
        status: vehicle.status || (Math.random() > 0.3 ? 'active' : 'inactive'),
        speed: vehicle.speed || Math.floor(Math.random() * 100),
        lastUpdate: vehicle.lastUpdate || new Date().toISOString(),
      }));

      setVehicles(vehiclesWithCoords);
      setGeofences(geofencesData);
    } catch (err) {
      console.error('Error loading tracking data:', err);
      setError('Failed to load tracking data');
    } finally {
      setLoading(false);
    }
  }, [defaultCenter]);

  useEffect(() => {
    loadData();

    // Set up refresh interval
    const refreshInterval = (config.refreshInterval || 30) * 1000; // Default 30 seconds
    const interval = setInterval(loadData, refreshInterval);

    return () => clearInterval(interval);
  }, [loadData, config.refreshInterval]);

  // Filter vehicles based on search term
  const filteredVehicles = (Array.isArray(vehicles) ? vehicles : []).filter(
    vehicle =>
      vehicle.license_plate?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      vehicle.make?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      vehicle.model?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const renderSidebar = () => {
    if (!sidebarOpen) return null; // completely hide

    return (
      <div className="w-80 transition-all duration-300 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col">
        {/* Sidebar Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            Vehicle Tracking
          </h3>
          <button
            onClick={() => setSidebarOpen(false)}
            className="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors bg-white dark:bg-gray-800"
          >
            <Menu className="h-5 w-5 text-gray-900 dark:text-gray-100" />
          </button>
        </div>

        {/* Search input */}
        <div className="p-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search vehicles..."
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>

        {/* Vehicle List */}
        <div className="flex-1 overflow-y-auto">
          <div className="p-4 space-y-3">
            {filteredVehicles.map(vehicle => (
              <div
                key={vehicle.id}
                onClick={() => setSelectedVehicle(vehicle)}
                className={`p-3 rounded-lg border cursor-pointer transition-all ${selectedVehicle?.id === vehicle.id
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                  : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
                  }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div
                      className={`w-3 h-3 rounded-full ${vehicle.status === 'active' ? 'bg-green-500' : 'bg-red-500'
                        }`}
                    />
                    <div>
                      <div className="font-medium text-gray-900 dark:text-gray-100">
                        {vehicle.license_plate}
                      </div>
                      <div className="text-sm text-gray-500 dark:text-gray-400">
                        {vehicle.make} {vehicle.model}
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                      {vehicle.speed || 0} km/h
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">
                      {vehicle.status}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Summary Stats */}
        <div className="p-4 border-t border-gray-200 dark:border-gray-700">
          <div className="grid grid-cols-2 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-green-600">
                {vehicles.filter(v => v.status === 'active').length}
              </div>
              <div className="text-xs text-gray-500">Active</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-red-600">
                {vehicles.filter(v => v.status === 'inactive').length}
              </div>
              <div className="text-xs text-gray-500">Inactive</div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderMap = () => (
    <div className="flex-1 relative">
      {/* Burger button (always visible, top-left) - must be outside MapContainer for correct positioning */}
      <div className="absolute top-4 left-4 z-20">
        {!sidebarOpen && (
          <button
            onClick={() => setSidebarOpen(true)}
            className="p-2 bg-white dark:bg-gray-800 rounded-md shadow-md hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          >
            <Menu className="h-5 w-5 text-gray-900 dark:text-gray-100" />
          </button>
        )}
      </div>
      <MapContainer
        center={defaultCenter}
        zoom={defaultZoom}
        className="w-full h-full"
        zoomControl={true}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />
        {/* Vehicle Markers */}
        <LayerGroup>
          {filteredVehicles.map(vehicle => (
            <Marker
              key={vehicle.id}
              position={[vehicle.latitude, vehicle.longitude]}
              icon={createVehicleIcon(vehicle.status)}
            >
              <Popup>
                <div className="p-2">
                  <div className="font-semibold">{vehicle.license_plate}</div>
                  <div className="text-sm text-gray-600">
                    {vehicle.make} {vehicle.model}
                  </div>
                  <div className="text-sm mt-1">
                    <div>
                      Status:{' '}
                      <span
                        className={`font-medium ${vehicle.status === 'active' ? 'text-green-600' : 'text-red-600'
                          }`}
                      >
                        {vehicle.status}
                      </span>
                    </div>
                    <div>Speed: {vehicle.speed || 0} km/h</div>
                    {vehicle.lastUpdate && (
                      <div className="text-xs text-gray-500 mt-1">
                        Last update: {new Date(vehicle.lastUpdate).toLocaleTimeString()}
                      </div>
                    )}
                  </div>
                </div>
              </Popup>
            </Marker>
          ))}
        </LayerGroup>
        {/* Geofences */}
        <LayerGroup>
          {Array.isArray(geofences) &&
            geofences.map(geofence => (
              <Circle
                key={geofence.id}
                center={[geofence.latitude, geofence.longitude]}
                radius={geofence.radius}
                pathOptions={{
                  color: geofence.color || '#3388ff',
                  fillColor: geofence.color || '#3388ff',
                  fillOpacity: 0.1,
                  weight: 2,
                }}
              >
                <Popup>
                  <div className="p-2">
                    <div className="font-semibold">{geofence.name}</div>
                    <div className="text-sm text-gray-600">{geofence.description}</div>
                    <div className="text-sm mt-1">Radius: {geofence.radius}m</div>
                  </div>
                </Popup>
              </Circle>
            ))}
        </LayerGroup>
      </MapContainer>
      {/* Map Controls */}
      <div className="absolute top-4 right-4 z-10 flex flex-col space-y-2">
        <button
          onClick={loadData}
          className="p-2 bg-white dark:bg-gray-800 rounded-md shadow-md hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          title="Refresh"
        >
          <Navigation className="h-5 w-5" />
        </button>
      </div>
    </div>
  );

  return (
    <BaseWidget
      id={id}
      title={config.title || 'Vehicle Tracking Map'}
      loading={loading}
      error={error}
      className="p-0 overflow-hidden"
      style={{height: config.height || '400px'}}
    >
      <div className="flex h-full">
        {renderSidebar()}
        {renderMap()}
      </div>
    </BaseWidget>
  );
};

// Register the widget
registerWidget(WIDGET_TYPES.TRACKING_MAP, TrackingMapWidget, {
  title: 'Vehicle Tracking Map',
  description: 'Interactive map showing real-time vehicle locations with sidebar',
  category: WIDGET_CATEGORIES.TRACKING,
  icon: MapIcon,
  defaultConfig: {
    refreshInterval: 30, // 30 seconds
    defaultCenter: [-25.7479, 28.2293], // Pretoria, South Africa
    defaultZoom: 10,
    height: '400px',
  },
  configSchema: {
    refreshInterval: {
      type: 'number',
      label: 'Refresh Interval (seconds)',
      min: 10,
      max: 300,
      default: 30,
    },
    defaultCenter: {
      type: 'array',
      label: 'Default Map Center [lat, lng]',
      default: [-25.7479, 28.2293],
    },
    defaultZoom: {
      type: 'number',
      label: 'Default Zoom Level',
      min: 1,
      max: 20,
      default: 10,
    },
    height: {
      type: 'string',
      label: 'Widget Height',
      default: '400px',
    },
  },
  defaultSize: {w: 12, h: 8},
  minSize: {w: 8, h: 6},
  maxSize: {w: 12, h: 10},
});

export default TrackingMapWidget;
