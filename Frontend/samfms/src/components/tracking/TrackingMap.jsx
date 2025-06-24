import React, { useState, useEffect, useCallback } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle, Polyline, useMap } from 'react-leaflet';
import L from 'leaflet';
import { Crosshair, Layers, Navigation } from 'lucide-react';

// Fix for marker icons in React-Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
});

// Component to control map center and zoom
const MapController = ({ selectedVehicle, followMode, geofences }) => {
  const map = useMap();

  useEffect(() => {
    // When a vehicle is selected and we're in follow mode, center the map on that vehicle
    if (followMode && selectedVehicle?.latitude && selectedVehicle?.longitude) {
      map.setView(
        [selectedVehicle.latitude, selectedVehicle.longitude],
        followMode ? 15 : 13
      );
    }
  }, [selectedVehicle, followMode, map]);

  // Initial setup for geofences
  useEffect(() => {
    if (geofences && geofences.length > 0) {
      // Fit map bounds to include all geofences if no vehicle is selected
      if (!selectedVehicle) {
        const bounds = L.latLngBounds(
          geofences.map(geo => [geo.coordinates.lat, geo.coordinates.lng])
        );
        map.fitBounds(bounds.pad(0.2));
      }
    }
  }, [geofences, map, selectedVehicle]);

  return null;
};

const TrackingMap = ({ vehicles, selectedVehicle, geofences = [], paths = [], onMapReady }) => {
  const [mapReady, setMapReady] = useState(false);
  const [followMode, setFollowMode] = useState(false);
  const [mapType, setMapType] = useState('streets');

  // When map is ready
  useEffect(() => {
    if (mapReady && onMapReady) {
      onMapReady(true);
    }
  }, [mapReady, onMapReady]);

  // Set map as ready after component mount
  useEffect(() => {
    setMapReady(true);
  }, []);

  // Default center of the map - San Francisco
  const defaultCenter = [-25.755, 28.233];

  // Toggle follow mode
  const toggleFollowMode = useCallback(() => {
    setFollowMode(prev => !prev);
  }, []);

  // Map tile layers based on selected type
  const getMapLayer = () => {
    switch (mapType) {
      case 'satellite':
        return {
          url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
          attribution:
            'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
        };
      case 'terrain':
        return {
          url: 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
          attribution:
            'Map data: &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, <a href="http://viewfinderpanoramas.org">SRTM</a> | Map style: &copy; <a href="https://opentopomap.org">OpenTopoMap</a>',
        };
      case 'streets':
      default:
        return {
          url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
          attribution:
            '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        };
    }
  };

  const currentMapLayer = getMapLayer();

  return (
    <div className="bg-card rounded-lg shadow-md border border-border overflow-hidden h-[550px] relative">
      {!mapReady ? (
        <div className="absolute inset-0 flex items-center justify-center bg-muted/20">
          <div className="animate-pulse text-primary">Loading map...</div>
        </div>
      ) : (
        <>
          <MapContainer center={defaultCenter} zoom={12} style={{ width: '100%', height: '100%' }}>
            <TileLayer attribution={currentMapLayer.attribution} url={currentMapLayer.url} />

            {/* Map controller for centering */}
            <MapController
              selectedVehicle={selectedVehicle}
              followMode={followMode}
              geofences={geofences}
            />

            {/* Render all geofences */}
            {geofences.map(geofence => (
              <Circle
                key={geofence.id}
                center={[geofence.coordinates.lat, geofence.coordinates.lng]}
                radius={geofence.radius}
                pathOptions={{
                  color:
                    geofence.status === 'restricted'
                      ? '#EF4444'
                      : geofence.type === 'depot'
                      ? '#8B5CF6'
                      : geofence.type === 'customer'
                      ? '#3B82F6'
                      : '#10B981',
                  fillColor:
                    geofence.status === 'restricted'
                      ? '#FCA5A5'
                      : geofence.type === 'depot'
                      ? '#C4B5FD'
                      : geofence.type === 'customer'
                      ? '#BFDBFE'
                      : '#A7F3D0',
                  fillOpacity: 0.5,
                }}
              >
                <Popup>
                  <div>
                    <h3 className="font-medium">{geofence.name}</h3>
                    <p>Type: {geofence.type.charAt(0).toUpperCase() + geofence.type.slice(1)}</p>
                    <p>Radius: {geofence.radius}m</p>
                    <p>
                      Status: {geofence.status.charAt(0).toUpperCase() + geofence.status.slice(1)}
                    </p>
                  </div>
                </Popup>
              </Circle>
            ))}

            {/* Render path lines for vehicles */}
            {paths.map((path, index) => (
              <Polyline
                key={`path-${index}`}
                positions={path.points.map(point => [point.lat, point.lng])}
                pathOptions={{
                  color: path.color || '#3B82F6',
                  weight: 3,
                  opacity: 0.7,
                  dashArray: path.type === 'planned' ? '10, 10' : null,
                }}
              >
                <Popup>
                  <div>
                    <p className="font-medium">{path.title || `Route ${index + 1}`}</p>
                    {path.description && <p>{path.description}</p>}
                    {path.distance && <p>Distance: {path.distance} km</p>}
                  </div>
                </Popup>
              </Polyline>
            ))}

            {/* Vehicle markers */}
            {vehicles.map(vehicle => {
              if (!vehicle?.latitude || !vehicle?.longitude) return null;

              let markerColor;
              if (vehicle.status === 'online') markerColor = '#22c55e';
              else if (vehicle.status === 'offline') markerColor = '#3b82f6';
              else markerColor = '#ef4444';

              // Create a custom icon with the vehicle's heading
              const customIcon = new L.DivIcon({
                className: 'custom-div-icon',
                html: `
                  <div style="
                    position: relative;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                  ">
                    <div style="
                      background-color: ${markerColor}; 
                      width: ${selectedVehicle?.id === vehicle.id ? '24px' : '20px'}; 
                      height: ${selectedVehicle?.id === vehicle.id ? '24px' : '20px'}; 
                      border-radius: 50%; 
                      border: 2px solid white; 
                      box-shadow: 0 0 10px rgba(0,0,0,0.3);
                      display: flex;
                      align-items: center;
                      justify-content: center;
                      z-index: 1;
                    ">
                      ${
                        vehicle.status === 'online'
                          ? `<div style="
                          width: 0; 
                          height: 0; 
                          border-left: 6px solid transparent;
                          border-right: 6px solid transparent;
                          border-bottom: 10px solid white;
                          transform: rotate(${
                            vehicle.direction === 'North'
                              ? '0'
                              : vehicle.direction === 'East'
                              ? '90'
                              : vehicle.direction === 'South'
                              ? '180'
                              : vehicle.direction === 'West'
                              ? '270'
                              : vehicle.direction === 'North-East'
                              ? '45'
                              : vehicle.direction === 'South-East'
                              ? '135'
                              : vehicle.direction === 'South-West'
                              ? '225'
                              : vehicle.direction === 'North-West'
                              ? '315'
                              : '0'
                          }deg);
                        "></div>`
                          : ''
                      }
                    </div>
                    ${
                      selectedVehicle?.id === vehicle.id
                        ? `<div style="
                        position: absolute;
                        width: 34px;
                        height: 34px;
                        border-radius: 50%;
                        border: 2px solid ${markerColor};
                        animation: pulse 1.5s infinite;
                      "></div>`
                        : ''
                    }
                  </div>
                  <style>
                    @keyframes pulse {
                      0% { transform: scale(1); opacity: 1; }
                      100% { transform: scale(1.5); opacity: 0; }
                    }
                  </style>
                `,
                iconSize: [
                  selectedVehicle?.id === vehicle.id ? 35 : 30,
                  selectedVehicle?.id === vehicle.id ? 35 : 30,
                ],
                iconAnchor: [
                  selectedVehicle?.id === vehicle.id ? 17.5 : 15,
                  selectedVehicle?.id === vehicle.id ? 17.5 : 15,
                ],
                popupAnchor: [0, -15],
              });

              return (
                <Marker
                  key={vehicle.id}
                  position={[vehicle.latitude, vehicle.longitude]}
                  icon={customIcon}
                >
                  <Popup>
                    <div className="p-1">
                      <h3 className="font-medium">{vehicle.id}</h3>
                      <p>
                        {vehicle.model}
                      </p>
                      <p>Driver: {vehicle.driver || 'Unassigned'}</p>
                      <p>Status: {vehicle.status}</p>
                      {vehicle.speed && <p>Speed: {vehicle.speed}</p>}
                      {/* {vehicle.direction && vehicle.direction !== 'Stopped' && (
                        <p>Direction: {vehicle.direction}</p>
                      )} */}
                      {/* {vehicle.fuelLevel && <p>Fuel: {vehicle.fuelLevel}</p>} */}
                      <p>Last update: {vehicle.lastUpdate}</p>
                    </div>
                  </Popup>
                </Marker>
              );
            })}
          </MapContainer>

          {/* Map controls overlay */}
          <div className="absolute top-4 right-4 flex flex-col gap-2 z-[1000]">
            <div className="bg-card p-2 rounded-md shadow-md border border-border">
              <button
                className={`p-2 rounded-md w-8 h-8 flex items-center justify-center ${
                  followMode ? 'bg-primary text-primary-foreground' : 'hover:bg-accent/50'
                }`}
                onClick={toggleFollowMode}
                title={followMode ? 'Disable follow mode' : 'Enable follow mode'}
              >
                <Crosshair size={16} />
              </button>
            </div>
            <div className="bg-card p-2 rounded-md shadow-md border border-border">
              <button
                className={`p-2 rounded-md w-8 h-8 flex items-center justify-center ${
                  mapType === 'streets'
                    ? 'bg-primary text-primary-foreground'
                    : 'hover:bg-accent/50'
                }`}
                onClick={() => setMapType('streets')}
                title="Street map"
              >
                <Navigation size={16} />
              </button>
              <button
                className={`p-2 rounded-md w-8 h-8 flex items-center justify-center mt-1 ${
                  mapType === 'satellite'
                    ? 'bg-primary text-primary-foreground'
                    : 'hover:bg-accent/50'
                }`}
                onClick={() => setMapType('satellite')}
                title="Satellite map"
              >
                <Layers size={16} />
              </button>
              <button
                className={`p-2 rounded-md w-8 h-8 flex items-center justify-center mt-1 ${
                  mapType === 'terrain'
                    ? 'bg-primary text-primary-foreground'
                    : 'hover:bg-accent/50'
                }`}
                onClick={() => setMapType('terrain')}
                title="Terrain map"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="m2 22 10-10 10 10M12 12V3" />
                  <path d="m9 6 3-3 3 3" />
                </svg>
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default TrackingMap;
