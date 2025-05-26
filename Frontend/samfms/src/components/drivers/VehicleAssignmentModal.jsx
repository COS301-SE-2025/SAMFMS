import React, { useState } from 'react';
import { X, Search } from 'lucide-react';

const VehicleAssignmentModal = ({
  closeVehicleAssignmentModal,
  selectedDrivers,
  currentDriver,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedVehicle, setSelectedVehicle] = useState(null);

  // Sample vehicles data (in a real app this would come from props or an API)
  const vehicles = [
    {
      id: 'VEH-001',
      make: 'Toyota',
      model: 'Camry',
      year: '2023',
      licensePlate: 'ABC-1234',
      status: 'Available',
    },
    {
      id: 'VEH-002',
      make: 'Ford',
      model: 'Transit',
      year: '2022',
      licensePlate: 'XYZ-5678',
      status: 'Available',
    },
    {
      id: 'VEH-003',
      make: 'Honda',
      model: 'Civic',
      year: '2021',
      licensePlate: 'DEF-9012',
      status: 'In Use',
    },
  ];

  const filteredVehicles = vehicles.filter(
    vehicle =>
      vehicle.make.toLowerCase().includes(searchTerm.toLowerCase()) ||
      vehicle.model.toLowerCase().includes(searchTerm.toLowerCase()) ||
      vehicle.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      vehicle.licensePlate.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleAssignVehicle = () => {
    if (!selectedVehicle) return;

    // In a real app, this would make an API call
    console.log(
      `Assigned vehicle ${selectedVehicle.id} to driver ${
        currentDriver ? currentDriver.id : 'multiple drivers'
      }`
    );

    closeVehicleAssignmentModal();
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-background rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-auto animate-in fade-in-0 zoom-in-95">
        <div className="sticky top-0 bg-background z-10 p-4 border-b border-border flex items-center justify-between">
          <h2 className="text-xl font-bold">Assign Vehicle</h2>
          <button onClick={closeVehicleAssignmentModal} className="hover:bg-muted rounded-full p-1">
            <X size={20} />
          </button>
        </div>

        <div className="p-6">
          <div className="mb-6">
            <h3 className="text-lg font-medium mb-2">
              {currentDriver
                ? `Assign a vehicle to ${currentDriver.name}`
                : `Assign a vehicle to ${selectedDrivers.length} selected drivers`}
            </h3>
            <p className="text-muted-foreground text-sm">
              Select from available vehicles below to assign to the driver(s).
            </p>
          </div>

          <div className="mb-6">
            <div className="relative">
              <input
                type="text"
                placeholder="Search by vehicle ID, make, model, or license plate"
                className="w-full px-4 py-2 pl-10 rounded-md border border-input bg-background"
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
              />
              <Search
                className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground"
                size={18}
              />
            </div>
          </div>

          <div className="border border-border rounded-md overflow-hidden mb-6">
            <table className="w-full text-sm">
              <thead className="bg-muted/50">
                <tr>
                  <th className="w-[36px] px-4 py-3"></th>
                  <th className="px-4 py-3 text-left">Vehicle ID</th>
                  <th className="px-4 py-3 text-left">Make & Model</th>
                  <th className="px-4 py-3 text-left">Year</th>
                  <th className="px-4 py-3 text-left">License Plate</th>
                  <th className="px-4 py-3 text-left">Status</th>
                </tr>
              </thead>
              <tbody>
                {filteredVehicles.map(vehicle => (
                  <tr
                    key={vehicle.id}
                    className={`border-t border-border hover:bg-accent/10 cursor-pointer ${
                      selectedVehicle?.id === vehicle.id ? 'bg-primary/10' : ''
                    }`}
                    onClick={() => setSelectedVehicle(vehicle)}
                  >
                    <td className="px-4 py-3">
                      <input
                        type="radio"
                        checked={selectedVehicle?.id === vehicle.id}
                        onChange={() => setSelectedVehicle(vehicle)}
                        className="rounded-full border-gray-300"
                      />
                    </td>
                    <td className="px-4 py-3">{vehicle.id}</td>
                    <td className="px-4 py-3">
                      {vehicle.make} {vehicle.model}
                    </td>
                    <td className="px-4 py-3">{vehicle.year}</td>
                    <td className="px-4 py-3">{vehicle.licensePlate}</td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-block px-2 py-1 rounded-full text-xs ${
                          vehicle.status === 'Available'
                            ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                            : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                        }`}
                      >
                        {vehicle.status}
                      </span>
                    </td>
                  </tr>
                ))}
                {filteredVehicles.length === 0 && (
                  <tr>
                    <td colSpan="6" className="px-4 py-3 text-center text-muted-foreground">
                      No vehicles found
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          <div className="flex justify-end space-x-2">
            <button
              onClick={closeVehicleAssignmentModal}
              className="px-4 py-2 border border-input rounded-md hover:bg-accent hover:text-accent-foreground"
            >
              Cancel
            </button>
            <button
              onClick={handleAssignVehicle}
              disabled={!selectedVehicle}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
            >
              Assign Vehicle
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VehicleAssignmentModal;
