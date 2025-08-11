import React, { useState, useEffect, useCallback } from 'react';
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Circle,
  LayerGroup,
  FeatureGroup,
  useMap,
} from 'react-leaflet';
import { Search, Navigation, Car, Shield, ChevronLeft, ChevronRight } from 'lucide-react';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { getVehicles } from '../../backend/api/vehicles';
import { listGeofences } from '../../backend/api/geofences';
import { listLocations } from '../../backend/api/locations';

// Fix for default markers in react-leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
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

// Custom geofence icon
const createGeofenceIcon = type => {
  const color = type === 'depot' ? '#3b82f6' : type === 'restricted' ? '#ef4444' : '#8b5cf6';
  return L.divIcon({
    html: `<div style="background-color: ${color}; width: 20px; height: 20px; border-radius: 50%; border: 2px solid white; display: flex; align-items: center; justify-content: center;">
             <svg width="12" height="12" viewBox="0 0 24 24" fill="white">
               <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/>
             </svg>
           </div>`,
    className: 'custom-geofence-marker',
    iconSize: [20, 20],
    iconAnchor: [10, 10],
  });
};

// Geofence path options based on type
const getGeofenceOptions = type => {
  switch (type) {
    case 'depot':
      return {
        color: '#3b82f6',
        fillColor: '#3b82f6',
        fillOpacity: 0.2,
        weight: 2,
      };
    case 'restricted':
      return {
        color: '#ef4444',
        fillColor: '#ef4444',
        fillOpacity: 0.3,
        weight: 2,
      };
    case 'safe_zone':
      return {
        color: '#22c55e',
        fillColor: '#22c55e',
        fillOpacity: 0.2,
        weight: 2,
      };
    default:
      return {
        color: '#8b5cf6',
        fillColor: '#8b5cf6',
        fillOpacity: 0.2,
        weight: 2,
      };
  }
};

// Map updater component to center on selected items
const MapUpdater = ({ center, zoom = 13 }) => {
  const map = useMap();

  useEffect(() => {
    if (center && center[0] && center[1]) {
      map.setView(center, zoom);
    }
  }, [center, zoom, map]);

  return null;
};

const TrackingMapWithSidebar = () => {
  const [activeTab, setActiveTab] = useState('vehicles');
  const [vehicles, setVehicles] = useState([]);
  const [geofences, setGeofences] = useState([]);
  const [showGeofences, setShowGeofences] = useState(true);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [mapCenter, setMapCenter] = useState([37.7749, -122.4194]); // Default to San Francisco
  const [selectedItem, setSelectedItem] = useState(null);

  // Load vehicles data
  const loadVehicles = useCallback(async () => {
    try {
      setLoading(true);

      // Load both vehicles and locations
      const [vehiclesResponse, locationsResponse] = await Promise.all([
        getVehicles({ limit: 100 }),
        listLocations(),
      ]);

      const vehiclesData =
        vehiclesResponse.data?.data?.vehicles ||
        vehiclesResponse.vehicles ||
        vehiclesResponse.data?.vehicles ||
        [];
      const locationsData =
        locationsResponse.data?.data?.data ||
        locationsResponse.data?.data ||
        locationsResponse.data ||
        [];

      // Create a map of vehicle locations by vehicle_id
      const locationMap = {};
      locationsData.forEach(location => {
        locationMap[location.vehicle_id] = {
          lat: location.latitude,
          lng: location.longitude,
          location: location, // Store full location data
        };
      });

      // Only include vehicles that have actual GPS location data
      const transformedVehicles = vehiclesData
        .filter(vehicle => {
          const vehicleId = vehicle.id || vehicle.vehicle_id;
          return locationMap[vehicleId]; // Only include vehicles with GPS data
        })
        .map(vehicle => {
          const vehicleId = vehicle.id || vehicle.vehicle_id;
          const vehicleLocation = locationMap[vehicleId];
          return {
            id: vehicleId,
            name: vehicle.vehicle_name || vehicle.name || `Vehicle ${vehicleId}`,
            make: vehicle.make || 'Unknown',
            model: vehicle.model || 'Unknown',
            status: vehicle.status || 'unknown',
            license_plate: vehicle.license_plate || 'N/A',
            coordinates: {
              lat: vehicleLocation.lat,
              lng: vehicleLocation.lng,
            },
            hasLocation: true, // All displayed vehicles have real location data
            locationData: vehicleLocation.location, // Store full location data for additional info
          };
        });

      setVehicles(transformedVehicles);
    } catch (err) {
      console.error('Error loading vehicles:', err);
      setError('Failed to load vehicles');
    }
  }, []);

  // Load geofences data
  const loadGeofences = useCallback(async () => {
    try {
      const response = await listGeofences();
      // Handle nested API response structure: response.data.data
      const geofencesData = response.data?.data || response.data || response || [];

      // Transform geofences data according to API response structure
      const transformedGeofences = geofencesData
        .map(geofence => ({
          id: geofence.id,
          name: geofence.name || `Geofence ${geofence.id}`,
          description: geofence.description || '',
          type: geofence.type || 'general',
          // Extract coordinates from geometry.center
          coordinates: geofence.geometry?.center
            ? {
                lat: geofence.geometry.center.latitude,
                lng: geofence.geometry.center.longitude,
              }
            : {
                lat: 37.7749 + (Math.random() - 0.5) * 0.1,
                lng: -122.4194 + (Math.random() - 0.5) * 0.1,
              },
          radius: geofence.geometry?.radius || 1000,
          status: geofence.status || 'active',
        }))
        .filter(
          geofence => geofence.coordinates && geofence.coordinates.lat && geofence.coordinates.lng
        );

      setGeofences(transformedGeofences);
    } catch (err) {
      console.error('Error loading geofences:', err);
      setError('Failed to load geofences');
    } finally {
      setLoading(false);
    }
  }, []);

  // Load data on mount
  useEffect(() => {
    const loadData = async () => {
      await Promise.all([loadVehicles(), loadGeofences()]);
    };
    loadData();
  }, [loadVehicles, loadGeofences]);

  // Filter items based on search term
  const filteredItems =
    activeTab === 'vehicles'
      ? vehicles.filter(
          vehicle =>
            vehicle.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            vehicle.make.toLowerCase().includes(searchTerm.toLowerCase()) ||
            vehicle.model.toLowerCase().includes(searchTerm.toLowerCase()) ||
            vehicle.license_plate.toLowerCase().includes(searchTerm.toLowerCase())
        )
      : geofences.filter(
          geofence =>
            geofence.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            geofence.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
            geofence.type.toLowerCase().includes(searchTerm.toLowerCase())
        );

  // Handle item selection and map centering
  const handleItemSelect = item => {
    setSelectedItem(item);
    setMapCenter([item.coordinates.lat, item.coordinates.lng]);
  };

  if (loading && vehicles.length === 0 && geofences.length === 0) {
    return (
      <div className="bg-card shadow-md p-6 mb-6">
        <div className="flex items-center justify-center h-96">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mr-3"></div>
          <span>Loading map data...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-card shadow-md p-6 mb-6">
        <div className="bg-destructive/10 border border-destructive text-destructive px-4 py-3">
          <p>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-card shadow-md mb-6">
      <div className="flex flex-col lg:flex-row gap-0 relative" style={{ height: '85vh' }}>
        {/* Map */}
        <div className="flex-1 border border-border overflow-hidden relative">
          <MapContainer center={mapCenter} zoom={13} style={{ height: '100%', width: '100%' }}>
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            <MapUpdater center={mapCenter} />

            {/* Vehicle Markers */}
            {activeTab === 'vehicles' &&
              vehicles.map(vehicle => (
                <Marker
                  key={`vehicle-${vehicle.id}`}
                  position={[vehicle.coordinates.lat, vehicle.coordinates.lng]}
                  icon={createVehicleIcon(vehicle.status)}
                >
                  <Popup>
                    <div className="text-sm">
                      <h4 className="font-medium">{vehicle.name}</h4>
                      <p className="text-muted-foreground">
                        {vehicle.make} {vehicle.model}
                      </p>
                      <p className="text-muted-foreground">Plate: {vehicle.license_plate}</p>
                      <div className="flex items-center mt-1">
                        <div
                          className={`w-2 h-2 rounded-full mr-2 ${
                            vehicle.status === 'active'
                              ? 'bg-green-500'
                              : vehicle.status === 'inactive'
                              ? 'bg-red-500'
                              : 'bg-yellow-500'
                          }`}
                        ></div>
                        <span className="text-xs capitalize">{vehicle.status}</span>
                      </div>
                    </div>
                  </Popup>
                </Marker>
              ))}

            {/* Geofence Circles and Markers - Always show when enabled */}
            {showGeofences && geofences.length > 0 && (
              <LayerGroup>
                {geofences.map(geofence => (
                  <FeatureGroup
                    key={`geofence-group-${geofence.id}`}
                    pathOptions={getGeofenceOptions(geofence.type)}
                  >
                    <Popup>
                      <div className="text-sm">
                        <h4 className="font-medium">{geofence.name}</h4>
                        <p className="text-muted-foreground">{geofence.description}</p>
                        <div className="flex items-center mt-1">
                          <div
                            className={`w-2 h-2 rounded-full mr-2 ${
                              geofence.type === 'depot'
                                ? 'bg-blue-500'
                                : geofence.type === 'restricted'
                                ? 'bg-red-500'
                                : geofence.type === 'safe_zone'
                                ? 'bg-green-500'
                                : 'bg-purple-500'
                            }`}
                          ></div>
                          <span className="text-xs capitalize">{geofence.type}</span>
                        </div>
                        {geofence.radius && (
                          <p className="text-xs text-muted-foreground mt-1">
                            Radius: {geofence.radius}m
                          </p>
                        )}
                      </div>
                    </Popup>
                    {/* Circle representing the geofence area */}
                    <Circle
                      center={[geofence.coordinates.lat, geofence.coordinates.lng]}
                      radius={geofence.radius || 1000}
                    />
                    {/* Center marker - only show when geofences tab is active */}
                    {activeTab === 'geofences' && (
                      <Marker
                        position={[geofence.coordinates.lat, geofence.coordinates.lng]}
                        icon={createGeofenceIcon(geofence.type)}
                      />
                    )}
                  </FeatureGroup>
                ))}
              </LayerGroup>
            )}
          </MapContainer>

          {/* Sidebar Toggle Button */}
          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="absolute top-4 right-4 z-[1000] bg-white border border-border shadow-md p-2 hover:bg-accent"
            title={sidebarCollapsed ? 'Show Sidebar' : 'Hide Sidebar'}
          >
            {sidebarCollapsed ? (
              <ChevronLeft className="w-4 h-4" />
            ) : (
              <ChevronRight className="w-4 h-4" />
            )}
          </button>
        </div>

        {/* Sidebar */}
        <div
          className={`${
            sidebarCollapsed ? 'w-0' : 'w-full lg:w-80'
          } transition-all duration-300 overflow-hidden flex flex-col bg-card border-l border-border`}
        >
          <div className="flex flex-col h-full p-4">
            {/* Tabs */}
            <div className="flex border-b border-border mb-4">
              <button
                className={`flex-1 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'vehicles'
                    ? 'border-primary text-primary bg-primary/5'
                    : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'
                }`}
                onClick={() => {
                  setActiveTab('vehicles');
                  setSearchTerm('');
                  setSelectedItem(null);
                }}
              >
                <Car className="w-4 h-4 inline mr-2" />
                Vehicles ({vehicles.length})
              </button>
              <button
                className={`flex-1 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'geofences'
                    ? 'border-primary text-primary bg-primary/5'
                    : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'
                }`}
                onClick={() => {
                  setActiveTab('geofences');
                  setSearchTerm('');
                  setSelectedItem(null);
                }}
              >
                <Shield className="w-4 h-4 inline mr-2" />
                Geofences ({geofences.length})
              </button>
            </div>

            {/* Geofence Toggle */}
            <div className="flex items-center justify-between mb-4 px-2">
              <span className="text-sm text-muted-foreground">Show Geofences</span>
              <button
                onClick={() => setShowGeofences(!showGeofences)}
                className={`relative inline-flex h-6 w-11 items-center transition-colors ${
                  showGeofences ? 'bg-primary' : 'bg-gray-300'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform bg-white transition-transform ${
                    showGeofences ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            {/* Search */}
            <div className="relative mb-4">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
              <input
                type="text"
                placeholder={`Search ${activeTab}...`}
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>

            {/* Items List */}
            <div className="flex-1 overflow-y-auto space-y-2">
              {filteredItems.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <p>No {activeTab} found</p>
                  {searchTerm && <p className="text-xs mt-1">Try adjusting your search</p>}
                </div>
              ) : (
                filteredItems.map(item => (
                  <div
                    key={item.id}
                    className={`p-3 border border-border cursor-pointer transition-colors hover:bg-accent ${
                      selectedItem?.id === item.id ? 'bg-primary/10 border-primary' : ''
                    }`}
                    onClick={() => handleItemSelect(item)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="font-medium text-sm truncate">{item.name}</h4>
                        {activeTab === 'vehicles' ? (
                          <div className="mt-1">
                            <p className="text-xs text-muted-foreground">
                              {item.make} {item.model}
                            </p>
                            <p className="text-xs text-muted-foreground">
                              Plate: {item.license_plate}
                            </p>
                            <div className="flex items-center mt-1">
                              <div
                                className={`w-2 h-2 rounded-full mr-2 ${
                                  item.status === 'active'
                                    ? 'bg-green-500'
                                    : item.status === 'inactive'
                                    ? 'bg-red-500'
                                    : 'bg-yellow-500'
                                }`}
                              ></div>
                              <span className="text-xs capitalize text-muted-foreground">
                                {item.status}
                              </span>
                            </div>
                          </div>
                        ) : (
                          <div className="mt-1">
                            <p className="text-xs text-muted-foreground truncate">
                              {item.description || 'No description'}
                            </p>
                            <div className="flex items-center mt-1">
                              <div
                                className={`w-2 h-2 rounded-full mr-2 ${
                                  item.type === 'depot'
                                    ? 'bg-blue-500'
                                    : item.type === 'restricted'
                                    ? 'bg-red-500'
                                    : 'bg-purple-500'
                                }`}
                              ></div>
                              <span className="text-xs capitalize text-muted-foreground">
                                {item.type}
                              </span>
                            </div>
                          </div>
                        )}
                      </div>
                      <Navigation className="w-4 h-4 text-muted-foreground ml-2 flex-shrink-0" />
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TrackingMapWithSidebar;
