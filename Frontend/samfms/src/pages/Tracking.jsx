import React, { useState, useEffect } from 'react';
import VehicleStatistics from '../components/trips/VehicleStatistics';
import VehicleList from '../components/trips/VehicleList';
import TrackingMap from '../components/tracking/TrackingMap';
import GeofenceManager from '../components/tracking/GeofenceManager';
import LocationHistory from '../components/tracking/LocationHistory';

const Tracking = () => {
  // Sample mock data for vehicles with location
  const [vehicles, setVehicles] = useState([]);
  const [selectedVehicle, setSelectedVehicle] = useState(null);

  useEffect(() => {
    // Connect to your Core backend WebSocket endpoint
    const ws = new WebSocket('ws://localhost:8000/ws/vehicles'); // Adjust URL/port as needed

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log("Received vehicles from Core:", data.vehicles);
      setVehicles(data.vehicles); // Expecting { vehicles: [...] }
    };

    ws.onerror = (err) => {
      console.error('WebSocket error:', err);
    };

    return () => ws.close();
  }, []);

  // Calculate statistics
  const stats = {
    activeVehicles: vehicles.filter(v => v.status === 'active').length,
    idleVehicles: vehicles.filter(v => v.status === 'idle').length,
    nonOperationalVehicles: vehicles.filter(v => ['maintenance', 'breakdown'].includes(v.status))
      .length,
  };

  const handleSelectVehicle = vehicle => {
    setSelectedVehicle(vehicle);
    // The map will automatically center on this vehicle via the MapController component
  };
  return (
    <div className="container mx-auto px-4 py-8">
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
          <TrackingMap vehicles={vehicles} selectedVehicle={selectedVehicle} />
        </div>{' '}
        {/* Vehicle list takes 1/3 of the width on large screens */}
        <div className="lg:col-span-1">
          <VehicleList vehicles={vehicles} onSelectVehicle={handleSelectVehicle} />
        </div>
      </div>{' '}
      {/* Geofence Management Component */}
      <div className="mt-8">
        <GeofenceManager />
      </div>{' '}
      {/* Location History Component */}
      <div className="mt-8 mb-8">
        <LocationHistory vehicles={vehicles} />
      </div>
    </div>
  );
};

export default Tracking;
