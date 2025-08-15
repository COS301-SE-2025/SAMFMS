import React, { useState, useEffect, useRef, useCallback } from 'react';
import { MapPin, Menu, Search, Navigation, Car, Clock, User, Locate } from 'lucide-react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet';
import { getLocation } from '../../backend/api/locations';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix for default markers in react-leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Custom vehicle icon for active trips map
const createVehicleIcon = status => {
  const color =
    status === 'In Transit' ? '#3b82f6' : status === 'At Destination' ? '#22c55e' : '#f59e0b';
  return L.divIcon({
    html: `<div style="background-color: ${color}; width: 20px; height: 20px; border-radius: 50%; border: 2px solid white; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">
             <svg width="12" height="12" viewBox="0 0 24 24" fill="white">
               <path d="M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l4.414 4.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-2M8 7H6a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2v-2"/>
             </svg>
           </div>`,
    className: 'custom-vehicle-marker',
    iconSize: [20, 20],
    iconAnchor: [10, 10],
  });
};

// Map updater component to center on selected items
const MapUpdater = ({ center, zoom = 13, bounds = null }) => {
  const map = useMap();

  useEffect(() => {
    if (bounds && bounds.length > 0) {
      // Fit bounds to show the entire route
      map.fitBounds(bounds, { padding: [20, 20] });
    } else if (center && center[0] && center[1]) {
      map.setView(center, zoom);
    }
  }, [center, zoom, bounds, map]);

  return null;
};

const ActiveTripsMap = ({ activeLocations = [] }) => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTrip, setSelectedTrip] = useState(null);
  const [mapCenter, setMapCenter] = useState([37.7749, -122.4194]);
  const [mapBounds, setMapBounds] = useState(null);
  const [vehicleLocations, setVehicleLocations] = useState({}); // Store vehicle locations by vehicle ID
  const [showTrips, setShowTrips] = useState(true); // Toggle for trip display
  const [showVehicles, setShowVehicles] = useState(true); // Toggle for vehicle display

  // Debug: Log vehicle locations when they change
  useEffect(() => {
    console.log('Vehicle locations updated:', vehicleLocations);
    console.log('Number of vehicle locations:', Object.keys(vehicleLocations).length);
    console.log('Active locations (trips):', activeLocations);
    // Log which vehicle IDs we're trying to fetch locations for
    const vehicleIds = activeLocations.map(loc => loc.vehicleId).filter(Boolean);
    console.log('Vehicle IDs to track:', vehicleIds);
  }, [vehicleLocations, activeLocations]);

  // Function to fetch vehicle location
  const fetchVehicleLocation = async vehicleId => {
    try {
      const response = await getLocation(vehicleId);
      // Handle the response structure based on the API response you provided
      console.log(`Vehicle ${vehicleId} location:`, response);

      // Handle the nested response structure: response.data.data is an array of location objects
      if (
        response.data &&
        response.data.data &&
        Array.isArray(response.data.data) &&
        response.data.data.length > 0
      ) {
        const locationData = response.data.data[0]; // Take the first (most recent) location

        if (locationData.location && locationData.location.coordinates) {
          return {
            id: vehicleId,
            position: [locationData.location.coordinates[1], locationData.location.coordinates[0]], // [lat, lng] for Leaflet
            speed: locationData.speed || null,
            heading: locationData.heading || null,
            lastUpdated: new Date(locationData.timestamp || locationData.updated_at),
          };
        }

        // Fallback to direct coordinates if location.coordinates doesn't exist
        if (locationData.latitude && locationData.longitude) {
          return {
            id: vehicleId,
            position: [locationData.latitude, locationData.longitude], // [lat, lng] for Leaflet
            speed: locationData.speed || null,
            heading: locationData.heading || null,
            lastUpdated: new Date(locationData.timestamp || locationData.updated_at),
          };
        }
      }

      console.warn(`No valid location data found for vehicle ${vehicleId}`);
      return null;
    } catch (error) {
      console.error(`Error fetching location for vehicle ${vehicleId}:`, error);
      return null;
    }
  };

  // Function to fetch all vehicle locations for active trips
  const fetchAllVehicleLocations = useCallback(async () => {
    const locationPromises = activeLocations.map(async trip => {
      if (trip.vehicleId) {
        const location = await fetchVehicleLocation(trip.vehicleId);
        return { vehicleId: trip.vehicleId, location };
      }
      return null;
    });

    const results = await Promise.all(locationPromises);
    const locationsMap = {};

    results.forEach(result => {
      if (result && result.location) {
        locationsMap[result.vehicleId] = result.location;
      }
    });

    setVehicleLocations(locationsMap);
  }, [activeLocations]);

  // Filter active trips based on search term
  const filteredTrips = activeLocations.filter(
    trip =>
      (trip.vehicle_id || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
      (trip.driver_assignment || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
      (trip.destination.name || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
      (trip.status || "").toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Handle trip selection
  const handleTripSelect = trip => {
    setSelectedTrip(trip);

    // If the trip has route coordinates, fit the map to show the entire route
    if (trip.routeCoordinates && trip.routeCoordinates.length > 0) {
      setMapBounds(trip.routeCoordinates);
      setMapCenter(null); // Don't use center when using bounds
    } else {
      // Fallback to centering on destination
      setMapCenter(trip.position);
      setMapBounds(null);
    }
  };

  // Handle escape key to close sidebar
  useEffect(() => {
    const handleKeyDown = event => {
      if (event.key === 'Escape' && !sidebarCollapsed) {
        setSidebarCollapsed(true);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [sidebarCollapsed]);

  // Fetch vehicle locations when active locations change and poll for updates
  useEffect(() => {
    if (activeLocations.length === 0) {
      setVehicleLocations({});
      return;
    }

    // Initial fetch
    fetchAllVehicleLocations();

    // Set up polling every 3 seconds for live location updates
    const locationInterval = setInterval(() => {
      fetchAllVehicleLocations();
    }, 500);

    return () => clearInterval(locationInterval);
  }, [activeLocations, fetchAllVehicleLocations]); // Re-fetch when active trips change

  // Auto-center map when active locations load
  useEffect(() => {
    if (activeLocations.length > 0 && !selectedTrip) {
      // Center on the first location or calculate center of all locations
      const validLocations = activeLocations.filter(
        loc => loc.position && loc.position[0] !== 0 && loc.position[1] !== 0
      );

      if (validLocations.length === 1) {
        setMapCenter(validLocations[0].position);
      } else if (validLocations.length > 1) {
        // Calculate approximate center of all locations
        const avgLat =
          validLocations.reduce((sum, loc) => sum + loc.position[0], 0) / validLocations.length;
        const avgLng =
          validLocations.reduce((sum, loc) => sum + loc.position[1], 0) / validLocations.length;
        setMapCenter([avgLat, avgLng]);
      }
    }
  }, [activeLocations, selectedTrip]);

  return (
    <div className="h-96 relative">
      <MapContainer
        center={mapCenter}
        zoom={12}
        style={{ height: '100%', width: '100%' }}
        className="rounded-b-xl"
        zoomControl={false}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />
        <MapUpdater center={mapCenter} zoom={13} bounds={mapBounds} />

        {/* Render route polylines */}
        {showTrips &&
          activeLocations &&
          activeLocations.length > 0 &&
          activeLocations.map(location => (
            <React.Fragment key={`route-${location.id}`}>
              {/* Route polyline */}
              {location.routeCoordinates && location.routeCoordinates.length > 0 && (
                <Polyline
                  positions={location.routeCoordinates}
                  pathOptions={{
                    color:
                      location.status === 'In Transit'
                        ? '#3b82f6'
                        : location.status === 'At Destination'
                        ? '#22c55e'
                        : '#f59e0b',
                    weight: 4,
                    opacity: 0.8,
                  }}
                />
              )}

              {/* Origin marker - White flag for starting point */}
              {location.origin && location.origin[0] !== 0 && location.origin[1] !== 0 && (
                <Marker
                  position={location.origin}
                  icon={L.divIcon({
                    html: `<div style="background-color: white; width: 24px; height: 24px; border-radius: 50%; border: 3px solid #64748b; box-shadow: 0 3px 8px rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center;">
                               <svg width="14" height="14" viewBox="0 0 24 24" fill="#64748b">
                                 <path d="M14.4,6H20V16H13L11,13V21A1,1 0 0,1 10,22H9A1,1 0 0,1 8,21V4A1,1 0 0,1 9,3H10A1,1 0 0,1 11,4V6H14.4L14.4,6Z"/>
                               </svg>
                             </div>`,
                    className: 'custom-origin-marker',
                    iconSize: [24, 24],
                    iconAnchor: [12, 12],
                  })}
                >
                  <Popup>
                    <div className="text-sm">
                      <h4 className="font-semibold flex items-center gap-2">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="#64748b">
                          <path d="M14.4,6H20V16H13L11,13V21A1,1 0 0,1 10,22H9A1,1 0 0,1 8,21V4A1,1 0 0,1 9,3H10A1,1 0 0,1 11,4V6H14.4L14.4,6Z" />
                        </svg>
                        Starting Point
                      </h4>
                      <p className="text-muted-foreground">{location.vehicleName}</p>
                    </div>
                  </Popup>
                </Marker>
              )}

              {/* Destination marker - Green flag for end location */}
              <Marker
                position={location.position}
                icon={L.divIcon({
                  html: `<div style="background-color: #22c55e; width: 28px; height: 28px; border-radius: 50%; border: 3px solid white; box-shadow: 0 4px 10px rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center;">
                             <svg width="16" height="16" viewBox="0 0 24 24" fill="white">
                               <path d="M14.4,6H20V16H13L11,13V21A1,1 0 0,1 10,22H9A1,1 0 0,1 8,21V4A1,1 0 0,1 9,3H10A1,1 0 0,1 11,4V6H14.4L14.4,6Z"/>
                             </svg>
                           </div>`,
                  className: 'custom-destination-marker',
                  iconSize: [28, 28],
                  iconAnchor: [14, 14],
                })}
              >
                <Popup>
                  <div className="text-sm">
                    <h4 className="font-semibold flex items-center gap-2">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="#22c55e">
                        <path d="M14.4,6H20V16H13L11,13V21A1,1 0 0,1 10,22H9A1,1 0 0,1 8,21V4A1,1 0 0,1 9,3H10A1,1 0 0,1 11,4V6H14.4L14.4,6Z" />
                      </svg>
                      Destination
                    </h4>
                    <p className="text-muted-foreground">{location.vehicleName}</p>
                    <p className="text-muted-foreground">Driver: {location.driver}</p>
                    <p className="text-muted-foreground">Going to: {location.destination}</p>
                    <div className="flex items-center gap-2 mt-2">
                      <div
                        className={`w-2 h-2 rounded-full ${
                          location.status === 'In Transit'
                            ? 'bg-blue-500'
                            : location.status === 'At Destination'
                            ? 'bg-green-500'
                            : 'bg-orange-500'
                        }`}
                      ></div>
                      <span className="text-xs">{location.status}</span>
                    </div>
                    <div className="mt-1">
                      <div className="flex justify-between text-xs">
                        <span>Progress</span>
                        <span>{location.progress}%</span>
                      </div>
                      <div className="w-full bg-muted rounded-full h-1.5 mt-1">
                        <div
                          className="bg-primary h-1.5 rounded-full transition-all duration-300"
                          style={{ width: `${location.progress}%` }}
                        ></div>
                      </div>
                    </div>
                  </div>
                </Popup>
              </Marker>
            </React.Fragment>
          ))}

        {/* Legacy markers (keeping for backwards compatibility - remove these when not needed) */}
        {showTrips &&
          activeLocations &&
          activeLocations.length > 0 &&
          activeLocations
            .filter(
              location => !location.routeCoordinates || location.routeCoordinates.length === 0
            )
            .map(location => (
              <Marker
                key={location.id}
                position={location.position}
                icon={createVehicleIcon(location.status)}
              >
                <Popup>
                  <div className="text-sm">
                    <h4 className="font-semibold">{location.vehicleName}</h4>
                    <p className="text-muted-foreground">Driver: {location.driver}</p>
                    <p className="text-muted-foreground">Going to: {location.destination}</p>
                    <div className="flex items-center gap-2 mt-2">
                      <div
                        className={`w-2 h-2 rounded-full ${
                          location.status === 'In Transit'
                            ? 'bg-blue-500'
                            : location.status === 'At Destination'
                            ? 'bg-green-500'
                            : 'bg-orange-500'
                        }`}
                      ></div>
                      <span className="text-xs">{location.status}</span>
                    </div>
                    <div className="mt-1">
                      <div className="flex justify-between text-xs">
                        <span>Progress</span>
                        <span>{location.progress}%</span>
                      </div>
                      <div className="w-full bg-muted rounded-full h-1.5 mt-1">
                        <div
                          className="bg-primary h-1.5 rounded-full transition-all duration-300"
                          style={{ width: `${location.progress}%` }}
                        ></div>
                      </div>
                    </div>
                  </div>
                </Popup>
              </Marker>
            ))}

        {/* Render live vehicle location markers - LAST to ensure they appear on top */}
        {showVehicles &&
          Object.entries(vehicleLocations).map(([vehicleId, locationData]) => {
            // Find the corresponding trip for this vehicle
            const trip = activeLocations.find(loc => loc.vehicleId === vehicleId);

            return (
              <Marker
                key={`live-vehicle-${vehicleId}`}
                position={locationData.position}
                icon={L.divIcon({
                  html: `<div style="display: flex; align-items: center; justify-content: center; z-index: 1000; position: relative;">
                           <svg width="20" height="20" viewBox="0 0 24 24" fill="#3b82f6" style="filter: drop-shadow(0 2px 4px rgba(0,0,0,0.5));">
                             <path d="M5,11L6.5,6.5H17.5L19,11M17.5,16A1.5,1.5 0 0,1 16,14.5A1.5,1.5 0 0,1 17.5,13A1.5,1.5 0 0,1 19,14.5A1.5,1.5 0 0,1 17.5,16M6.5,16A1.5,1.5 0 0,1 5,14.5A1.5,1.5 0 0,1 6.5,13A1.5,1.5 0 0,1 8,14.5A1.5,1.5 0 0,1 6.5,16M18.92,6C18.72,5.42 18.16,5 17.5,5H6.5C5.84,5 5.28,5.42 5.08,6L3,12V20A1,1 0 0,0 4,21H5A1,1 0 0,0 6,20V19H18V20A1,1 0 0,0 19,21H20A1,1 0 0,0 21,20V12L18.92,6Z"/>
                           </svg>
                         </div>`,
                  className: 'live-vehicle-marker',
                  iconSize: [20, 20],
                  iconAnchor: [10, 10],
                })}
                zIndexOffset={1000} // Ensure this marker appears above all others
              >
                <Popup>
                  <div className="text-sm">
                    <h4 className="font-semibold flex items-center gap-2">
                      <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
                      Live Vehicle Location
                    </h4>
                    <p className="text-muted-foreground">
                      Vehicle: {trip?.vehicleName || `Vehicle ${vehicleId}`}
                    </p>
                    <p className="text-muted-foreground">Driver: {trip?.driver || 'Unknown'}</p>
                    {locationData.speed !== null && (
                      <p className="text-xs text-muted-foreground">
                        Speed: {Math.round(locationData.speed)} km/h
                      </p>
                    )}
                    {locationData.heading !== null && (
                      <p className="text-xs text-muted-foreground">
                        Heading: {Math.round(locationData.heading)}°
                      </p>
                    )}
                    <p className="text-xs text-muted-foreground mt-1">
                      Last updated: {locationData.lastUpdated?.toLocaleTimeString() || 'Unknown'}
                    </p>
                  </div>
                </Popup>
              </Marker>
            );
          })}
      </MapContainer>

      {/* Sidebar Toggle Button */}
      <div className="absolute top-4 left-4 z-[1000]">
        <button
          onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
          className="bg-card border border-border hover:bg-accent text-foreground p-2 rounded-lg shadow-lg transition-all duration-300 hover:scale-105 active:scale-95"
          title={sidebarCollapsed ? 'Show Trip List' : 'Hide Trip List'}
        >
          <Menu
            className={`w-5 h-5 transition-transform duration-300 ${
              sidebarCollapsed ? 'rotate-0' : 'rotate-180'
            }`}
          />
        </button>
      </div>

      {/* Map Controls Overlay */}
      <div className="absolute top-4 right-4 flex flex-col gap-2 z-[1000]">
        <div className="bg-white dark:bg-card border border-border rounded-lg shadow-lg p-2">
          <div className="flex flex-col gap-2 text-sm">
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                <span className="text-muted-foreground">In Transit</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                <span className="text-muted-foreground">At Destination</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 bg-orange-500 rounded-full"></div>
                <span className="text-muted-foreground">Loading</span>
              </div>
            </div>
            <div className="flex items-center gap-2 border-t border-border pt-2">
              <div className="flex items-center gap-1">
                <div className="w-3 h-0.5 bg-blue-500"></div>
                <span className="text-muted-foreground text-xs">Route</span>
              </div>
              <div className="flex items-center gap-1">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="#64748b">
                  <path d="M14.4,6H20V16H13L11,13V21A1,1 0 0,1 10,22H9A1,1 0 0,1 8,21V4A1,1 0 0,1 9,3H10A1,1 0 0,1 11,4V6H14.4L14.4,6Z" />
                </svg>
                <span className="text-muted-foreground text-xs">Start</span>
              </div>
              <div className="flex items-center gap-1">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="#22c55e">
                  <path d="M14.4,6H20V16H13L11,13V21A1,1 0 0,1 10,22H9A1,1 0 0,1 8,21V4A1,1 0 0,1 9,3H10A1,1 0 0,1 11,4V6H14.4L14.4,6Z" />
                </svg>
                <span className="text-muted-foreground text-xs">End</span>
              </div>
              <div className="flex items-center gap-1">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="#3b82f6">
                  <path d="M5,11L6.5,6.5H17.5L19,11M17.5,16A1.5,1.5 0 0,1 16,14.5A1.5,1.5 0 0,1 17.5,13A1.5,1.5 0 0,1 19,14.5A1.5,1.5 0 0,1 17.5,16M6.5,16A1.5,1.5 0 0,1 5,14.5A1.5,1.5 0 0,1 6.5,13A1.5,1.5 0 0,1 8,14.5A1.5,1.5 0 0,1 6.5,16M18.92,6C18.72,5.42 18.16,5 17.5,5H6.5C5.84,5 5.28,5.42 5.08,6L3,12V20A1,1 0 0,0 4,21H5A1,1 0 0,0 6,20V19H18V20A1,1 0 0,0 19,21H20A1,1 0 0,0 21,20V12L18.92,6Z" />
                </svg>
                <span className="text-muted-foreground text-xs">Live Vehicle</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Sidebar Backdrop */}
      {!sidebarCollapsed && (
        <div
          className="absolute inset-0 bg-black bg-opacity-10 z-[998] transition-opacity duration-300"
          onClick={() => setSidebarCollapsed(true)}
        />
      )}

      {/* Sidebar - Overlay on left side */}
      <div
        className={`absolute top-0 left-0 w-80 h-full bg-card border-r border-border shadow-xl z-[999] transition-all duration-500 ease-in-out transform ${
          sidebarCollapsed ? '-translate-x-full opacity-0' : 'translate-x-0 opacity-100'
        }`}
      >
        <div className="flex flex-col h-full p-4">
          {/* Header */}
          <div className="flex items-center justify-between mb-4 pb-3 border-b border-border">
            <div className="flex items-center gap-2">
              <Car className="w-5 h-5 text-primary" />
              <h4 className="text-lg font-semibold">Active Trips</h4>
            </div>
            <span className="text-sm text-muted-foreground bg-primary/10 px-2 py-1 rounded-full">
              {activeLocations.length}
            </span>
          </div>

          {/* Display Toggles */}
          <div className="mb-4 p-3 bg-muted/30 rounded-lg border border-border">
            <h5 className="text-sm font-medium mb-3 text-foreground">Map Display</h5>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Show Trip Routes</span>
                <button
                  onClick={() => setShowTrips(!showTrips)}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    showTrips ? 'bg-primary' : 'bg-muted-foreground/20'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      showTrips ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Show Live Vehicles</span>
                <button
                  onClick={() => setShowVehicles(!showVehicles)}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    showVehicles ? 'bg-primary' : 'bg-muted-foreground/20'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      showVehicles ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>
            </div>
          </div>

          {/* Search */}
          <div className="relative mb-4">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
            <input
              type="text"
              placeholder="Search trips..."
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary transition-all duration-200 rounded-md"
            />
          </div>

          {/* Trip List */}
          <div className="flex-1 overflow-y-auto space-y-2">
            {filteredTrips.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <Car className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p>No trips found</p>
                {searchTerm && <p className="text-xs mt-1">Try adjusting your search</p>}
              </div>
            ) : (
              filteredTrips.map((trip, index) => (
                <div
                  key={trip.id}
                  className={`p-3 border border-border cursor-pointer transition-all duration-300 ease-in-out hover:bg-accent hover:scale-[1.02] hover:shadow-md transform rounded-xl ${
                    selectedTrip?.id === trip.id
                      ? 'bg-primary/10 border-primary scale-[1.02] shadow-md'
                      : ''
                  }`}
                  style={{ animationDelay: `${index * 50}ms` }}
                  onClick={() => handleTripSelect(trip)}
                >
                  <div className="space-y-2">
                    <div className="flex items-start justify-between">
                      <h5 className="font-medium text-sm truncate flex-1">{trip.vehicleName}</h5>
                      <div className="flex items-center ml-2">
                        <div
                          className={`w-2 h-2 rounded-full mr-1 ${
                            trip.status === 'In Transit'
                              ? 'bg-blue-500 animate-pulse'
                              : trip.status === 'At Destination'
                              ? 'bg-green-500'
                              : 'bg-orange-500 animate-pulse'
                          }`}
                        ></div>
                        <span className="text-xs text-muted-foreground capitalize">
                          {trip.status.toLowerCase()}
                        </span>
                      </div>
                    </div>

                    <div className="space-y-1">
                      <div className="flex items-center text-xs text-muted-foreground">
                        <User className="w-3 h-3 mr-1" />
                        <span className="truncate">{trip.driver}</span>
                      </div>

                      <div className="flex items-center text-xs text-muted-foreground">
                        <Navigation className="w-3 h-3 mr-1" />
                        <span className="truncate">{trip.destination}</span>
                      </div>
                    </div>

                    {/* Progress bar */}
                    <div className="mt-2">
                      <div className="flex justify-between text-xs text-muted-foreground mb-1">
                        <span>Progress</span>
                        <span>{trip.progress}%</span>
                      </div>
                      <div className="w-full bg-muted rounded-full h-1.5">
                        <div
                          className={`h-1.5 rounded-full transition-all duration-300 ${
                            trip.status === 'In Transit'
                              ? 'bg-blue-500'
                              : trip.status === 'At Destination'
                              ? 'bg-green-500'
                              : 'bg-orange-500'
                          }`}
                          style={{ width: `${trip.progress}%` }}
                        ></div>
                      </div>
                    </div>

                    {/* Action button */}
                    <div className="pt-2">
                      <button
                        onClick={e => {
                          e.stopPropagation();
                          handleTripSelect(trip);
                        }}
                        className="w-full flex items-center justify-center gap-1 px-2 py-1 bg-primary/10 hover:bg-primary/20 text-primary text-xs rounded-md transition-colors duration-200"
                      >
                        <Locate className="w-3 h-3" />
                        <span>Focus on Map</span>
                      </button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ActiveTripsMap;
