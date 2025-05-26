import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle, useMap } from 'react-leaflet';
import L from 'leaflet';

// Fix for marker icons in React-Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
});

// Component to recenter the map when selected vehicle changes
const MapController = ({ selectedVehicle }) => {
  const map = useMap();

  useEffect(() => {
    if (selectedVehicle?.location) {
      map.setView([selectedVehicle.location.latitude, selectedVehicle.location.longitude], 13);
    }
  }, [selectedVehicle, map]);

  return null;
};

// Helper functions for map markers are implemented inline

const MapDisplay = ({ vehicles, selectedVehicle }) => {
  const [mapReady, setMapReady] = useState(false);

  useEffect(() => {
    // Set map as ready after component mount
    setMapReady(true);
  }, []);

  // Default center of the map - San Francisco
  const defaultCenter = [37.7749, -122.4194];
  return (
    <div className="bg-card rounded-lg shadow-md border border-border overflow-hidden h-[500px] relative">
      {!mapReady ? (
        <div className="absolute inset-0 flex items-center justify-center bg-muted/20">
          <div className="animate-pulse text-primary">Loading map...</div>
        </div>
      ) : (
        <MapContainer center={defaultCenter} zoom={12} style={{ width: '100%', height: '100%' }}>
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {/* Add controller to handle map recenter */}
          <MapController selectedVehicle={selectedVehicle} />

          {/* Landmarks as circles */}
          <Circle
            center={[37.7749, -122.4194]}
            radius={500}
            pathOptions={{ color: '#8B5CF6', fillColor: '#C4B5FD', fillOpacity: 0.5 }}
          >
            <Popup>HQ</Popup>
          </Circle>

          <Circle
            center={[37.7833, -122.4167]}
            radius={1200}
            pathOptions={{ color: '#EF4444', fillColor: '#FCA5A5', fillOpacity: 0.5 }}
          >
            <Popup>No-Go Zone</Popup>
          </Circle>

          <Circle
            center={[37.7694, -122.4862]}
            radius={200}
            pathOptions={{ color: '#3B82F6', fillColor: '#BFDBFE', fillOpacity: 0.5 }}
          >
            <Popup>Client Site</Popup>
          </Circle>

          {/* Vehicle markers */}
          {vehicles.map(vehicle => {
            if (!vehicle.location?.latitude || !vehicle.location?.longitude) return null;

            let markerColor;
            if (vehicle.status === 'active') markerColor = '#22c55e';
            else if (vehicle.status === 'idle') markerColor = '#3b82f6';
            else markerColor = '#ef4444';

            const customIcon = new L.DivIcon({
              className: 'custom-div-icon',
              html: `<div style="background-color: ${markerColor}; width: 20px; height: 20px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 10px rgba(0,0,0,0.3);"></div>`,
              iconSize: [20, 20],
              iconAnchor: [10, 10],
              popupAnchor: [0, -10],
            });

            return (
              <Marker
                key={vehicle.id}
                position={[vehicle.location.latitude, vehicle.location.longitude]}
                icon={customIcon}
              >
                <Popup>
                  <div>
                    <h3 className="font-medium">{vehicle.id}</h3>
                    <p>
                      {vehicle.make} {vehicle.model}
                    </p>
                    <p>Driver: {vehicle.driver || 'Unassigned'}</p>
                    <p>Status: {vehicle.status}</p>
                    {vehicle.speed && <p>Speed: {vehicle.speed}</p>}
                    <p>Last update: {vehicle.lastUpdate}</p>
                  </div>
                </Popup>
              </Marker>
            );
          })}
        </MapContainer>
      )}
    </div>
  );
};

export default MapDisplay;
