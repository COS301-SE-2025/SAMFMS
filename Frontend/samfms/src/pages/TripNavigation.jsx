import React, { useState, useEffect, useCallback } from 'react';
import { MapPin, Clock, User, Car, Navigation, Square, Phone, MessageCircle } from 'lucide-react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet';
import { getDriverActiveTrips, finishTrip } from '../backend/api/trips';
import { getCurrentUser } from '../backend/api/auth';
import { getDriverEMPID, TripFinishedStatus } from '../backend/api/drivers';
import { getLocation } from '../backend/api/locations';
import { getVehiclePolyline } from '../backend/api/trips';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix for default markers in react-leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Map updater component to follow the vehicle
const MapUpdater = ({ center, bounds = null }) => {
  const map = useMap();

  useEffect(() => {
    if (bounds && bounds.length > 0) {
      // Fit bounds to show the entire route
      map.fitBounds(bounds, { padding: [20, 20] });
    } else if (center && center[0] && center[1]) {
      map.setView(center, 16); // Higher zoom for driver follow mode
    }
  }, [center, bounds, map]);

  return null;
};

const ActiveTrip = ({ onTripEnded }) => {
  const [activeTrip, setActiveTrip] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [endingTrip, setEndingTrip] = useState(false);
  const [canEndTrip, setCanEndTrip] = useState(false);
  const [statusCheckInterval, setStatusCheckInterval] = useState(null);
  
  // Map-related state
  const [mapCenter, setMapCenter] = useState([37.7749, -122.4194]);
  const [mapBounds, setMapBounds] = useState(null);
  const [vehicleLocation, setVehicleLocation] = useState(null);
  const [vehiclePolyline, setVehiclePolyline] = useState(null);

  // Get current user ID from authentication
  const getCurrentUserId = () => {
    const user = getCurrentUser();
    return user?.id || user?._id || user?.userId;
  };

  const getEmployeeID = async (security_id) => {
    try {
      const response = await getDriverEMPID(security_id);
      const employee_id = response.data;
      return employee_id;
    } catch (error) {
      console.error("Error fetching employee ID:", error);
      return null;
    }
  };

  // Helper function to get vehicle ID from trip data
  const getVehicleId = useCallback(trip => {
    return trip.vehicleId || trip.vehicle_id || trip.id;
  }, []);

  // Function to check if trip is finished
  const checkTripFinished = async (employeeId) => {
    try {
      const isFinished = await TripFinishedStatus(employeeId);
      setCanEndTrip(isFinished);
      return isFinished;
    } catch (error) {
      console.error('Error checking trip status:', error);
      return false;
    }
  };

  // Function to fetch vehicle location
  const fetchVehicleLocation = async vehicleId => {
    try {
      const response = await getLocation(vehicleId);

      // Handle nested data structure: response.data.data.data
      let locationData = null;
      
      if (response.data?.data?.data) {
        // Handle case where data is nested three levels deep
        locationData = response.data.data.data;
      } else if (response.data?.data && Array.isArray(response.data.data) && response.data.data.length > 0) {
        // Handle case where data is an array at second level
        locationData = response.data.data[0];
      } else if (response.data?.data) {
        // Handle case where data is directly at second level
        locationData = response.data.data;
      }

      if (locationData) {
        // Try coordinates from location object first
        if (locationData.location && locationData.location.coordinates && locationData.location.coordinates.length >= 2) {
          return {
            id: vehicleId,
            position: [locationData.location.coordinates[1], locationData.location.coordinates[0]], // [lat, lng]
            speed: locationData.speed || null,
            heading: locationData.heading || null,
            lastUpdated: new Date(locationData.timestamp || locationData.updated_at),
          };
        }

        // Fallback to direct latitude/longitude properties
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
      const response = await getVehiclePolyline(vehicleId);

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

  // Function to fetch vehicle data (location and polyline)
  const fetchVehicleData = useCallback(async () => {
    if (!activeTrip) return;

    const vehicleId = getVehicleId(activeTrip);
    if (!vehicleId) return;

    try {
      const [location, polyline] = await Promise.all([
        fetchVehicleLocation(vehicleId),
        fetchVehiclePolyline(vehicleId),
      ]);

      if (location) {
        setVehicleLocation(location);
        // Update map center to follow the vehicle
        setMapCenter(location.position);
      }

      if (polyline) {
        setVehiclePolyline(polyline);
      }
    } catch (error) {
      console.error('Error fetching vehicle data:', error);
    }
  }, [activeTrip, getVehicleId]);

  // Start monitoring trip finish status
  const startStatusMonitoring = async (employeeId) => {
    // Don't start if already monitoring
    if (statusCheckInterval) {
      return;
    }

    const interval = setInterval(async () => {
      await checkTripFinished(employeeId);
    }, 500); // Check every 30 seconds

    setStatusCheckInterval(interval);
    
    // Also check immediately
    await checkTripFinished(employeeId);
  };

  // Stop monitoring trip finish status
  const stopStatusMonitoring = () => {
    if (statusCheckInterval) {
      clearInterval(statusCheckInterval);
      setStatusCheckInterval(null);
    }
    setCanEndTrip(false);
  };

  // Fetch active trip
  const fetchActiveTrip = async () => {
    try {
      setError(null);
      
      const driverId = getCurrentUserId();
      if (!driverId) {
        throw new Error('No driver ID found');
      }

      const employeeID = await getEmployeeID(driverId);
      if (!employeeID?.data) {
        throw new Error('No employee ID found');
      }
      
      
      const response = await getDriverActiveTrips(employeeID.data);
      
      if (response && response.length > 0) {
        const trip = response[0]; // Get the first active trip
        setActiveTrip(trip);
        
        // Start monitoring trip finish status
        await startStatusMonitoring(employeeID.data);
      } else {
        setActiveTrip(null);
        stopStatusMonitoring();
      }
    } catch (err) {
      console.error('Error fetching active trip:', err);
      setError(err.message);
      setActiveTrip(null);
      stopStatusMonitoring();
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchActiveTrip();

    // Cleanup interval on unmount
    return () => {
      if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
      }
    };
  }, []);

  // Fetch vehicle data when active trip changes and poll for updates
  useEffect(() => {
    if (!activeTrip) {
      setVehicleLocation(null);
      setVehiclePolyline(null);
      return;
    }

    // Initial fetch
    fetchVehicleData();

    // Set up polling every 3 seconds for live updates
    const dataInterval = setInterval(() => {
      fetchVehicleData();
    }, 3000);

    return () => clearInterval(dataInterval);
  }, [activeTrip, fetchVehicleData]);

  const formatTripData = trip => {
    if (!trip) return null;
    
    return {
      id: trip.id || trip._id,
      name: trip.name || 'Active Trip',
      startLocation: trip.origin?.address || trip.origin?.name || 'Unknown Location',
      endLocation: trip.destination?.address || trip.destination?.name || 'Unknown Location',
      startTime: trip.scheduledStartTime
        ? new Date(trip.scheduledStartTime).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          })
        : 'Unknown Time',
      endTime: trip.scheduledEndTime
        ? new Date(trip.scheduledEndTime).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          })
        : null,
      actualStartTime: trip.actual_start_time
        ? new Date(trip.actual_start_time).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          })
        : null,
      passenger: trip.passenger_name || 'Unknown Passenger',
      passengerPhone: trip.passenger_phone || null,
      vehicle: {
        model: trip.vehicle_model || 'Unknown Vehicle',
        registration: trip.vehicle_registration || 'Unknown',
      },
      status: trip.status || 'in-progress',
      distance: trip.estimatedDistance ? `${trip.estimatedDistance} km` : 'Unknown distance',
      estimatedDuration: trip.estimated_duration
        ? `${trip.estimated_duration}m`
        : 'Unknown duration',
      // Add position for map display
      position: trip.destination?.coordinates ? [trip.destination.coordinates[1], trip.destination.coordinates[0]] : null,
      origin: trip.origin?.coordinates ? [trip.origin.coordinates[1], trip.origin.coordinates[0]] : null,
      routeCoordinates: trip.routeCoordinates || null,
    };
  };

  // Handle ending a trip
  const handleEndTrip = async () => {
    if (!activeTrip) return;
    
    setEndingTrip(true);
    
    try {
      const now = new Date().toISOString();
      const data = {
        "actual_end_time": now,
        "status": "completed"
      }
      
      const tripId = activeTrip.id || activeTrip._id;
      console.log("Ending trip id: ", tripId);
      
      const response = await finishTrip(tripId, data);
      console.log("Response for ending trip: ", response);
      
      // Stop monitoring
      stopStatusMonitoring();
      
      // Clear active trip
      setActiveTrip(null);
      setVehicleLocation(null);
      setVehiclePolyline(null);
      
      // Notify parent component
      if (onTripEnded) {
        onTripEnded(tripId);
      }
      
      console.log(`Trip ${tripId} ended successfully`);
      window.location.href = "http://localhost:21015/driver-home";
      
    } catch (error) {
      console.error('Error ending trip:', error);
      setError('Failed to end trip. Please try again.');
    } finally {
      setEndingTrip(false);
    }
  };

  // Calculate trip duration
  const calculateTripDuration = (startTime) => {
    if (!startTime) return 'Unknown duration';
    
    const start = new Date(startTime);
    const now = new Date();
    const diffMs = now - start;
    const diffMins = Math.floor(diffMs / (1000 * 60));
    
    if (diffMins < 60) {
      return `${diffMins} minutes`;
    } else {
      const hours = Math.floor(diffMins / 60);
      const minutes = diffMins % 60;
      return `${hours}h ${minutes}m`;
    }
  };

  // Get the polyline coordinates for the trip
  const getTripPolyline = () => {
    if (vehiclePolyline && vehiclePolyline.length > 0) {
      return vehiclePolyline;
    }
    return formattedTrip?.routeCoordinates;
  };

  // Get origin coordinates for the trip
  const getTripOrigin = () => {
    if (vehiclePolyline && vehiclePolyline.length > 0) {
      return vehiclePolyline[0];
    }
    return formattedTrip?.origin;
  };

  if (loading) {
    return (
      <div className="bg-card rounded-lg shadow-sm border border-border h-full">
        <div className="py-3 px-3 sm:p-4 border-b border-border">
          <h3 className="text-base sm:text-lg font-semibold text-foreground">Active Trip</h3>
        </div>
        <div className="p-4 sm:p-6 text-center text-muted-foreground">
          <div className="animate-spin h-8 w-8 border-2 border-primary border-t-transparent rounded-full mx-auto mb-2"></div>
          <p className="text-sm">Loading active trip...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-card rounded-lg shadow-sm border border-border h-full">
        <div className="py-3 px-3 sm:p-4 border-b border-border">
          <h3 className="text-base sm:text-lg font-semibold text-foreground">Active Trip</h3>
        </div>
        <div className="p-4 sm:p-6 text-center text-red-500">
          <p className="text-sm">Error: {error}</p>
          <button 
            onClick={fetchActiveTrip}
            className="mt-2 px-3 py-1 bg-primary text-primary-foreground rounded text-sm hover:bg-primary/90"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!activeTrip) {
    return (
      <div className="bg-card rounded-lg shadow-sm border border-border h-full">
        <div className="py-3 px-3 sm:p-4 border-b border-border">
          <h3 className="text-base sm:text-lg font-semibold text-foreground">Active Trip</h3>
        </div>
        <div className="p-4 sm:p-6 text-center text-muted-foreground">
          <Navigation className="h-10 w-10 sm:h-12 sm:w-12 mx-auto mb-2 opacity-50" />
          <p className="text-sm">No active trip</p>
          <p className="text-xs mt-1">Start a trip from your upcoming trips</p>
        </div>
      </div>
    );
  }

  const formattedTrip = formatTripData(activeTrip);
  const polylineCoords = getTripPolyline();
  const originCoords = getTripOrigin();

  return (
    <div className="bg-card rounded-lg shadow-sm border border-border h-full flex flex-col">
      {/* Header */}
      <div className="py-3 px-3 sm:p-4 border-b border-border flex-shrink-0">
        <div className="flex items-center justify-between">
          <h3 className="text-base sm:text-lg font-semibold text-foreground">Active Trip</h3>
          <div className="flex items-center space-x-2">
            <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs font-medium">
              In Progress
            </span>
            {vehicleLocation && (
              <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" title="Live GPS"></div>
            )}
          </div>
        </div>
      </div>

      {/* Map Container */}
      <div className="flex-1 relative">
        <MapContainer
          center={mapCenter}
          zoom={16}
          style={{ height: '100%', width: '100%' }}
          className="rounded-b-lg"
          zoomControl={true}
        >
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          />
          <MapUpdater center={mapCenter} bounds={mapBounds} />

          {/* Route polyline */}
          {polylineCoords && polylineCoords.length > 0 && (
            <Polyline
              positions={polylineCoords}
              pathOptions={{
                color: vehiclePolyline ? '#3b82f6' : '#f59e0b',
                weight: vehiclePolyline ? 5 : 4,
                opacity: 0.8,
                dashArray: vehiclePolyline ? '10, 5' : null,
              }}
            />
          )}

          {/* Origin marker */}
          {originCoords && originCoords[0] !== 0 && originCoords[1] !== 0 && (
            <Marker
              position={originCoords}
              icon={L.divIcon({
                html: `<div style="background-color: ${
                  vehiclePolyline ? '#3b82f6' : 'white'
                }; width: 20px; height: 20px; border-radius: 50%; border: 3px solid #64748b; box-shadow: 0 3px 8px rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center;">
                         <svg width="12" height="12" viewBox="0 0 24 24" fill="${
                           vehiclePolyline ? 'white' : '#64748b'
                         }">
                           <path d="M14.4,6H20V16H13L11,13V21A1,1 0 0,1 10,22H9A1,1 0 0,1 8,21V4A1,1 0 0,1 9,3H10A1,1 0 0,1 11,4V6H14.4L14.4,6Z"/>
                         </svg>
                       </div>`,
                className: 'custom-origin-marker',
                iconSize: [20, 20],
                iconAnchor: [10, 10],
              })}
            >
              <Popup>
                <div className="text-sm">
                  <h4 className="font-semibold">
                    {vehiclePolyline ? 'Current Route Start' : 'Original Start'}
                  </h4>
                  <p className="text-muted-foreground">{formattedTrip.startLocation}</p>
                </div>
              </Popup>
            </Marker>
          )}

          {/* Destination marker */}
          {formattedTrip.position && (
            <Marker
              position={formattedTrip.position}
              icon={L.divIcon({
                html: `<div style="background-color: #22c55e; width: 24px; height: 24px; border-radius: 50%; border: 3px solid white; box-shadow: 0 4px 10px rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center;">
                         <svg width="14" height="14" viewBox="0 0 24 24" fill="white">
                           <path d="M14.4,6H20V16H13L11,13V21A1,1 0 0,1 10,22H9A1,1 0 0,1 8,21V4A1,1 0 0,1 9,3H10A1,1 0 0,1 11,4V6H14.4L14.4,6Z"/>
                         </svg>
                       </div>`,
                className: 'custom-destination-marker',
                iconSize: [24, 24],
                iconAnchor: [12, 12],
              })}
            >
              <Popup>
                <div className="text-sm">
                  <h4 className="font-semibold">Destination</h4>
                  <p className="text-muted-foreground">{formattedTrip.endLocation}</p>
                </div>
              </Popup>
            </Marker>
          )}

          {/* Live vehicle location marker */}
          {vehicleLocation && (
            <Marker
              position={vehicleLocation.position}
              icon={L.divIcon({
                html: `<div style="display: flex; align-items: center; justify-content: center; z-index: 1000; position: relative;">
                       <svg width="24" height="24" viewBox="0 0 24 24" fill="#3b82f6" style="filter: drop-shadow(0 2px 4px rgba(0,0,0,0.5));">
                         <path d="M5,11L6.5,6.5H17.5L19,11M17.5,16A1.5,1.5 0 0,1 16,14.5A1.5,1.5 0 0,1 17.5,13A1.5,1.5 0 0,1 19,14.5A1.5,1.5 0 0,1 17.5,16M6.5,16A1.5,1.5 0 0,1 5,14.5A1.5,1.5 0 0,1 6.5,13A1.5,1.5 0 0,1 8,14.5A1.5,1.5 0 0,1 6.5,16M18.92,6C18.72,5.42 18.16,5 17.5,5H6.5C5.84,5 5.28,5.42 5.08,6L3,12V20A1,1 0 0,0 4,21H5A1,1 0 0,0 6,20V19H18V20A1,1 0 0,0 19,21H20A1,1 0 0,0 21,20V12L18.92,6Z"/>
                       </svg>
                     </div>`,
                className: 'live-vehicle-marker',
                iconSize: [24, 24],
                iconAnchor: [12, 12],
              })}
              zIndexOffset={1000}
            >
              <Popup>
                <div className="text-sm">
                  <h4 className="font-semibold flex items-center gap-2">
                    <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
                    Your Vehicle
                  </h4>
                  <p className="text-muted-foreground">{formattedTrip.vehicle.model}</p>
                  {vehicleLocation.speed !== null && (
                    <p className="text-xs text-muted-foreground">
                      Speed: {Math.round(vehicleLocation.speed)} km/h
                    </p>
                  )}
                  {vehicleLocation.heading !== null && (
                    <p className="text-xs text-muted-foreground">
                      Heading: {Math.round(vehicleLocation.heading)}°
                    </p>
                  )}
                  <p className="text-xs text-muted-foreground mt-1">
                    Last updated: {vehicleLocation.lastUpdated?.toLocaleTimeString() || 'Unknown'}
                  </p>
                </div>
              </Popup>
            </Marker>
          )}
        </MapContainer>

        {/* End Trip Button - Fixed at bottom */}
        {canEndTrip && (
          <div className="absolute bottom-4 left-4 right-4 z-[1000]">
            <button
              onClick={handleEndTrip}
              disabled={endingTrip}
              className="inline-flex items-center space-x-2 px-6 py-3 bg-red-600 hover:bg-red-700 disabled:bg-red-400 text-white font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-opacity-50 w-full justify-center shadow-lg"
            >
              {endingTrip ? (
                <>
                  <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                  <span>Ending Trip...</span>
                </>
              ) : (
                <>
                  <Square className="h-4 w-4" />
                  <span>End Trip</span>
                </>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default ActiveTrip;