import React from 'react';
import { MapPin } from 'lucide-react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
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

const ActiveTripsMap = ({ activeLocations = [] }) => {
  return (
    <div className="bg-card border border-border rounded-xl shadow-lg overflow-hidden animate-fade-in animate-delay-200">
      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <MapPin className="h-5 w-5 text-primary" />
            <h3 className="text-lg font-semibold">Active Trip Locations</h3>
          </div>
          <div className="text-sm text-muted-foreground">
            {activeLocations.length} vehicles tracked
          </div>
        </div>
      </div>
      <div className="h-96 relative">
        <MapContainer
          center={[37.7749, -122.4194]}
          zoom={12}
          style={{ height: '100%', width: '100%' }}
          className="rounded-b-xl"
          zoomControl={false}
        >
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          />
          {activeLocations &&
            activeLocations.length > 0 &&
            activeLocations.map(location => (
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
        </MapContainer>

        {/* Map Controls Overlay */}
        <div className="absolute top-4 right-4 flex flex-col gap-2 z-[1000]">
          <div className="bg-white dark:bg-card border border-border rounded-lg shadow-lg p-2">
            <div className="flex items-center gap-2 text-sm">
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
          </div>
        </div>
      </div>
    </div>
  );
};

export default ActiveTripsMap;
