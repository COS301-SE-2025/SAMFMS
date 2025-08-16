import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Menu, Search, Navigation, Car, User, Locate, LocateFixed, Route } from 'lucide-react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet';
import { getLocation } from '../../backend/api/locations';
import { getVehiclePolyline } from '../../backend/api/trips';
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
  const [vehicleLocations, setVehicleLocations] = useState({});
  const [vehiclePolylines, setVehiclePolylines] = useState({}); // New state for dynamic polylines
  const [showTrips, setShowTrips] = useState(true);
  const [showVehicles, setShowVehicles] = useState(true);
  const [useDynamicRoutes, setUseDynamicRoutes] = useState(true); // Toggle for dynamic vs static routes

  // Address search state
  const [addressSearch, setAddressSearch] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [searchSuggestions, setSearchSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [userLocation, setUserLocation] = useState(null);
  const [showUserLocation, setShowUserLocation] = useState(false);

  // Ref for search container to handle click outside
  const searchContainerRef = useRef(null);

  // Helper function to get vehicle ID from trip data (handles both vehicleId and vehicle_id)
  const getVehicleId = useCallback(trip => {
    return trip.vehicleId || trip.vehicle_id || trip.id;
  }, []);

  // Debug: Log vehicle locations and polylines when they change
  useEffect(() => {
    console.log('Vehicle locations updated:', vehicleLocations);
    console.log('Vehicle polylines updated:', vehiclePolylines);
    console.log('Number of vehicle locations:', Object.keys(vehicleLocations).length);
    console.log('Number of vehicle polylines:', Object.keys(vehiclePolylines).length);
    console.log('Active locations (trips):', activeLocations);
    console.log('Selected trip:', selectedTrip);

    // Debug vehicle IDs
    activeLocations.forEach((trip, index) => {
      console.log(`Trip ${index}:`, {
        id: trip.id,
        vehicleId: getVehicleId(trip),
        originalVehicleId: trip.vehicleId,
        originalVehicle_id: trip.vehicle_id,
      });
    });
  }, [vehicleLocations, vehiclePolylines, activeLocations, selectedTrip, getVehicleId]);

  // Function to fetch vehicle location
  const fetchVehicleLocation = async vehicleId => {
    try {
      const response = await getLocation(vehicleId);
      console.log(`Vehicle ${vehicleId} location:`, response);

      if (
        response.data &&
        response.data.data &&
        Array.isArray(response.data.data) &&
        response.data.data.length > 0
      ) {
        const locationData = response.data.data[0];

        if (locationData.location && locationData.location.coordinates) {
          return {
            id: vehicleId,
            position: [locationData.location.coordinates[1], locationData.location.coordinates[0]],
            speed: locationData.speed || null,
            heading: locationData.heading || null,
            lastUpdated: new Date(locationData.timestamp || locationData.updated_at),
          };
        }

        if (locationData.latitude && locationData.longitude) {
          return {
            id: vehicleId,
            position: [locationData.latitude, locationData.longitude],
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

  // Function to fetch vehicle polyline
  const fetchVehiclePolyline = async vehicleId => {
    try {
      console.log(`Fetching polyline for vehicle ${vehicleId}`);
      const response = await getVehiclePolyline(vehicleId);

      // Handle the response based on your backend structure
      // Assuming the response contains the polyline coordinates
      if (response && response.data) {
        const polylineData = response.data.data;

        return polylineData;
      }

      console.warn(`No valid polyline data found for vehicle ${vehicleId}`);
      return null;
    } catch (error) {
      console.error(`Error fetching polyline for vehicle ${vehicleId}:`, error);
      return null;
    }
  };

  // Function to fetch all vehicle locations and polylines for active trips
  const fetchAllVehicleData = useCallback(async () => {
    const locationPromises = activeLocations.map(async trip => {
      const vehicleId = getVehicleId(trip);
      if (vehicleId) {
        const location = await fetchVehicleLocation(vehicleId);
        return { vehicleId, location };
      }
      return null;
    });

    // Fetch polylines only if dynamic routes are enabled
    const polylinePromises = useDynamicRoutes
      ? activeLocations.map(async trip => {
          const vehicleId = getVehicleId(trip);
          if (vehicleId) {
            const polyline = await fetchVehiclePolyline(vehicleId);
            return { vehicleId, polyline };
          }
          return null;
        })
      : [];

    const [locationResults, polylineResults] = await Promise.all([
      Promise.all(locationPromises),
      Promise.all(polylinePromises),
    ]);

    // Process location results
    const locationsMap = {};
    locationResults.forEach(result => {
      if (result && result.location) {
        locationsMap[result.vehicleId] = result.location;
      }
    });

    // Process polyline results
    const polylinesMap = {};
    polylineResults.forEach(result => {
      if (result && result.polyline) {
        polylinesMap[result.vehicleId] = result.polyline;
      }
    });

    setVehicleLocations(locationsMap);
    setVehiclePolylines(polylinesMap);
  }, [activeLocations, useDynamicRoutes, getVehicleId]);

  // Filter active trips based on search term and selection
  const filteredTrips = activeLocations
    .filter(trip => !selectedTrip || trip.id === selectedTrip.id)
    .filter(
      trip =>
        (trip.vehicle_id || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
        (trip.driver_assignment || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
        (trip.destination.name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
        (trip.status || '').toLowerCase().includes(searchTerm.toLowerCase())
    );

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
            // Keep default location if geolocation fails
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
    setMapBounds(null); // Clear bounds when centering on address
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
      setMapBounds(null); // Clear bounds when centering on user location
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
            setMapBounds(null);
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

  // Clean up timeouts on unmount
  useEffect(() => {
    return () => {
      if (window.addressSearchTimeout) {
        clearTimeout(window.addressSearchTimeout);
      }
    };
  }, []);

  // Handle trip selection - toggle selection if same trip is clicked
  const handleTripSelect = trip => {
    const newSelectedTrip = selectedTrip?.id === trip.id ? null : trip;
    setSelectedTrip(newSelectedTrip);

    // Clear search when selecting/deselecting a trip
    setSearchTerm('');

    // Only set map bounds if we're selecting a trip (not deselecting)
    if (newSelectedTrip) {
      // Check if we have a dynamic polyline for this trip
      const vehicleId = getVehicleId(trip);
      const dynamicPolyline = vehiclePolylines[vehicleId];

      if (useDynamicRoutes && dynamicPolyline && dynamicPolyline.length > 0) {
        // Use dynamic polyline for bounds
        setMapBounds(dynamicPolyline);
        setMapCenter(null);
      } else if (trip.routeCoordinates && trip.routeCoordinates.length > 0) {
        // Fallback to original route coordinates
        setMapBounds(trip.routeCoordinates);
        setMapCenter(null);
      } else {
        // Fallback to centering on destination
        setMapCenter(trip.position);
        setMapBounds(null);
      }
    } else {
      // When deselecting, reset to show all trips
      if (activeLocations.length > 0) {
        const validLocations = activeLocations.filter(
          loc => loc.position && loc.position[0] !== 0 && loc.position[1] !== 0
        );

        if (validLocations.length === 1) {
          setMapCenter(validLocations[0].position);
        } else if (validLocations.length > 1) {
          const avgLat =
            validLocations.reduce((sum, loc) => sum + loc.position[0], 0) / validLocations.length;
          const avgLng =
            validLocations.reduce((sum, loc) => sum + loc.position[1], 0) / validLocations.length;
          setMapCenter([avgLat, avgLng]);
        }
        setMapBounds(null);
      }
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

  // Fetch vehicle data when active locations change and poll for updates
  useEffect(() => {
    if (activeLocations.length === 0) {
      setVehicleLocations({});
      setVehiclePolylines({});
      return;
    }

    // Initial fetch
    fetchAllVehicleData();

    // Set up polling every 5 seconds for live updates
    const dataInterval = setInterval(() => {
      fetchAllVehicleData();
    }, 3000);

    return () => clearInterval(dataInterval);
  }, [activeLocations, fetchAllVehicleData]);

  // Auto-center map when active locations load
  useEffect(() => {
    if (activeLocations.length > 0 && !selectedTrip) {
      const validLocations = activeLocations.filter(
        loc => loc.position && loc.position[0] !== 0 && loc.position[1] !== 0
      );

      if (validLocations.length === 1) {
        setMapCenter(validLocations[0].position);
      } else if (validLocations.length > 1) {
        const avgLat =
          validLocations.reduce((sum, loc) => sum + loc.position[0], 0) / validLocations.length;
        const avgLng =
          validLocations.reduce((sum, loc) => sum + loc.position[1], 0) / validLocations.length;
        setMapCenter([avgLat, avgLng]);
      }
    }
  }, [activeLocations, selectedTrip]);

  // Function to get the polyline coordinates for a trip
  const getTripPolyline = trip => {
    const vehicleId = getVehicleId(trip);
    if (useDynamicRoutes && vehiclePolylines[vehicleId]) {
      return vehiclePolylines[vehicleId];
    }
    return trip.routeCoordinates;
  };

  // Function to get origin coordinates for a trip
  const getTripOrigin = trip => {
    const vehicleId = getVehicleId(trip);
    if (useDynamicRoutes && vehiclePolylines[vehicleId] && vehiclePolylines[vehicleId].length > 0) {
      return vehiclePolylines[vehicleId][0];
    }
    return trip.origin;
  };

  return (
    <div className="h-[600px] relative">
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

        {/* Render route polylines with dynamic or static routes */}
        {showTrips &&
          activeLocations &&
          activeLocations.length > 0 &&
          activeLocations
            .filter(location => !selectedTrip || location.id === selectedTrip.id)
            .map(location => {
              const polylineCoords = getTripPolyline(location);
              const originCoords = getTripOrigin(location);

              return (
                <React.Fragment key={`route-${location.id}`}>
                  {/* Route polyline */}
                  {polylineCoords && polylineCoords.length > 0 && (
                    <Polyline
                      positions={polylineCoords}
                      pathOptions={{
                        color:
                          location.status === 'In Transit'
                            ? '#3b82f6'
                            : location.status === 'At Destination'
                            ? '#22c55e'
                            : '#f59e0b',
                        weight:
                          useDynamicRoutes && vehiclePolylines[getVehicleId(location)] ? 5 : 4,
                        opacity: 0.8,
                        dashArray:
                          useDynamicRoutes && vehiclePolylines[getVehicleId(location)]
                            ? '10, 5'
                            : null,
                      }}
                    />
                  )}

                  {/* Origin marker - Updated to use dynamic origin if available */}
                  {originCoords && originCoords[0] !== 0 && originCoords[1] !== 0 && (
                    <Marker
                      position={originCoords}
                      icon={L.divIcon({
                        html: `<div style="background-color: ${
                          useDynamicRoutes && vehiclePolylines[getVehicleId(location)]
                            ? '#3b82f6'
                            : 'white'
                        }; width: 24px; height: 24px; border-radius: 50%; border: 3px solid #64748b; box-shadow: 0 3px 8px rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center;">
                                 <svg width="14" height="14" viewBox="0 0 24 24" fill="${
                                   useDynamicRoutes && vehiclePolylines[getVehicleId(location)]
                                     ? 'white'
                                     : '#64748b'
                                 }">
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
                            {useDynamicRoutes && vehiclePolylines[getVehicleId(location)]
                              ? 'Current Route Start'
                              : 'Original Start'}
                          </h4>
                          <p className="text-muted-foreground">{location.vehicleName}</p>
                        </div>
                      </Popup>
                    </Marker>
                  )}

                  {/* Destination marker */}
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
                        {useDynamicRoutes && vehiclePolylines[getVehicleId(location)] && (
                          <div className="mt-2 text-xs text-blue-600">
                            📍 Using dynamic route from current location
                          </div>
                        )}
                      </div>
                    </Popup>
                  </Marker>
                </React.Fragment>
              );
            })}

        {/* Legacy markers for trips without routes */}
        {showTrips &&
          activeLocations &&
          activeLocations.length > 0 &&
          activeLocations
            .filter(location => !selectedTrip || location.id === selectedTrip.id)
            .filter(
              location => !getTripPolyline(location) || getTripPolyline(location).length === 0
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

        {/* Render live vehicle location markers */}
        {showVehicles &&
          Object.entries(vehicleLocations)
            .filter(([vehicleId]) => !selectedTrip || vehicleId === getVehicleId(selectedTrip))
            .map(([vehicleId, locationData]) => {
              const trip = activeLocations.find(loc => getVehicleId(loc) === vehicleId);

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
                  zIndexOffset={1000}
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

        {/* User Location Marker */}
        {showUserLocation && userLocation && (
          <Marker
            position={userLocation}
            icon={L.divIcon({
              html: `<div style="background-color: #ef4444; width: 16px; height: 16px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3); display: flex; align-items: center; justify-content: center;">
                       <div style="background-color: white; width: 4px; height: 4px; border-radius: 50%;"></div>
                     </div>`,
              className: 'user-location-marker',
              iconSize: [16, 16],
              iconAnchor: [8, 8],
            })}
          >
            <Popup>
              <div className="text-sm">
                <h4 className="font-semibold flex items-center gap-2">
                  <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                  Your Location
                </h4>
                <p className="text-muted-foreground text-xs">Current position from GPS</p>
              </div>
            </Popup>
          </Marker>
        )}
      </MapContainer>

      {/* Floating Address Search Bar and Toggle Buttons */}
      <div className="absolute top-4 left-4 right-4 z-[1000]">
        <div className="flex items-start gap-3">
          {/* Location Button */}
          <button
            onClick={handleLocationButtonClick}
            className={`flex items-center justify-center rounded-lg shadow-lg border px-3 py-2 h-10 transition-all duration-300 ease-in-out hover:scale-105 active:scale-95 ${
              showUserLocation
                ? 'bg-blue-500 hover:bg-blue-600 border-blue-600 text-white'
                : 'bg-white hover:bg-gray-50 border-gray-300 text-gray-600 dark:bg-card dark:hover:bg-accent dark:border-border dark:text-foreground'
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
                <div className="relative flex items-center bg-white dark:bg-card border border-border rounded-lg shadow-lg transition-all duration-300 ease-in-out h-10">
                  <Search className="absolute left-3 text-muted-foreground w-4 h-4 transition-colors duration-200" />
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
                    className="w-full pl-10 pr-12 py-3 rounded-lg border-0 focus:outline-none focus:ring-2 focus:ring-primary bg-transparent text-foreground text-sm placeholder-muted-foreground transition-all duration-200"
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
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
                    </div>
                  )}
                </div>

                {/* Search Suggestions Dropdown */}
                {showSuggestions && searchSuggestions.length > 0 && (
                  <div className="bg-white dark:bg-card border border-border rounded-lg shadow-lg max-h-60 overflow-y-auto z-[1001] animate-in fade-in slide-in-from-top-1 duration-200">
                    {searchSuggestions.map((suggestion, index) => (
                      <button
                        key={suggestion.place_id}
                        onClick={() => handleAddressSelect(suggestion)}
                        className="w-full text-left px-4 py-3 hover:bg-accent transition-all duration-200 border-b border-border last:border-b-0 focus:outline-none focus:bg-accent transform hover:translate-x-1"
                        style={{ animationDelay: `${index * 50}ms` }}
                      >
                        <div className="text-sm font-medium text-foreground truncate transition-colors duration-200">
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
                  : 'bg-white hover:bg-gray-50 border-gray-300 text-gray-600 dark:bg-card dark:hover:bg-accent dark:border-border dark:text-foreground'
              }`}
              title={`${showVehicles ? 'Hide' : 'Show'} Vehicles`}
            >
              <Car className="w-4 h-4 transition-transform duration-200" />
              <span className="text-sm font-medium hidden sm:inline">Vehicles</span>
            </button>

            {/* Routes Toggle */}
            <button
              onClick={() => setShowTrips(!showTrips)}
              className={`flex items-center gap-2 px-3 py-2 h-10 rounded-lg shadow-lg border transition-all duration-300 ease-in-out hover:scale-105 active:scale-95 ${
                showTrips
                  ? 'bg-blue-500 hover:bg-blue-600 border-blue-600 text-white'
                  : 'bg-white hover:bg-gray-50 border-gray-300 text-gray-600 dark:bg-card dark:hover:bg-accent dark:border-border dark:text-foreground'
              }`}
              title={`${showTrips ? 'Hide' : 'Show'} Trip Routes`}
            >
              <Route className="w-4 h-4 transition-transform duration-200" />
              <span className="text-sm font-medium hidden sm:inline">Routes</span>
            </button>

            {/* Sidebar Toggle Button */}
            <button
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              className="flex items-center justify-center bg-white dark:bg-card border border-border dark:border-border shadow-lg px-3 py-2 h-10 hover:bg-gray-50 dark:hover:bg-accent transition-all duration-300 ease-in-out hover:scale-105 active:scale-95 rounded-lg"
              title={sidebarCollapsed ? 'Show Trip List' : 'Hide Trip List'}
            >
              <Menu
                className={`w-4 h-4 text-gray-600 dark:text-foreground transition-transform duration-300 ${
                  sidebarCollapsed ? 'rotate-0' : 'rotate-180'
                }`}
              />
            </button>
          </div>
        </div>
      </div>

      {/* Sidebar - Enhanced with dynamic route toggle */}
      <div
        className={`absolute top-20 right-4 w-full sm:w-80 h-[calc(100vh-174px)] bg-card border border-border shadow-xl rounded-2xl z-[999] transition-all duration-500 ease-in-out transform ${
          sidebarCollapsed ? 'translate-x-full opacity-0' : 'translate-x-0 opacity-100'
        }`}
      >
        <div className="flex flex-col h-full p-4">
          {/* Header */}
          <div className="flex items-center justify-between mb-4 pb-3 border-b border-border">
            <div className="flex items-center gap-2">
              <Car className="w-5 h-5 text-primary" />
              <h4 className="text-lg font-semibold">
                {selectedTrip ? 'Selected Trip' : 'Active Trips'}
              </h4>
            </div>
            <span className="text-sm text-muted-foreground bg-primary/10 px-2 py-1 rounded-full">
              {selectedTrip ? '1' : activeLocations.length}
            </span>
          </div>

          {/* Display Toggles */}
          <div className="mb-4 p-3 bg-muted/30 rounded-lg border border-border">
            <h5 className="text-sm font-medium mb-3 text-foreground">Map Display</h5>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex flex-col">
                  <span className="text-sm text-muted-foreground">Dynamic Routes</span>
                  <span className="text-xs text-muted-foreground/70">From current location</span>
                </div>
                <button
                  onClick={() => setUseDynamicRoutes(!useDynamicRoutes)}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    useDynamicRoutes ? 'bg-primary' : 'bg-muted-foreground/20'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      useDynamicRoutes ? 'translate-x-6' : 'translate-x-1'
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
              placeholder={selectedTrip ? 'Search selected trip...' : 'Search trips...'}
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary transition-all duration-200 rounded-md"
            />
          </div>

          {/* Show All Trips Button - Only visible when a trip is selected */}
          {selectedTrip && (
            <div className="mb-4">
              <button
                onClick={() => setSelectedTrip(null)}
                className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-primary/10 hover:bg-primary/20 text-primary text-sm rounded-md transition-colors duration-200 border border-primary/20"
              >
                <Car className="w-4 h-4" />
                <span>Show All Trips</span>
              </button>
            </div>
          )}

          {/* Trip List */}
          <div className="flex-1 overflow-y-auto space-y-2">
            {filteredTrips.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <Car className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p>No trips found</p>
                {searchTerm && <p className="text-xs mt-1">Try adjusting your search</p>}
              </div>
            ) : (
              filteredTrips.map((trip, index) => {
                const hasDynamicRoute = useDynamicRoutes && vehiclePolylines[getVehicleId(trip)];
                const hasLiveLocation = vehicleLocations[getVehicleId(trip)];

                return (
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

                        {/* Status indicators for dynamic route and live location */}
                        <div className="flex items-center gap-2 text-xs">
                          {hasDynamicRoute && (
                            <div className="flex items-center gap-1 text-blue-600">
                              <div
                                className="w-2 h-0.5 bg-blue-600"
                                style={{ borderStyle: 'dashed' }}
                              ></div>
                              <span>Dynamic Route</span>
                            </div>
                          )}
                          {hasLiveLocation && (
                            <div className="flex items-center gap-1 text-green-600">
                              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                              <span>Live GPS</span>
                            </div>
                          )}
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

                      {/* Action buttons */}
                      <div className="pt-2 space-y-2">
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
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ActiveTripsMap;
