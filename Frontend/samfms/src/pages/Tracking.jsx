import React, {useState, useEffect} from 'react';
import VehicleStatistics from '../components/trips/VehicleStatistics';
import VehicleList from '../components/trips/VehicleList';
import TrackingMap from '../components/tracking/TrackingMap';
import GeofenceManager from '../components/tracking/GeofenceManager';
import LocationHistory from '../components/tracking/LocationHistory';

const Tracking = () => {
  const [vehicles, setVehicles] = useState([]);
  const [selectedVehicle, setSelectedVehicle] = useState(null);
  const [geofences, setGeofences] = useState([]);

  useEffect(() => {
    // Connect to your Core backend WebSocket endpoint
    const ws = new WebSocket('wss://capstone-samfms.dns.net.za:21017/ws/vehicles');

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.vehicles) {
        setVehicles(data.vehicles);
      } else {
        setVehicles([]);
        console.warn("No vehicles data received:", data);
      }
    };

    ws.onerror = (err) => {
      console.error('WebSocket error:', err);
    };

    ws.onclose = (event) => {
      console.warn('WebSocket closed:', event);
    };

    return () => ws.close();
  }, []);

  // Calculate statistics
  const stats = {
    activeVehicles: vehicles.filter(v => v.status === 'online').length,
    idleVehicles: vehicles.filter(v => v.status === 'offline').length,
    // nonOperationalVehicles: vehicles.filter(v => ['maintenance', 'breakdown'].includes(v.status))
    //   .length,
  };

  const handleSelectVehicle = vehicle => {
    setSelectedVehicle(vehicle);
    // The map will automatically center on this vehicle via the MapController component
  };

  // Handle geofence changes from the GeofenceManager
  const handleGeofenceChange = (updatedGeofences) => {
    console.log("Geofences updated:", updatedGeofences);
    setGeofences(updatedGeofences);
  };

  return (
    <div className="relative container mx-auto px-4 py-8">
      {/* Background pattern */}
      <div
        className="absolute inset-0 z-0 opacity-10 pointer-events-none"
        style={{
          backgroundImage: 'url("/logo/logo_icon_dark.svg")',
          backgroundSize: '200px',
          backgroundRepeat: 'repeat',
          filter: 'blur(1px)',
        }}
        aria-hidden="true"
      />

      <div className="relative z-10">
        <h1 className="text-3xl font-bold mb-6">Vehicle Tracking</h1>
        {/* Tracking Analytics Section - Moved to the top */}
        <div className="mb-6">
          <h2 className="text-xl font-semibold mb-4">Tracking Analytics</h2>
          <div className="bg-card rounded-lg shadow-md p-6 border border-border">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {' '}
              <div className="p-4 bg-accent/10 rounded-md">
                <p className="text-sm text-muted-foreground">Total Distance Today</p>
                <p className="text-2xl font-bold">462 km</p>
              </div>
              <div className="p-4 bg-accent/10 rounded-md">
                <p className="text-sm text-muted-foreground">Avg. Speed</p>
                <p className="text-2xl font-bold">55 km/h</p>
              </div>
              <div className="p-4 bg-accent/10 rounded-md">
                <p className="text-sm text-muted-foreground">Fuel Used Today</p>
                <p className="text-2xl font-bold">170 L</p>
              </div>
              <div className="p-4 bg-accent/10 rounded-md">
                <p className="text-sm text-muted-foreground">Idle Time</p>
                <p className="text-2xl font-bold">1.5 hrs</p>
              </div>
            </div>
          </div>
        </div>
        {/* Vehicle Statistics */}
        <VehicleStatistics stats={stats} />
        {/* Map and Vehicle List Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {' '}
          {/* Map display takes 2/3 of the width on large screens */}
          <div className="lg:col-span-2">
            <TrackingMap 
              vehicles={vehicles} 
              selectedVehicle={selectedVehicle}
              geofences={geofences} 
            />
          </div>{' '}
          {/* Vehicle list takes 1/3 of the width on large screens */}
          <div className="lg:col-span-1">
            <VehicleList vehicles={vehicles} onSelectVehicle={handleSelectVehicle} />
          </div>
        </div>{' '}
        {/* Geofence Management Component */}
        <div className="mt-8">
          <GeofenceManager 
            onGeofenceChange={handleGeofenceChange}
            currentGeofences={geofences}
          />
        </div>{' '}
        {/* Location History Component */}
        <div className="mt-8 mb-8">
          <LocationHistory vehicles={vehicles} />
        </div>
      </div>
    </div>
  );
};

export default Tracking;