import React, { useState, useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet';
import { Navigation, MapPin, Target, AlertCircle, ChevronLeft, ChevronRight } from 'lucide-react';
import L from 'leaflet';
import { getDriverActiveTrips } from '../backend/api/trips';
import { getCurrentUser } from '../backend/api/auth';
import { getDriverEMPID } from '../backend/api/drivers';

// Fix for default markers in react-leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Custom icons for different markers
const originIcon = new L.Icon({
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  className: 'origin-marker'
});

const destinationIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  className: 'destination-marker'
});

// Current location icon (blue circle)
const currentLocationIcon = new L.DivIcon({
  html: '<div style="background-color: #007acc; width: 20px; height: 20px; border-radius: 50%; border: 3px solid white; box-shadow: 0 0 10px rgba(0,122,204,0.5);"></div>',
  className: 'current-location-marker',
  iconSize: [20, 20],
  iconAnchor: [10, 10]
});

// Map Center Controller Component - keeps map centered on current location
const MapCenterController = ({ currentLocation }) => {
  const map = useMap();

  useEffect(() => {
    if (currentLocation) {
      // Pan to current location smoothly
      map.panTo(currentLocation, {
        animate: true,
        duration: 1.0
      });
    }
  }, [map, currentLocation]);

  return null;
};

// Simple Route Display Component - replaces complex routing machine
const SimpleRouteDisplay = ({ origin, destination, onRouteFound }) => {
  const map = useMap();
  const routeLayerRef = useRef(null);
  const [routeCalculated, setRouteCalculated] = useState(false);

  useEffect(() => {
    if (!origin || !destination || !map || routeCalculated) return;

    // Simple straight line route for basic display
    const createStraightLineRoute = () => {
      try {
        // Remove existing route layer
        if (routeLayerRef.current) {
          map.removeLayer(routeLayerRef.current);
        }

        // Create simple polyline between origin and destination
        routeLayerRef.current = L.polyline([origin, destination], {
          color: '#007acc',
          weight: 4,
          opacity: 0.7,
          dashArray: '10, 5'
        }).addTo(map);

        // Calculate approximate distance and duration
        const distance = map.distance(origin, destination);
        const approximateDuration = Math.max(distance / 50, 300); // Rough estimate: 50m/s average speed, min 5 minutes

        if (onRouteFound) {
          onRouteFound({
            distance: distance,
            duration: approximateDuration
          });
        }

        setRouteCalculated(true);
        console.log('Simple route displayed');
      } catch (error) {
        console.error('Error creating simple route:', error);
      }
    };

    createStraightLineRoute();

    return () => {
      try {
        if (routeLayerRef.current && map) {
          map.removeLayer(routeLayerRef.current);
          routeLayerRef.current = null;
        }
      } catch (error) {
        console.error('Error cleaning up route layer:', error);
      }
    };
  }, [map, origin, destination, onRouteFound]);

  return null;
};

const TripNavigation = () => {
  const [activeTrip, setActiveTrip] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentLocation, setCurrentLocation] = useState(null);
  const [locationError, setLocationError] = useState(null);
  const [routeInfo, setRouteInfo] = useState(null);
  const watchIdRef = useRef(null);
  
  // Default center - Cape Town coordinates
  const defaultCenter = [-33.9249, 18.4241];

  // Get current user ID from authentication
  const getCurrentUserId = () => {
    const user = getCurrentUser();
    return user?.id || user?._id || user?.userId;
  };

  const getEmployeeID = async (security_id) => {
    try {
      const response = await getDriverEMPID(security_id);
      console.log("Response for employee id: ", response);
      return response.data?.data || response.data;
    } catch (error) {
      console.error("Error fetching employee ID:", error);
      return null;
    }
  };

  // Geolocation tracking
  useEffect(() => {
    if (!navigator.geolocation) {
      setLocationError('Geolocation is not supported by this browser');
      return;
    }

    // Check if we're on a secure origin
    const isSecureOrigin = location.protocol === 'https:' || 
                          location.hostname === 'localhost' || 
                          location.hostname === '127.0.0.1';

    if (!isSecureOrigin) {
      console.warn('Geolocation requires HTTPS. Using fallback location.');
      // Set a fallback location (Cape Town coordinates as example) - no warning display
      setCurrentLocation(defaultCenter);
      return;
    }

    const options = {
      enableHighAccuracy: true,
      timeout: 10000,
      maximumAge: 1000
    };

    const success = (position) => {
      const { latitude, longitude } = position.coords;
      console.log('Current location:', { latitude, longitude });
      setCurrentLocation([latitude, longitude]);
      setLocationError(null);
    };

    const error = (err) => {
      console.error('Geolocation error:', err);
      
      // Provide more specific error messages
      let errorMessage = 'Location access denied';
      
      switch(err.code) {
        case err.PERMISSION_DENIED:
          errorMessage = 'Location access denied by user';
          break;
        case err.POSITION_UNAVAILABLE:
          errorMessage = 'Location information unavailable';
          break;
        case err.TIMEOUT:
          errorMessage = 'Location request timed out';
          break;
        default:
          errorMessage = `Location error: ${err.message}`;
          break;
      }
      
      setLocationError(errorMessage);
      // Use fallback location without showing warning for HTTPS issues
      if (err.code === err.PERMISSION_DENIED) {
        setCurrentLocation(defaultCenter);
      }
    };

    // Start watching location
    watchIdRef.current = navigator.geolocation.watchPosition(success, error, options);

    return () => {
      if (watchIdRef.current) {
        navigator.geolocation.clearWatch(watchIdRef.current);
      }
    };
  }, []);

  // Handle route found callback
  const handleRouteFound = (routeData) => {
    console.log('Route data received:', routeData);
    setRouteInfo(routeData);
  };

  // Remove the old fetchDirections and generateBasicDirections functions
  // as they're replaced by Leaflet Routing Machine

  // Fetch active trip data
  useEffect(() => {
    const fetchActiveTrip = async (isInitialLoad = false) => {
      try {
        if (isInitialLoad) {
          setLoading(true);
        }
        
        const driverId = getCurrentUserId();
        
        if (!driverId) {
          throw new Error('No driver ID found');
        }

        const employeeID = await getEmployeeID(driverId);
        if (!employeeID) {
          throw new Error('No employee ID found');
        }

        console.log("Fetching active trip for EMP ID: ", employeeID);
        
        const response = await getDriverActiveTrips(employeeID);
        console.log("Active trip response: ", response);
        console.log("Response type:", typeof response);
        console.log("Response is array:", Array.isArray(response));
        console.log("Response data:", response?.data);
        console.log("Response length:", response?.length);
        
        // Handle different response structures
        let trips = [];
        if (Array.isArray(response)) {
          trips = response;
        } else if (response?.data && Array.isArray(response.data)) {
          trips = response.data;
        } else if (response?.data?.data && Array.isArray(response.data.data)) {
          trips = response.data.data;
        } else if (response && typeof response === 'object') {
          trips = [response]; // Single trip object
        }
        
        console.log("Processed trips:", trips);
        
        if (trips && trips.length > 0) {
          const newTrip = trips[0];
          console.log("New trip found:", newTrip);
          console.log("Trip coordinates - Origin:", newTrip?.origin?.location?.coordinates);
          console.log("Trip coordinates - Destination:", newTrip?.destination?.location?.coordinates);
          
          // Only update trip on initial load or if trip changed
          if (isInitialLoad || !activeTrip || activeTrip.id !== newTrip.id) {
            console.log('New trip detected or initial load');
            setActiveTrip(newTrip);
          } else {
            // Just update the trip data
            console.log('Updating existing trip data');
            setActiveTrip(newTrip);
          }
        } else {
          if (isInitialLoad) {
            setError('No active trip found');
          }
        }
      } catch (err) {
        console.error('Error fetching active trip:', err);
        if (isInitialLoad) {
          setError(err.message);
        }
      } finally {
        if (isInitialLoad) {
          setLoading(false);
        }
      }
    };

    // Initial fetch with full loading state
    fetchActiveTrip(true);

    // Set up interval to fetch every 1000ms (background updates only)
    const intervalId = setInterval(() => {
      fetchActiveTrip(false); // Background update without loading state
    }, 1000);

    // Cleanup interval on component unmount
    return () => {
      clearInterval(intervalId);
    };
  }, []); // Remove activeTrip from dependency array to prevent unnecessary re-runs

  // Extract coordinates and route info from active trip
  const getMapData = () => {
    console.log("getMapData called with activeTrip:", activeTrip);
    
    if (!activeTrip) {
      console.log("No activeTrip, using default center");
      return { center: currentLocation || defaultCenter, zoom: 16 };
    }

    console.log("ActiveTrip structure:", {
      origin: activeTrip.origin,
      destination: activeTrip.destination,
      originCoords: activeTrip.origin?.location?.coordinates,
      destCoords: activeTrip.destination?.location?.coordinates
    });

    const origin = activeTrip.origin?.location?.coordinates;
    const destination = activeTrip.destination?.location?.coordinates;

    console.log("Extracted coordinates:", { origin, destination });

    if (origin && destination) {
      // Convert from [lng, lat] to [lat, lng] for Leaflet
      const originLatLng = [origin[1], origin[0]];
      const destinationLatLng = [destination[1], destination[0]];
      
      console.log("Converted coordinates:", { originLatLng, destinationLatLng });
      
      // Always center on current location if available, otherwise use origin
      const center = currentLocation || originLatLng;
      
      const mapData = {
        center: center,
        zoom: 18, // Higher zoom for navigation
        origin: originLatLng,
        destination: destinationLatLng,
        route: activeTrip.route_info?.coordinates?.map(coord => [coord[0], coord[1]]) || []
      };
      
      console.log("Final map data:", mapData);
      return mapData;
    }

    console.log("No valid coordinates found, using default");
    return { center: currentLocation || defaultCenter, zoom: 16 };
  };

  // Get maneuver icon based on instruction type
  const getManeuverIcon = (maneuver) => {
    if (!maneuver) return <Navigation className="w-4 h-4" />;
    
    switch (maneuver.type) {
      case 'start':
        return <MapPin className="w-4 h-4 text-green-600" />;
      case 'arrive':
        return <MapPin className="w-4 h-4 text-red-600" />;
      case 'turn-left':
        return <ChevronLeft className="w-4 h-4" />;
      case 'turn-right':
        return <ChevronRight className="w-4 h-4" />;
      default:
        return <Navigation className="w-4 h-4" />;
    }
  };

  const mapData = getMapData();

  // Debug logging
  console.log('Component state:', { 
    activeTrip: !!activeTrip, 
    loading,
    error 
  });

  if (loading) {
    return (
      <div className="h-screen w-full flex items-center justify-center">
        <div className="text-lg">Loading trip navigation...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-screen w-full flex items-center justify-center">
        <div className="text-lg text-red-600">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="h-screen w-full">
      {/* Removed location error notification for HTTPS warnings */}
      
      <div className="h-full w-full">
        <MapContainer
          center={mapData.center}
          zoom={mapData.zoom}
          style={{ height: '100%', width: '100%' }}
          className="z-10"
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          
          {/* Map Center Controller - keeps map centered on driver */}
          <MapCenterController currentLocation={currentLocation} />
          
          {/* Origin Marker */}
          {mapData.origin && (
            <Marker position={mapData.origin} icon={originIcon}>
              <Popup>
                <div>
                  <h3 className="font-semibold">Origin</h3>
                  <p className="text-sm">{activeTrip?.origin?.name || 'Starting location'}</p>
                </div>
              </Popup>
            </Marker>
          )}
          
          {/* Destination Marker */}
          {mapData.destination && (
            <Marker position={mapData.destination} icon={destinationIcon}>
              <Popup>
                <div>
                  <h3 className="font-semibold">Destination</h3>
                  <p className="text-sm">{activeTrip?.destination?.name || 'Destination location'}</p>
                </div>
              </Popup>
            </Marker>
          )}

          {/* Current Location Marker */}
          {currentLocation && (
            <Marker position={currentLocation} icon={currentLocationIcon}>
              <Popup>
                <div>
                  <h3 className="font-semibold">Your Location</h3>
                  <p className="text-sm">Current position</p>
                </div>
              </Popup>
            </Marker>
          )}

          {/* Simple route display instead of complex routing machine */}
          {mapData.origin && mapData.destination && (
            <SimpleRouteDisplay
              origin={mapData.origin}
              destination={mapData.destination}
              onRouteFound={handleRouteFound}
            />
          )}
          
          {/* Fallback Route Polyline (if routing machine fails) */}
          {!mapData.origin || !mapData.destination ? (
            mapData.route && mapData.route.length > 0 && (
              <Polyline
                positions={mapData.route}
                color="blue"
                weight={4}
                opacity={0.7}
              />
            )
          ) : null}
        </MapContainer>
      </div>
      {/* Trip Info Overlay */}
      {activeTrip && (
        <div className="absolute top-4 left-4 bg-white rounded-lg shadow-lg p-4 max-w-sm z-[1000]">
          <h2 className="font-semibold text-lg mb-2">{activeTrip.name}</h2>
          {activeTrip.description && (
            <p className="text-sm text-gray-600 mb-2">{activeTrip.description}</p>
          )}
          <div className="text-sm space-y-1">
            <div><strong>Distance:</strong> {
              routeInfo?.distance 
                ? `${(routeInfo.distance / 1000).toFixed(1)} km`
                : activeTrip.route_info?.distance
                  ? `${(activeTrip.route_info.distance / 1000).toFixed(1)} km`
                  : 'Calculating...'
            }</div>
            <div><strong>Est. Duration:</strong> {
              routeInfo?.duration
                ? `${Math.round(routeInfo.duration / 60)} min`
                : activeTrip.route_info?.duration
                  ? `${Math.round(activeTrip.route_info.duration / 60)} min`
                  : 'Calculating...'
            }</div>
            <div><strong>Started:</strong> {new Date(activeTrip.actual_start_time).toLocaleTimeString()}</div>
          </div>
        </div>
      )}

      {/* Turn-by-Turn Directions Panel - REMOVED */}
    </div>
  );
};

export default TripNavigation;
