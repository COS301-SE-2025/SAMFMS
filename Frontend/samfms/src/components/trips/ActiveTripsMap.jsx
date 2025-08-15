import React, { useState, useEffect, useRef } from 'react';
import { MapPin, Menu, Search, Navigation, Car, Clock, User, Locate } from 'lucide-react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
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
const MapUpdater = ({ center, zoom = 13 }) => {
  const map = useMap();

  useEffect(() => {
    if (center && center[0] && center[1]) {
      map.setView(center, zoom);
    }
  }, [center, zoom, map]);

  return null;
};

const ActiveTripsMap = ({ activeLocations = [] }) => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTrip, setSelectedTrip] = useState(null);
  const [mapCenter, setMapCenter] = useState([37.7749, -122.4194]);

  // Filter active trips based on search term
  const filteredTrips = activeLocations.filter(
    trip =>
      trip.vehicleName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      trip.driver.toLowerCase().includes(searchTerm.toLowerCase()) ||
      trip.destination.toLowerCase().includes(searchTerm.toLowerCase()) ||
      trip.status.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Handle trip selection
  const handleTripSelect = trip => {
    setSelectedTrip(trip);
    setMapCenter(trip.position);
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
          <MapUpdater center={mapCenter} zoom={13} />
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
    </div>
  );
};

export default ActiveTripsMap;
