import React from 'react';
import { X } from 'lucide-react';

const DriverAssignmentModal = ({
  closeAssignmentModal,
  selectedVehicles,
  handleSelectVehicle,
  vehicles,
  currentVehicle,
}) => {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-card w-full max-w-lg rounded-lg shadow-xl overflow-hidden">
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold">Assign Driver</h2>
            <button
              onClick={closeAssignmentModal}
              className="text-muted-foreground hover:text-foreground"
            >
              <X size={20} />
            </button>
          </div>

          <div className="mb-6">
            <h3 className="font-medium mb-2">Selected Vehicles</h3>
            {selectedVehicles.length > 0 ? (
              <div className="max-h-32 overflow-y-auto">
                {selectedVehicles.map(id => {
                  const vehicle = vehicles.find(v => v.id === id);
                  return (
                    <div
                      key={id}
                      className="flex items-center justify-between mb-2 p-2 bg-accent/10 rounded-md"
                    >
                      <span>
                        {vehicle.make} {vehicle.model} ({id})
                      </span>
                      <button
                        onClick={() => handleSelectVehicle(id)}
                        className="text-muted-foreground hover:text-destructive"
                      >
                        <X size={16} />
                      </button>
                    </div>
                  );
                })}
              </div>
            ) : currentVehicle ? (
              <div className="p-2 bg-accent/10 rounded-md">
                {currentVehicle.make} {currentVehicle.model} ({currentVehicle.id})
              </div>
            ) : (
              <p className="text-muted-foreground">No vehicles selected</p>
            )}
          </div>

          <div className="mb-6">
            <label className="block text-sm font-medium mb-2">Select Driver</label>
            <select className="w-full border border-border bg-background rounded-md p-2">
              <option value="">Select a driver...</option>
              <option value="john-doe">John Doe</option>
              <option value="emma-johnson">Emma Johnson</option>
              <option value="michael-smith">Michael Smith</option>
              <option value="sarah-davis">Sarah Davis</option>
              <option value="unassigned">Unassigned</option>
            </select>
          </div>

          <div className="mb-6">
            <label className="block text-sm font-medium mb-2">Assignment Date</label>
            <input
              type="date"
              className="w-full border border-border bg-background rounded-md p-2"
              defaultValue="2025-05-23"
            />
          </div>

          <div className="mb-6">
            <label className="block text-sm font-medium mb-2">Notes</label>
            <textarea
              className="w-full border border-border bg-background rounded-md p-2 min-h-[80px]"
              placeholder="Add any notes about this assignment..."
            />
          </div>

          <div className="flex justify-end gap-2">
            <button
              onClick={closeAssignmentModal}
              className="px-4 py-2 border border-border rounded-md hover:bg-accent/10 transition"
            >
              Cancel
            </button>
            <button className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition">
              Assign Driver
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DriverAssignmentModal;
