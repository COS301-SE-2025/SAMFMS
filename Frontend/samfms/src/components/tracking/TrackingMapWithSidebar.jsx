import React, { useState, useEffect, useCallback, useRef } from 'react';
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
import {
  Search,
  Navigation,
  Car,
  Shield,
  Menu,
  Plus,
  Edit2,
  Trash2,
  Locate,
  LocateFixed,
} from 'lucide-react';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { getVehicles } from '../../backend/api/vehicles';
import { listGeofences, deleteGeofence } from '../../backend/api/geofences';
import { listLocations } from '../../backend/api/locations';
import GeofenceManager from './GeofenceManager';

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
  const [showVehicles, setShowVehicles] = useState(true);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [showAddGeofenceModal, setShowAddGeofenceModal] = useState(false);
  const [editingGeofence, setEditingGeofence] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [mapCenter, setMapCenter] = useState([37.7749, -122.4194]); // Default to San Francisco, will be updated with user location
  const [selectedItem, setSelectedItem] = useState(null);
  const [userLocation, setUserLocation] = useState(null);
  const [showUserLocation, setShowUserLocation] = useState(false);

  // Address search state
  const [addressSearch, setAddressSearch] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [searchSuggestions, setSearchSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);

  // Ref for search container to handle click outside
  const searchContainerRef = useRef(null);

  // Cleanup timeout on unmount
  useEffect(() => {
    // Handle click outside search bar to hide suggestions
    const handleClickOutside = event => {
      if (searchContainerRef.current && !searchContainerRef.current.contains(event.target)) {
        setShowSuggestions(false);
      }
    };

    // Close sidebar with Escape key
    const handleKeyDown = event => {
      if (event.key === 'Escape' && !sidebarCollapsed) {
        setSidebarCollapsed(true);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('mousedown', handleClickOutside);

    return () => {
      if (window.addressSearchTimeout) {
        clearTimeout(window.addressSearchTimeout);
      }
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [sidebarCollapsed]);

  // Get user's location on mount
  useEffect(() => {
    const getUserLocation = () => {
      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
          position => {
            const { latitude, longitude } = position.coords;
            const locationArray = [latitude, longitude];
            setUserLocation(locationArray);
            setMapCenter(locationArray);
          },
          error => {
            console.warn('Could not get user location:', error);
            // Keep default location (San Francisco) if geolocation fails
          },
          {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 300000, // 5 minutes
          }
        );
      } else {
        console.warn('Geolocation is not supported by this browser.');
      }
    };

    getUserLocation();
  }, []);

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

      console.log('Locations response structure:', locationsResponse);
      console.log('Extracted locationsData:', locationsData);
      console.log('Is locationsData an array?', Array.isArray(locationsData));

      // Ensure locationsData is an array before using forEach
      if (!Array.isArray(locationsData)) {
        console.warn('locationsData is not an array:', typeof locationsData, locationsData);
        setVehicles([]); // Set empty array if no valid location data
        return;
      }

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
            (vehicle.name?.toLowerCase() || '').includes(searchTerm.toLowerCase()) ||
            (vehicle.make?.toLowerCase() || '').includes(searchTerm.toLowerCase()) ||
            (vehicle.model?.toLowerCase() || '').includes(searchTerm.toLowerCase()) ||
            (vehicle.license_plate?.toLowerCase() || '').includes(searchTerm.toLowerCase())
        )
      : geofences.filter(
          geofence =>
            (geofence.name?.toLowerCase() || '').includes(searchTerm.toLowerCase()) ||
            (geofence.description?.toLowerCase() || '').includes(searchTerm.toLowerCase()) ||
            (geofence.type?.toLowerCase() || '').includes(searchTerm.toLowerCase())
        );

  // Handle geofence changes from the GeofenceManager
  const handleGeofenceChange = useCallback(async updatedGeofences => {
    // We now rely primarily on server refresh through onSuccess
    // This is kept for backward compatibility but simplified
    console.log('Geofences changed, relying on server refresh');
  }, []);

  // Enhanced function to handle successful geofence operations
  const handleGeofenceSuccess = useCallback(async () => {
    // Reload geofences to show the latest data from the server
    console.log('Refreshing geofences after successful operation');
    await loadGeofences();

    // Close modal
    setShowAddGeofenceModal(false);
    setEditingGeofence(null);
  }, [loadGeofences]);

  // Handle item selection and map centering
  const handleItemSelect = item => {
    setSelectedItem(item);
    setMapCenter([item.coordinates.lat, item.coordinates.lng]);
  };

  // Handle geofence editing
  const handleEditGeofence = (geofence, event) => {
    event.stopPropagation(); // Prevent item selection
    setEditingGeofence(geofence);
    setShowAddGeofenceModal(true);
  };

  // Handle geofence deletion
  const handleDeleteGeofence = async (geofenceId, event) => {
    event.stopPropagation(); // Prevent item selection

    if (window.confirm('Are you sure you want to delete this geofence?')) {
      try {
        await deleteGeofence(geofenceId);
        // Immediately update the state to remove the deleted geofence
        setGeofences(prev => prev.filter(g => g.id !== geofenceId));
        // Reload geofences to ensure we have the latest data
        await loadGeofences();
      } catch (error) {
        console.error('Error deleting geofence:', error);
        alert('Failed to delete geofence. Please try again.');
        // Reload geofences in case of error to ensure consistency
        await loadGeofences();
      }
    }
  };

  // Address search functionality
  const handleAddressSearch = async query => {
    if (!query.trim()) {
      setSearchSuggestions([]);
      setShowSuggestions(false);
      return;
    }

    setIsSearching(true);
    try {
      // Using Nominatim (OpenStreetMap) geocoding service
      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(
          query
        )}&limit=5&addressdetails=1`
      );

      if (response.ok) {
        const data = await response.json();
        const suggestions = data.map(item => ({
          display_name: item.display_name,
          lat: parseFloat(item.lat),
          lon: parseFloat(item.lon),
          place_id: item.place_id,
        }));

        setSearchSuggestions(suggestions);
        setShowSuggestions(suggestions.length > 0);
      }
    } catch (error) {
      console.error('Error searching address:', error);
      setSearchSuggestions([]);
    } finally {
      setIsSearching(false);
    }
  };

  // Handle address selection from suggestions
  const handleAddressSelect = suggestion => {
    setMapCenter([suggestion.lat, suggestion.lon]);
    setAddressSearch(suggestion.display_name);
    setShowSuggestions(false);
    setSearchSuggestions([]);
    // Keep the search bar expanded after selection so user can see the selected address
  };

  // Handle input change with debounced search
  const handleAddressInputChange = value => {
    setAddressSearch(value);

    // Clear previous timeout
    if (window.addressSearchTimeout) {
      clearTimeout(window.addressSearchTimeout);
    }

    // Set new timeout for search
    window.addressSearchTimeout = setTimeout(() => {
      handleAddressSearch(value);
    }, 300);
  };

  // Handle location button click
  const handleLocationButtonClick = () => {
    if (userLocation && userLocation[0] && userLocation[1]) {
      setMapCenter([userLocation[0], userLocation[1]]);
      setShowUserLocation(!showUserLocation);
    } else {
      // Try to get location again if we don't have it
      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
          position => {
            const { latitude, longitude } = position.coords;
            const locationArray = [latitude, longitude];
            setUserLocation(locationArray);
            setMapCenter(locationArray);
            setShowUserLocation(true);
          },
          error => {
            console.warn('Could not get user location:', error);
            alert('Unable to get your location. Please check your browser permissions.');
          },
          {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 300000,
          }
        );
      }
    }
  };
  if (loading && vehicles.length === 0 && geofences.length === 0) {
    return (
      <div
        className="w-full flex items-center justify-center"
        style={{ height: 'calc(100vh - 70px)' }}
      >
        <div className="flex items-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mr-3"></div>
          <span>Loading map data...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div
        className="w-full flex items-center justify-center p-6"
        style={{ height: 'calc(100vh - 70px)' }}
      >
        <div className="bg-destructive/10 border border-destructive text-destructive px-4 py-3 rounded max-w-md w-full text-center">
          <p>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full" style={{ height: 'calc(100vh - 70px)' }}>
      <div className="relative h-full">
        {/* Map - Full Width */}
        <div className="w-full h-full border border-border overflow-hidden relative">
          {/* Floating Address Search Bar and Toggle Buttons */}
          <div className="absolute top-4 left-4 right-4 z-[1000]">
            <div className="flex items-start gap-3">
              {/* Location Button */}
              <button
                onClick={handleLocationButtonClick}
                className={`flex items-center justify-center rounded-lg shadow-lg border px-3 py-2 h-10 transition-all duration-300 ease-in-out hover:scale-105 active:scale-95 ${
                  showUserLocation
                    ? 'bg-blue-500 hover:bg-blue-600 border-blue-600 text-white'
                    : 'bg-white hover:bg-gray-50 border-gray-300 text-gray-600 dark:bg-gray-800 dark:hover:bg-gray-700 dark:border-gray-600 dark:text-gray-300'
                }`}
                title="Go to my location"
              >
                {showUserLocation ? (
                  <LocateFixed className="w-4 h-4 transition-transform duration-200" />
                ) : (
                  <Locate className="w-4 h-4 transition-transform duration-200" />
                )}
              </button>

              {/* Search Bar Container */}
              <div className="flex-1" ref={searchContainerRef}>
                <div className="transition-all duration-300 ease-in-out">
                  <div className="space-y-2">
                    {/* Search bar */}
                    <div className="relative flex items-center bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg shadow-lg transition-all duration-300 ease-in-out h-10">
                      <Search className="absolute left-3 text-gray-500 dark:text-gray-400 w-4 h-4 transition-colors duration-200" />
                      <input
                        type="text"
                        placeholder="Search for an address..."
                        value={addressSearch}
                        onChange={e => handleAddressInputChange(e.target.value)}
                        onFocus={() => {
                          if (searchSuggestions.length > 0) {
                            setShowSuggestions(true);
                          }
                        }}
                        className="w-full pl-10 pr-12 py-3 rounded-lg border-0 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-transparent text-gray-900 dark:text-gray-100 text-sm placeholder-gray-500 dark:placeholder-gray-400 transition-all duration-200"
                        onKeyDown={e => {
                          if (e.key === 'Escape') {
                            setAddressSearch('');
                            setShowSuggestions(false);
                            setSearchSuggestions([]);
                          }
                        }}
                      />
                      {/* Loading spinner */}
                      {isSearching && (
                        <div className="absolute right-3 transition-opacity duration-200">
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                        </div>
                      )}
                    </div>

                    {/* Search Suggestions Dropdown */}
                    {showSuggestions && searchSuggestions.length > 0 && (
                      <div className="bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg shadow-lg max-h-60 overflow-y-auto z-[1001] animate-in fade-in slide-in-from-top-1 duration-200">
                        {searchSuggestions.map((suggestion, index) => (
                          <button
                            key={suggestion.place_id}
                            onClick={() => handleAddressSelect(suggestion)}
                            className="w-full text-left px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-700 transition-all duration-200 border-b border-gray-100 dark:border-gray-600 last:border-b-0 focus:outline-none focus:bg-gray-50 dark:focus:bg-gray-700 transform hover:translate-x-1"
                            style={{ animationDelay: `${index * 50}ms` }}
                          >
                            <div className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate transition-colors duration-200">
                              {suggestion.display_name}
                            </div>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Control Buttons Container - Fixed height regardless of search state */}
              <div className="flex items-center gap-2 h-10">
                {/* Vehicles Toggle */}
                <button
                  onClick={() => setShowVehicles(!showVehicles)}
                  className={`flex items-center gap-2 px-3 py-2 h-10 rounded-lg shadow-lg border transition-all duration-300 ease-in-out hover:scale-105 active:scale-95 ${
                    showVehicles
                      ? 'bg-green-500 hover:bg-green-600 border-green-600 text-white'
                      : 'bg-white hover:bg-gray-50 border-gray-300 text-gray-600 dark:bg-gray-800 dark:hover:bg-gray-700 dark:border-gray-600 dark:text-gray-300'
                  }`}
                  title={`${showVehicles ? 'Hide' : 'Show'} Vehicles`}
                >
                  <Car className="w-4 h-4 transition-transform duration-200" />
                  <span className="text-sm font-medium hidden sm:inline">Vehicles</span>
                </button>

                {/* Geofences Toggle */}
                <button
                  onClick={() => setShowGeofences(!showGeofences)}
                  className={`flex items-center gap-2 px-3 py-2 h-10 rounded-lg shadow-lg border transition-all duration-300 ease-in-out hover:scale-105 active:scale-95 ${
                    showGeofences
                      ? 'bg-blue-500 hover:bg-blue-600 border-blue-600 text-white'
                      : 'bg-white hover:bg-gray-50 border-gray-300 text-gray-600 dark:bg-gray-800 dark:hover:bg-gray-700 dark:border-gray-600 dark:text-gray-300'
                  }`}
                  title={`${showGeofences ? 'Hide' : 'Show'} Geofences`}
                >
                  <Shield className="w-4 h-4 transition-transform duration-200" />
                  <span className="text-sm font-medium hidden sm:inline">Geofences</span>
                </button>

                {/* Sidebar Toggle Button */}
                <button
                  onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
                  className="flex items-center justify-center bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 shadow-lg px-3 py-2 h-10 hover:bg-gray-50 dark:hover:bg-gray-700 transition-all duration-300 ease-in-out hover:scale-105 active:scale-95 rounded-lg"
                  title={sidebarCollapsed ? 'Show Sidebar' : 'Hide Sidebar'}
                >
                  <Menu
                    className={`w-4 h-4 text-gray-600 dark:text-gray-300 transition-transform duration-300 ${
                      sidebarCollapsed ? 'rotate-0' : 'rotate-180'
                    }`}
                  />
                </button>
              </div>
            </div>
          </div>

          <MapContainer
            center={mapCenter}
            zoom={13}
            style={{ height: '100%', width: '100%' }}
            zoomControl={false}
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            <MapUpdater center={mapCenter} />

            {/* Vehicle Markers */}
            {showVehicles &&
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

            {/* User Location Marker */}
            {showUserLocation && userLocation && userLocation[0] && userLocation[1] && (
              <Marker
                position={[userLocation[0], userLocation[1]]}
                icon={L.divIcon({
                  className: 'user-location-marker',
                  html: `<div style="
                    width: 16px; 
                    height: 16px; 
                    background: #3b82f6; 
                    border: 2px solid white; 
                    border-radius: 50%; 
                    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
                    position: relative;
                    top: -8px;
                    left: -8px;
                  "></div>`,
                  iconSize: [16, 16],
                  iconAnchor: [8, 8],
                })}
              >
                <Popup>
                  <div className="text-sm">
                    <h4 className="font-medium">Your Location</h4>
                    <p className="text-muted-foreground">Current position</p>
                  </div>
                </Popup>
              </Marker>
            )}

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
        </div>

        {/* Sidebar Backdrop - More prominent on mobile */}
        {!sidebarCollapsed && (
          <div
            className="absolute inset-0 bg-black bg-opacity-10 sm:bg-opacity-10 z-[998] transition-opacity duration-300"
            onClick={() => setSidebarCollapsed(true)}
          />
        )}

        {/* Sidebar - Overlay on top of map */}
        <div
          className={`absolute top-20 right-4 w-full sm:w-80 h-[calc(100vh-174px)] bg-card border border-border shadow-xl rounded-2xl z-[999] transition-all duration-500 ease-in-out transform ${
            sidebarCollapsed ? 'translate-x-full opacity-0' : 'translate-x-0 opacity-100'
          }`}
        >
          <div className="flex flex-col h-full p-4 animate-in slide-in-from-right-4 duration-300">
            {/* Tabs */}
            <div className="flex border-b border-border mb-4">
              <button
                className={`flex-1 px-4 py-2 text-sm font-medium border-b-2 transition-all duration-300 ease-in-out ${
                  activeTab === 'vehicles'
                    ? 'border-primary text-primary bg-primary/5 transform scale-105'
                    : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border hover:bg-accent/50'
                }`}
                onClick={() => {
                  setActiveTab('vehicles');
                  setSearchTerm('');
                  setSelectedItem(null);
                }}
              >
                <Car
                  className={`w-4 h-4 inline mr-2 transition-transform duration-200 ${
                    activeTab === 'vehicles' ? 'scale-110' : ''
                  }`}
                />
                Vehicles ({vehicles.length})
              </button>
              <button
                className={`flex-1 px-4 py-2 text-sm font-medium border-b-2 transition-all duration-300 ease-in-out ${
                  activeTab === 'geofences'
                    ? 'border-primary text-primary bg-primary/5 transform scale-105'
                    : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border hover:bg-accent/50'
                }`}
                onClick={() => {
                  setActiveTab('geofences');
                  setSearchTerm('');
                  setSelectedItem(null);
                }}
              >
                <Shield
                  className={`w-4 h-4 inline mr-2 transition-transform duration-200 ${
                    activeTab === 'geofences' ? 'scale-110' : ''
                  }`}
                />
                Geofences ({geofences.length})
              </button>
            </div>

            {/* Search */}
            <div className="relative mb-4">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4 transition-colors duration-200" />
              <input
                type="text"
                placeholder={`Search ${activeTab}...`}
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary transition-all duration-200 rounded-md"
              />
            </div>

            {/* Add Geofence Button - Only show when geofences tab is active */}
            {activeTab === 'geofences' && (
              <div className="mb-4 animate-in fade-in slide-in-from-top-2 duration-300">
                <button
                  onClick={() => setShowAddGeofenceModal(true)}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-primary text-primary-foreground hover:bg-primary/90 transition-all duration-300 ease-in-out text-sm font-medium rounded-md hover:scale-105 active:scale-95"
                >
                  <Plus className="w-4 h-4 transition-transform duration-200" />
                  Add Geofence
                </button>
              </div>
            )}

            {/* Items List */}
            <div className="flex-1 overflow-y-auto space-y-2">
              {filteredItems.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground animate-in fade-in duration-300">
                  <p>No {activeTab} found</p>
                  {searchTerm && <p className="text-xs mt-1">Try adjusting your search</p>}
                </div>
              ) : (
                filteredItems.map((item, index) => (
                  <div
                    key={item.id}
                    className={`w-full p-3 border border-border cursor-pointer transition-all duration-300 ease-in-out hover:bg-accent hover:scale-[1.02] hover:shadow-md transform animate-in fade-in slide-in-from-left-2 rounded-xl ${
                      selectedItem?.id === item.id
                        ? 'bg-primary/10 border-primary scale-[1.02] shadow-md'
                        : ''
                    }`}
                    style={{ animationDelay: `${index * 50}ms` }}
                    onClick={() => handleItemSelect(item)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="font-medium text-sm truncate transition-colors duration-200">
                          {item.name}
                        </h4>
                        {activeTab === 'vehicles' ? (
                          <div className="mt-1 space-y-1">
                            <p className="text-xs text-muted-foreground transition-colors duration-200">
                              {item.make} {item.model}
                            </p>
                            <p className="text-xs text-muted-foreground transition-colors duration-200">
                              Plate: {item.license_plate}
                            </p>
                            <div className="flex items-center mt-1">
                              <div
                                className={`w-2 h-2 rounded-full mr-2 transition-all duration-300 ${
                                  item.status === 'active'
                                    ? 'bg-green-500 animate-pulse'
                                    : item.status === 'inactive'
                                    ? 'bg-red-500'
                                    : 'bg-yellow-500 animate-pulse'
                                }`}
                              ></div>
                              <span className="text-xs capitalize text-muted-foreground transition-colors duration-200">
                                {item.status}
                              </span>
                            </div>
                          </div>
                        ) : (
                          <div className="mt-1 space-y-1">
                            <p className="text-xs text-muted-foreground truncate transition-colors duration-200">
                              {item.description || 'No description'}
                            </p>
                            <div className="flex items-center mt-1">
                              <div
                                className={`w-2 h-2 rounded-full mr-2 transition-all duration-300 ${
                                  item.type === 'depot'
                                    ? 'bg-blue-500'
                                    : item.type === 'restricted'
                                    ? 'bg-red-500'
                                    : 'bg-purple-500'
                                }`}
                              ></div>
                              <span className="text-xs capitalize text-muted-foreground transition-colors duration-200">
                                {item.type}
                              </span>
                            </div>
                          </div>
                        )}
                      </div>
                      <div className="flex items-center gap-1 ml-2 flex-shrink-0">
                        {activeTab === 'geofences' ? (
                          <>
                            <button
                              onClick={e => handleEditGeofence(item, e)}
                              className="p-1 text-muted-foreground hover:text-primary hover:bg-primary/10 rounded transition-all duration-200 hover:scale-110"
                              title="Edit geofence"
                            >
                              <Edit2 className="w-3 h-3" />
                            </button>
                            <button
                              onClick={e => handleDeleteGeofence(item.id, e)}
                              className="p-1 text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded transition-all duration-200 hover:scale-110"
                              title="Delete geofence"
                            >
                              <Trash2 className="w-3 h-3" />
                            </button>
                          </>
                        ) : (
                          <Navigation className="w-4 h-4 text-muted-foreground transition-transform duration-200 group-hover:scale-110" />
                        )}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Add Geofence Modal */}
      {showAddGeofenceModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-[2000] flex items-center justify-center p-4 animate-in fade-in duration-300">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg max-w-5xl w-full max-h-[90vh] overflow-auto animate-in zoom-in-95 slide-in-from-bottom-4 duration-300 ease-out">
            <GeofenceManager
              showFormOnly={true}
              initialShowForm={true}
              onCancel={() => {
                setShowAddGeofenceModal(false);
                setEditingGeofence(null);
              }}
              onSuccess={handleGeofenceSuccess}
              onGeofenceChange={handleGeofenceChange}
              currentGeofences={geofences}
              editingGeofence={editingGeofence}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default TrackingMapWithSidebar;
