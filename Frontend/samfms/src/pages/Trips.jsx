import React, { useState } from 'react';
import VehicleStatistics from '../components/trips/VehicleStatistics';
import MapDisplay from '../components/trips/MapDisplay';
import VehicleList from '../components/trips/VehicleList';

const Trips = () => {
  // Sample mock data for vehicles with location
  const [vehicles] = useState([
    {
      id: 'VEH-001',
      make: 'Toyota',
      model: 'Camry',
      driver: 'John Smith',
      status: 'active',
      location: { latitude: 37.7749, longitude: -122.4194 },
      lastUpdate: '10 min ago',
      speed: '65 km/h',
      direction: 'North-East',
      fuelLevel: '70%',
    },
    {
      id: 'VEH-002',
      make: 'Ford',
      model: 'Transit',
      driver: 'Jane Wilson',
      status: 'idle',
      location: { latitude: 37.7833, longitude: -122.4167 },
      lastUpdate: '5 min ago',
      speed: '0 km/h',
      direction: 'Stopped',
      fuelLevel: '55%',
    },
    {
      id: 'VEH-003',
      make: 'Honda',
      model: 'CR-V',
      driver: 'Robert Johnson',
      status: 'active',
      location: { latitude: 37.7694, longitude: -122.4862 },
      lastUpdate: '2 min ago',
      speed: '58 km/h',
      direction: 'West',
      fuelLevel: '40%',
    },
    {
      id: 'VEH-004',
      make: 'Chevrolet',
      model: 'Suburban',
      driver: 'Emily Davis',
      status: 'maintenance',
      location: { latitude: 37.8044, longitude: -122.2711 },
      lastUpdate: '1 day ago',
      speed: '0 km/h',
      direction: 'Stopped',
      fuelLevel: '25%',
    },
    {
      id: 'VEH-005',
      make: 'Nissan',
      model: 'Rogue',
      driver: 'Michael Thompson',
      status: 'active',
      location: { latitude: 37.7879, longitude: -122.4074 },
      lastUpdate: '15 min ago',
      speed: '75 km/h',
      direction: 'South',
      fuelLevel: '80%',
    },
    {
      id: 'VEH-006',
      make: 'Tesla',
      model: 'Model 3',
      driver: 'Sarah Adams',
      status: 'idle',
      location: { latitude: 37.7701, longitude: -122.3845 },
      lastUpdate: '8 min ago',
      speed: '0 km/h',
      direction: 'Stopped',
      fuelLevel: '90%',
    },
    {
      id: 'VEH-007',
      make: 'Mercedes',
      model: 'Sprinter',
      driver: 'David Wilson',
      status: 'breakdown',
      location: { latitude: 37.784, longitude: -122.4378 },
      lastUpdate: '45 min ago',
      speed: '0 km/h',
      direction: 'Stopped',
      fuelLevel: '15%',
    },
  ]);

  // Calculate statistics
  const stats = {
    activeVehicles: vehicles.filter(v => v.status === 'active').length,
    idleVehicles: vehicles.filter(v => v.status === 'idle').length,
    nonOperationalVehicles: vehicles.filter(v => ['maintenance', 'breakdown'].includes(v.status))
      .length,
  };
  // State for selected vehicle
  const [selectedVehicle, setSelectedVehicle] = useState(null);

  const handleSelectVehicle = vehicle => {
    setSelectedVehicle(vehicle);
    // The map will automatically center on this vehicle via the MapController component
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Trip Management</h1>

      {/* Vehicle Statistics */}
      <VehicleStatistics stats={stats} />

      {/* Map and Vehicle List Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {' '}
        {/* Map display takes 2/3 of the width on large screens */}
        <div className="lg:col-span-2">
          <MapDisplay vehicles={vehicles} selectedVehicle={selectedVehicle} />
        </div>
        {/* Vehicle list takes 1/3 of the width on large screens */}
        <div className="lg:col-span-1">
          <VehicleList vehicles={vehicles} onSelectVehicle={handleSelectVehicle} />
        </div>
      </div>

      {/* Schedule Trip Button */}
      <div className="mt-6 flex justify-end">
        <button className="bg-primary text-primary-foreground px-4 py-2 rounded-md hover:bg-primary/90 transition">
          Schedule New Trip
        </button>
      </div>

      {/* Trip History Section */}
      <div className="mt-8">
        <h2 className="text-xl font-semibold mb-4">Trip History</h2>
        <div className="bg-card rounded-lg shadow-md p-6 border border-border">
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left py-3 px-4">Trip ID</th>
                  <th className="text-left py-3 px-4">Vehicle</th>
                  <th className="text-left py-3 px-4">Driver</th>
                  <th className="text-left py-3 px-4">Departure</th>
                  <th className="text-left py-3 px-4">Status</th>
                  <th className="text-left py-3 px-4">Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-border hover:bg-accent/10">
                  <td className="py-3 px-4">T-1001</td>
                  <td className="py-3 px-4">Toyota Camry (VEH-001)</td>
                  <td className="py-3 px-4">John Smith</td>
                  <td className="py-3 px-4">May 23, 2023 - 10:30 AM</td>
                  <td className="py-3 px-4">
                    <span className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 py-1 px-2 rounded-full text-xs">
                      Completed
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <button className="text-primary hover:text-primary/80">Details</button>
                  </td>
                </tr>
                <tr className="border-b border-border hover:bg-accent/10">
                  <td className="py-3 px-4">T-1002</td>
                  <td className="py-3 px-4">Ford Transit (VEH-002)</td>
                  <td className="py-3 px-4">Jane Wilson</td>
                  <td className="py-3 px-4">May 24, 2023 - 08:00 AM</td>
                  <td className="py-3 px-4">
                    <span className="bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 py-1 px-2 rounded-full text-xs">
                      In Progress
                    </span>
                  </td>
                  <td className="py-3 px-4 space-x-2">
                    <button className="text-primary hover:text-primary/80">Details</button>
                  </td>
                </tr>
                <tr className="border-b border-border hover:bg-accent/10">
                  <td className="py-3 px-4">T-1003</td>
                  <td className="py-3 px-4">Honda CR-V (VEH-003)</td>
                  <td className="py-3 px-4">Robert Johnson</td>
                  <td className="py-3 px-4">May 25, 2023 - 09:15 AM</td>
                  <td className="py-3 px-4">
                    <span className="bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200 py-1 px-2 rounded-full text-xs">
                      Scheduled
                    </span>
                  </td>
                  <td className="py-3 px-4 space-x-2">
                    <button className="text-primary hover:text-primary/80">Details</button>
                    <button className="text-destructive hover:text-destructive/80">Cancel</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Trips;
