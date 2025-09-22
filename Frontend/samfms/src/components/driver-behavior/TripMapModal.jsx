import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet';
import L from 'leaflet';
import { X, MapPin, Smartphone, Gauge, ChevronsUp, ChevronsDown, User, Calendar } from 'lucide-react';
import 'leaflet/dist/leaflet.css';

console.log('TripMapModal component loaded, Leaflet version:', L.version);

// Fix for default markers in React Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

// Custom violation icons using Lucide icons
const createViolationIcon = (type, color) => {
  const iconMap = {
    speeding: `<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>`,
    braking: `<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m7 11 2-2-2-2"/><path d="M11 13h4"/></svg>`,
    acceleration: `<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m17 11-2-2 2-2"/><path d="M9 11h4"/></svg>`,
    phone_usage: `<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect width="14" height="20" x="5" y="2" rx="2" ry="2"/><path d="M12 18h.01"/></svg>`
  };
  
  return L.divIcon({
    html: `<div style="background-color: ${color}; border: 2px solid white; border-radius: 50%; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; box-shadow: 0 3px 6px rgba(0,0,0,0.4);">
             ${iconMap[type] || iconMap.speeding}
           </div>`,
    className: 'custom-violation-marker',
    iconSize: [24, 24],
    iconAnchor: [12, 12],
  });
};

const TripMapModal = ({ isOpen, onClose, trip, violations = {} }) => {
  const [mapCenter, setMapCenter] = useState([-26.2041, 28.0473]); // Default to Johannesburg
  const [routeCoordinates, setRouteCoordinates] = useState([]);
  const [mapBounds, setMapBounds] = useState(null);

  // Component to auto-fit map bounds
  const FitBounds = ({ bounds }) => {
    const map = useMap();
    
    useEffect(() => {
      if (bounds && bounds.isValid()) {
        setTimeout(() => {
          map.fitBounds(bounds, { padding: [30, 30], maxZoom: 15 });
        }, 100);
      }
    }, [bounds, map]);
    
    return null;
  };

  useEffect(() => {
    if (trip && isOpen) {
      console.log('Trip data in map modal:', trip);
      
      let allCoordinates = [];
      
      // Set map center based on trip origin
      let originLat = null, originLng = null;
      
      if (trip.origin?.location?.coordinates) {
        // API format: origin.location.coordinates = [longitude, latitude]
        originLng = trip.origin.location.coordinates[0];
        originLat = trip.origin.location.coordinates[1];
        setMapCenter([originLat, originLng]);
        allCoordinates.push([originLat, originLng]);
      } else if (trip.origin?.lat && trip.origin?.lng) {
        // Legacy format
        setMapCenter([trip.origin.lat, trip.origin.lng]);
        allCoordinates.push([trip.origin.lat, trip.origin.lng]);
      }

      // Add destination to coordinates
      if (trip.destination?.location?.coordinates) {
        const destLng = trip.destination.location.coordinates[0];
        const destLat = trip.destination.location.coordinates[1];
        allCoordinates.push([destLat, destLng]);
      } else if (trip.destination?.lat && trip.destination?.lng) {
        allCoordinates.push([trip.destination.lat, trip.destination.lng]);
      }

      // Extract route coordinates from raw_route_response
      if (trip.raw_route_response) {
        try {
          const routeData = typeof trip.raw_route_response === 'string' 
            ? JSON.parse(trip.raw_route_response) 
            : trip.raw_route_response;

          console.log('Route data structure:', routeData);

          // Try different possible route data structures
          let coordinates = [];
          
          // Check for results[0].geometry[0] structure (from API response)
          if (routeData.results && 
              routeData.results[0] && 
              routeData.results[0].geometry && 
              Array.isArray(routeData.results[0].geometry[0])) {
            
            const geometryArray = routeData.results[0].geometry[0];
            coordinates = geometryArray.map(coord => [coord.lat, coord.lon]);
            console.log('Extracted coordinates from results.geometry:', coordinates.length, 'points');
          }
          // Check for GeoJSON features structure
          else if (routeData.features && routeData.features[0] && routeData.features[0].geometry) {
            const geoCoords = routeData.features[0].geometry.coordinates;
            coordinates = geoCoords.map(coord => [coord[1], coord[0]]); // Convert [lng, lat] to [lat, lng]
            console.log('Extracted coordinates from GeoJSON features:', coordinates.length, 'points');
          }
          
          if (coordinates.length > 0) {
            setRouteCoordinates(coordinates);
            allCoordinates = [...allCoordinates, ...coordinates];
          } else {
            console.warn('No valid route coordinates found in route data');
          }
        } catch (error) {
          console.error('Error parsing route data:', error);
        }
      }

      // Set map bounds for auto-fit
      if (allCoordinates.length > 1) {
        const bounds = L.latLngBounds(allCoordinates);
        setMapBounds(bounds);
      }
    }
  }, [trip, isOpen]);

  const renderViolationMarkers = () => {
    const markers = [];
    
    console.log('Rendering violation markers with data:', violations);
    
    Object.entries(violations).forEach(([type, violationList]) => {
      if (Array.isArray(violationList)) {
        violationList.forEach((violation, index) => {
          console.log(`Processing ${type} violation:`, violation);
          
          let violationLat = null, violationLng = null;
          
          // Handle different possible location formats
          // Check both 'location' and 'start_location' fields
          const locationData = violation.location || violation.start_location;
          
          if (locationData) {
            if (locationData.coordinates && Array.isArray(locationData.coordinates)) {
              // GeoJSON format: coordinates = [longitude, latitude]
              violationLng = locationData.coordinates[0];
              violationLat = locationData.coordinates[1];
            } else if (locationData.lat && locationData.lng) {
              // Direct lat/lng format
              violationLat = locationData.lat;
              violationLng = locationData.lng;
            } else if (locationData.lat && locationData.lon) {
              // lon format instead of lng
              violationLat = locationData.lat;
              violationLng = locationData.lon;
            }
          }
          
          if (violationLat && violationLng) {
            const color = type === 'speeding' ? '#ef4444' : 
                         type === 'braking' ? '#f97316' : 
                         type === 'acceleration' ? '#eab308' : '#8b5cf6';
            
            console.log(`Adding ${type} marker at [${violationLat}, ${violationLng}]`);
            
            markers.push(
              <Marker
                key={`${type}-${index}`}
                position={[violationLat, violationLng]}
                icon={createViolationIcon(type, color)}
              >
                <Popup>
                  <div className="p-3 min-w-48">
                    <div className="font-semibold text-gray-800 mb-3 capitalize flex items-center">
                      {type === 'speeding' && <Gauge className="w-4 h-4 mr-2 text-red-500" />}
                      {type === 'braking' && <ChevronsDown className="w-4 h-4 mr-2 text-orange-500" />}
                      {type === 'acceleration' && <ChevronsUp className="w-4 h-4 mr-2 text-yellow-500" />}
                      {type === 'phone_usage' && <Smartphone className="w-4 h-4 mr-2 text-purple-500" />}
                      {type.replace('_', ' ')} Violation
                    </div>
                    <div className="text-sm text-gray-600 space-y-2">
                      {type === 'speeding' && (
                        <>
                          <div className="flex justify-between">
                            <span className="font-medium">Speed:</span>
                            <span>{violation.speed} km/h</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="font-medium">Limit:</span>
                            <span>{violation.speed_limit} km/h</span>
                          </div>
                        </>
                      )}
                      {type === 'braking' && (
                        <>
                          <div className="flex justify-between">
                            <span className="font-medium">Deceleration:</span>
                            <span>{violation.deceleration} m/s²</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="font-medium">Threshold:</span>
                            <span>{violation.threshold} m/s²</span>
                          </div>
                        </>
                      )}
                      {type === 'acceleration' && (
                        <>
                          <div className="flex justify-between">
                            <span className="font-medium">Acceleration:</span>
                            <span>{violation.acceleration} m/s²</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="font-medium">Threshold:</span>
                            <span>{violation.threshold} m/s²</span>
                          </div>
                        </>
                      )}
                      {type === 'phone_usage' && (
                        <>
                          <div className="flex justify-between">
                            <span className="font-medium">Type:</span>
                            <span>{violation.violation_type}</span>
                          </div>
                          {violation.duration_seconds && (
                            <div className="flex justify-between">
                              <span className="font-medium">Duration:</span>
                              <span>{violation.duration_seconds}s</span>
                            </div>
                          )}
                        </>
                      )}
                      <div className="pt-1 border-t border-gray-200">
                        <div className="flex justify-between">
                          <span className="font-medium">Time:</span>
                          <span>{new Date(violation.time || violation.start_time).toLocaleString()}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </Popup>
              </Marker>
            );
          } else {
            console.warn(`No valid location found for ${type} violation:`, violation);
          }
        });
      }
    });
    
    console.log(`Total violation markers created: ${markers.length}`);
    return markers;
  };

  const renderOriginDestinationMarkers = () => {
    const markers = [];
    
    // Handle origin marker
    let originLat = null, originLng = null, originAddress = null;
    
    if (trip.origin?.location?.coordinates) {
      // API format: origin.location.coordinates = [longitude, latitude]
      originLng = trip.origin.location.coordinates[0];
      originLat = trip.origin.location.coordinates[1];
      originAddress = trip.origin.address;
    } else if (trip.origin?.lat && trip.origin?.lng) {
      // Legacy format
      originLat = trip.origin.lat;
      originLng = trip.origin.lng;
      originAddress = trip.origin.address;
    }
    
    if (originLat && originLng) {
      markers.push(
        <Marker
          key="origin"
          position={[originLat, originLng]}
          icon={L.divIcon({
            html: `<div style="background-color: #22c55e; border: 3px solid white; border-radius: 50%; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; box-shadow: 0 3px 6px rgba(0,0,0,0.4);">
                     <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg>
                   </div>`,
            className: 'custom-origin-marker',
            iconSize: [28, 28],
            iconAnchor: [14, 14],
          })}
        >
          <Popup>
            <div className="p-3 min-w-48">
              <div className="font-semibold text-green-600 mb-2 flex items-center">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" className="mr-2"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg>
                Trip Origin
              </div>
              <div className="text-sm text-gray-600">
                {originAddress || `${originLat.toFixed(6)}, ${originLng.toFixed(6)}`}
              </div>
            </div>
          </Popup>
        </Marker>
      );
    }
    
    // Handle destination marker
    let destLat = null, destLng = null, destAddress = null;
    
    if (trip.destination?.location?.coordinates) {
      // API format: destination.location.coordinates = [longitude, latitude]
      destLng = trip.destination.location.coordinates[0];
      destLat = trip.destination.location.coordinates[1];
      destAddress = trip.destination.address;
    } else if (trip.destination?.lat && trip.destination?.lng) {
      // Legacy format
      destLat = trip.destination.lat;
      destLng = trip.destination.lng;
      destAddress = trip.destination.address;
    }
    
    if (destLat && destLng) {
      markers.push(
        <Marker
          key="destination"
          position={[destLat, destLng]}
          icon={L.divIcon({
            html: `<div style="background-color: #dc2626; border: 3px solid white; border-radius: 50%; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; box-shadow: 0 3px 6px rgba(0,0,0,0.4);">
                     <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg>
                   </div>`,
            className: 'custom-destination-marker',
            iconSize: [28, 28],
            iconAnchor: [14, 14],
          })}
        >
          <Popup>
            <div className="p-3 min-w-48">
              <div className="font-semibold text-red-600 mb-2 flex items-center">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" className="mr-2"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg>
                Trip Destination
              </div>
              <div className="text-sm text-gray-600">
                {destAddress || `${destLat.toFixed(6)}, ${destLng.toFixed(6)}`}
              </div>
            </div>
          </Popup>
        </Marker>
      );
    }
    
    return markers;
  };

  const totalViolations = Object.values(violations).reduce((sum, violationList) => 
    sum + (Array.isArray(violationList) ? violationList.length : 0), 0
  );

  const formatDateTime = (dateString) => {
    if (!dateString) return 'Not available';
    try {
      return new Date(dateString).toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch (error) {
      return dateString;
    }
  };

  if (!isOpen) return null;

  console.log('TripMapModal rendering - isOpen:', isOpen, 'trip:', trip, 'violations:', violations);

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      <div className="flex items-center justify-center min-h-screen">
        {/* Background overlay */}
        <div 
          className="fixed inset-0 transition-opacity bg-black/60 backdrop-blur-sm"
          onClick={onClose}
        />

        {/* Full screen modal panel */}
        <div className="relative w-full h-full bg-white dark:bg-gray-900 flex flex-col">
          {/* Header */}
          <div className="bg-gradient-to-r from-slate-600 to-slate-700 px-6 py-4 text-white flex-shrink-0">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <MapPin className="w-7 h-7 mr-3 text-slate-200" />
                <div>
                  <h3 className="text-2xl font-bold mb-1">
                    {trip.trip_name || trip.name || 'Trip Route Map'}
                  </h3>
                  <div className="flex items-center space-x-6 text-slate-200 text-sm">
                    <div className="flex items-center">
                      <User className="w-4 h-4 mr-2" />
                      <span>{trip.driver_name || 'Unknown Driver'}</span>
                    </div>
                    <div className="flex items-center">
                      <Calendar className="w-4 h-4 mr-2" />
                      <span>{formatDateTime(trip.actual_start_time)}</span>
                    </div>
                    {totalViolations > 0 && (
                      <div className="flex items-center bg-red-500/20 px-3 py-1 rounded-full">
                        <span className="w-2 h-2 bg-red-400 rounded-full mr-2"></span>
                        <span className="font-medium">{totalViolations} violations</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
              <button
                onClick={onClose}
                className="text-white hover:bg-white/20 rounded-lg p-2 transition-colors duration-200"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
          </div>

          {/* Map Content - Full height */}
          <div className="flex-1 relative bg-gray-200">
            <MapContainer
              center={mapCenter}
              zoom={13}
              style={{ height: '100%', width: '100%', minHeight: '400px' }}
              className="z-10"
              whenCreated={(map) => {
                console.log('Map created:', map);
                setTimeout(() => {
                  map.invalidateSize();
                }, 100);
              }}
            >
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              
              {/* Auto-fit bounds */}
              {mapBounds && <FitBounds bounds={mapBounds} />}
              
              {/* Route polyline */}
              {routeCoordinates.length > 0 && (
                <Polyline
                  positions={routeCoordinates}
                  color="#3b82f6"
                  weight={4}
                  opacity={0.8}
                />
              )}
              
              {/* Origin and destination markers */}
              {renderOriginDestinationMarkers()}
              
              {/* Violation markers */}
              {renderViolationMarkers()}
            </MapContainer>
          </div>

          {/* Legend - Fixed bottom */}
          <div className="px-6 py-4 bg-slate-50 dark:bg-slate-800 border-t border-slate-200 dark:border-slate-700 flex-shrink-0">
            <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-3">Map Legend</h4>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 text-sm">
              <div className="flex items-center">
                <div className="w-5 h-5 bg-green-500 rounded-full mr-3 flex items-center justify-center">
                  <MapPin className="w-3 h-3 text-white" />
                </div>
                <span className="text-slate-600 dark:text-slate-300 font-medium">Origin</span>
              </div>
              <div className="flex items-center">
                <div className="w-5 h-5 bg-red-600 rounded-full mr-3 flex items-center justify-center">
                  <MapPin className="w-3 h-3 text-white" />
                </div>
                <span className="text-slate-600 dark:text-slate-300 font-medium">Destination</span>
              </div>
              <div className="flex items-center">
                <div className="w-5 h-5 bg-red-500 rounded-full mr-3 flex items-center justify-center">
                  <Gauge className="w-3 h-3 text-white" />
                </div>
                <span className="text-slate-600 dark:text-slate-300">Speeding ({violations.speeding?.length || 0})</span>
              </div>
              <div className="flex items-center">
                <div className="w-5 h-5 bg-orange-500 rounded-full mr-3 flex items-center justify-center">
                  <ChevronsDown className="w-3 h-3 text-white" />
                </div>
                <span className="text-slate-600 dark:text-slate-300">Hard Braking ({violations.braking?.length || 0})</span>
              </div>
              <div className="flex items-center">
                <div className="w-5 h-5 bg-yellow-500 rounded-full mr-3 flex items-center justify-center">
                  <ChevronsUp className="w-3 h-3 text-white" />
                </div>
                <span className="text-slate-600 dark:text-slate-300">Hard Acceleration ({violations.acceleration?.length || 0})</span>
              </div>
              <div className="flex items-center">
                <div className="w-5 h-5 bg-purple-500 rounded-full mr-3 flex items-center justify-center">
                  <Smartphone className="w-3 h-3 text-white" />
                </div>
                <span className="text-slate-600 dark:text-slate-300">Phone Usage ({violations.phone_usage?.length || 0})</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TripMapModal;