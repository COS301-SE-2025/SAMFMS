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

// Map controller for centering
const MapController = ({ followMode, focusLocation }) => {
  const map = useMap();
  useEffect(() => {
    if (followMode && focusLocation) {
      map.setView([focusLocation.latitude, focusLocation.longitude], 15);
    }
  }, [followMode, focusLocation, map]);
  return null;
};

const TrackingMap = ({
  locations = [], // Now the ONLY live data
  geofences = [],
  paths = [],
  onMapReady,
}) => {
  const [mapReady, setMapReady] = useState(false);
  const [followMode, setFollowMode] = useState(false);
  const [mapType, setMapType] = useState('streets');
  const [focusLocation, setFocusLocation] = useState(null);

  useEffect(() => {
    if (mapReady && onMapReady) onMapReady(true);
  }, [mapReady, onMapReady]);

  useEffect(() => {
    setMapReady(true);
    if (locations.length > 0) setFocusLocation(locations[0]); // Default focus on first location
  }, [locations]);

  const defaultCenter = [-25.755, 28.233];

  const toggleFollowMode = useCallback(() => {
    setFollowMode(prev => !prev);
  }, []);

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
    <div className="bg-card rounded-lg shadow-md border border-border overflow-hidden h-[500px] relative">
      {!mapReady ? (
        <div className="absolute inset-0 flex items-center justify-center bg-muted/20">
          <div className="animate-pulse text-primary">Loading map...</div>
        </div>
      ) : (
        <>
          <MapContainer center={defaultCenter} zoom={12} style={{ width: '100%', height: '100%' }}>
            <TileLayer attribution={currentMapLayer.attribution} url={currentMapLayer.url} />
            <MapController followMode={followMode} focusLocation={focusLocation} />

            {/* Geofences */}
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
                    <p>Type: {geofence.type}</p>
                    <p>Radius: {geofence.radius}m</p>
                    <p>Status: {geofence.status}</p>
                  </div>
                </Popup>
              </Circle>
            ))}

            {/* Live vehicle locations */}
            {locations.map(loc => (
              <Marker
                key={loc.id}
                position={[loc.latitude, loc.longitude]}
                icon={L.divIcon({
                  className: 'custom-location-icon',
                  html: `<div style="background:#ff9800;width:14px;height:14px;border-radius:50%;border:2px solid white"></div>`,
                  iconSize: [20, 20],
                  iconAnchor: [10, 10],
                })}
                eventHandlers={{
                  click: () => setFocusLocation(loc),
                }}
              >
                <Popup>
                  <div>
                    <p>
                      <strong>Vehicle:</strong> {loc.vehicle_id}
                    </p>
                    <p>
                      <strong>Speed:</strong> {loc.speed} km/h
                    </p>
                    <p>
                      <strong>Heading:</strong> {loc.heading}
                    </p>
                    <p>
                      <strong>Updated:</strong> {new Date(loc.updated_at).toLocaleString()}
                    </p>
                  </div>
                </Popup>
              </Marker>
            ))}

            {/* Optional route paths */}
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
              />
            ))}
          </MapContainer>

          {/* Map controls */}
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
