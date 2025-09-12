import React, {useState} from 'react';
import {MapContainer, TileLayer, Marker, Popup, useMapEvents} from 'react-leaflet';
import L from 'leaflet';
import RoutingMachine from './RoutingMachine';

// Fix for marker icons in React-Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
});

// Custom icons for different marker types - fixed to avoid DOM position issues
const createCustomIcon = (color, label) => {
  return L.divIcon({
    className: 'custom-trip-marker',
    html: `<div class="trip-marker-circle" style="background-color: ${color}; width: 30px; height: 30px; border-radius: 50%; border: 4px solid white; box-shadow: 0 0 15px rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 14px; line-height: 1;">${label || ''}</div>`,
    iconSize: [38, 38],
    iconAnchor: [19, 19],
    popupAnchor: [0, -19],
  });
};

const startIcon = createCustomIcon('#22c55e', 'S'); // Green with S
const endIcon = createCustomIcon('#ef4444', 'E'); // Red with E

// Component to handle map clicks
const MapEventHandler = ({onLocationSelect, mode}) => {
  useMapEvents({
    click: e => {
      // Prevent any default behaviors that might cause expansion
      if (e.originalEvent) {
        e.originalEvent.preventDefault();
        e.originalEvent.stopPropagation();
      }

      if (mode === 'select') {
        onLocationSelect({
          lat: e.latlng.lat,
          lng: e.latlng.lng,
        });
      }
    },
  });

  return null;
};

const TripPlanningMap = ({
  startLocation,
  endLocation,
  waypoints = [],
  onStartLocationChange,
  onEndLocationChange,
  onWaypointAdd,
  onWaypointRemove,
  onRouteCalculated,
  routeCalculating: externalRouteCalculating,
  setRouteCalculating: externalSetRouteCalculating,
  className = '',
}) => {
  const [mode] = useState('select'); // 'select' or 'view'
  const [selectionType, setSelectionType] = useState('start'); // 'start', 'end', or 'waypoint'
  const [internalRouteCalculating, setInternalRouteCalculating] = useState(false);

  // Use external state if provided, otherwise use internal state
  const routeCalculating =
    externalRouteCalculating !== undefined ? externalRouteCalculating : internalRouteCalculating;
  const setRouteCalculating = externalSetRouteCalculating || setInternalRouteCalculating;

  // Default center (Cape Town, South Africa)
  const defaultCenter = [-33.9249, 18.4241];

  // Determine map center based on available locations
  const getMapCenter = () => {
    if (startLocation) {
      return [startLocation.lat, startLocation.lng];
    }
    if (endLocation) {
      return [endLocation.lat, endLocation.lng];
    }
    return defaultCenter;
  };

  const handleLocationSelect = location => {
    if (selectionType === 'start') {
      onStartLocationChange(location);
    } else if (selectionType === 'end') {
      onEndLocationChange(location);
    } else if (selectionType === 'waypoint') {
      onWaypointAdd(location);
    }
  };

  const removeWaypoint = index => {
    onWaypointRemove(index);
  };

  return (
    <div className={`bg-card rounded-lg border border-border overflow-hidden ${className}`}>
      {/* Selection Controls Section */}
      <div className="p-4 bg-muted/20 border-b border-border">
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center gap-2 text-sm">
            <span className="font-medium">Select:</span>
            <button
              type="button"
              onClick={() => setSelectionType('start')}
              className={`px-3 py-1 rounded text-xs font-medium transition-colors ${selectionType === 'start'
                ? 'bg-green-100 text-green-800 border border-green-300'
                : 'bg-background border border-input hover:bg-accent'
                }`}
            >
              Start Point
            </button>
            <button
              type="button"
              onClick={() => setSelectionType('end')}
              className={`px-3 py-1 rounded text-xs font-medium transition-colors ${selectionType === 'end'
                ? 'bg-red-100 text-red-800 border border-red-300'
                : 'bg-background border border-input hover:bg-accent'
                }`}
            >
              End Point
            </button>
            <button
              type="button"
              onClick={() => setSelectionType('waypoint')}
              className={`px-3 py-1 rounded text-xs font-medium transition-colors ${selectionType === 'waypoint'
                ? 'bg-blue-100 text-blue-800 border border-blue-300'
                : 'bg-background border border-input hover:bg-accent'
                }`}
            >
              Add Waypoint
            </button>
          </div>
        </div>
      </div>

      {/* Location Status Section */}
      <div className="px-4 py-2 bg-muted/10 border-b border-border">
        <div className="flex flex-wrap items-center gap-4 text-xs">
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <span>Start: {startLocation ? '✓ Selected' : 'Click on map'}</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 bg-red-500 rounded-full"></div>
            <span>End: {endLocation ? '✓ Selected' : 'Click on map'}</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
            <span>Waypoints: {waypoints.length}</span>
          </div>
          {startLocation && endLocation && (
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
              <span className="text-purple-700 font-medium">Route will be calculated</span>
            </div>
          )}
        </div>
      </div>

      {/* Waypoints List Section */}
      {waypoints.length > 0 && (
        <div className="px-4 py-2 bg-muted/5 border-b border-border">
          <div className="text-xs text-muted-foreground mb-1">Waypoints:</div>
          <div className="flex flex-wrap gap-2">
            {waypoints.map((waypoint, index) => (
              <div
                key={index}
                className="flex items-center gap-1 px-2 py-1 bg-blue-50 border border-blue-200 rounded text-xs"
              >
                <span>#{index + 1}</span>
                <button
                  type="button"
                  onClick={() => removeWaypoint(index)}
                  className="text-red-500 hover:text-red-700 ml-1"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Map Container - Isolated to prevent expansion */}
      <div className="relative" style={{height: '384px', minHeight: '384px', maxHeight: '384px'}}>
        <div
          className="h-96 relative overflow-hidden bg-gray-100"
          style={{
            height: '384px',
            minHeight: '384px',
            maxHeight: '384px',
            width: '100%',
            minWidth: '100%',
            maxWidth: '100%',
            position: 'relative',
            contain: 'layout size'
          }}
        >
          {routeCalculating && (
            <div className="absolute top-2 right-2 z-[1000] bg-blue-500 text-white px-3 py-1 rounded-md text-sm font-medium shadow-lg">
              <div className="flex items-center gap-2">
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                Calculating route...
              </div>
            </div>
          )}
          <MapContainer
            center={getMapCenter()}
            zoom={12}
            className="w-full h-full trip-planning-map-container"
            style={{
              width: '100%',
              height: '100%',
              position: 'relative',
              zIndex: 1,
              maxWidth: '100%',
              maxHeight: '100%'
            }}
            zoomControl={true}
            scrollWheelZoom={true}
            doubleClickZoom={false}
            dragging={true}
            boxZoom={false}
            keyboard={false}
            touchZoom={true}
            attributionControl={false}
            key="trip-planning-map-static"
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />

            {/* Map event handler for clicking */}
            <MapEventHandler onLocationSelect={handleLocationSelect} mode={mode} />

            {/* Routing machine for route calculation and display */}
            <RoutingMachine
              startLocation={startLocation}
              endLocation={endLocation}
              waypoints={waypoints}
              onRouteCalculated={onRouteCalculated}
              isCalculating={routeCalculating}
              setIsCalculating={setRouteCalculating}
            />

            {/* Start location marker */}
            {startLocation && (
              <Marker
                key={`start-${startLocation.lat}-${startLocation.lng}`}
                position={[startLocation.lat, startLocation.lng]}
                icon={startIcon}
              >
                <Popup>
                  <div className="text-sm">
                    <div className="font-medium text-green-700">Start Location</div>
                    <div className="text-xs text-gray-600">
                      {startLocation.lat.toFixed(6)}, {startLocation.lng.toFixed(6)}
                    </div>
                  </div>
                </Popup>
              </Marker>
            )}

            {/* End location marker */}
            {endLocation && (
              <Marker
                key={`end-${endLocation.lat}-${endLocation.lng}`}
                position={[endLocation.lat, endLocation.lng]}
                icon={endIcon}
              >
                <Popup>
                  <div className="text-sm">
                    <div className="font-medium text-red-700">End Location</div>
                    <div className="text-xs text-gray-600">
                      {endLocation.lat.toFixed(6)}, {endLocation.lng.toFixed(6)}
                    </div>
                  </div>
                </Popup>
              </Marker>
            )}

            {/* Waypoint markers */}
            {waypoints.map((waypoint, index) => (
              <Marker
                key={`waypoint-${index}-${waypoint.lat}-${waypoint.lng}`}
                position={[waypoint.lat, waypoint.lng]}
                icon={createCustomIcon('#3b82f6', (index + 1).toString())}
              >
                <Popup>
                  <div className="text-sm">
                    <div className="font-medium text-blue-700">Waypoint #{index + 1}</div>
                    <div className="text-xs text-gray-600">
                      {waypoint.lat.toFixed(6)}, {waypoint.lng.toFixed(6)}
                    </div>
                    <button
                      type="button"
                      onClick={() => removeWaypoint(index)}
                      className="mt-1 px-2 py-1 bg-red-100 text-red-700 text-xs rounded hover:bg-red-200"
                    >
                      Remove
                    </button>
                  </div>
                </Popup>
              </Marker>
            ))}
          </MapContainer>
        </div>
      </div>
    </div>
  );
};

export default TripPlanningMap;