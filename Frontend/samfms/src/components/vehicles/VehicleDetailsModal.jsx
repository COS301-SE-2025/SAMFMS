import React from 'react';
import { X, Edit2, Trash2, Car, Fuel, Calendar } from 'lucide-react';

const VehicleDetailsModal = ({
  vehicle,
  closeVehicleDetails,
  openAssignmentModal,
  onEditVehicle,
  onDeleteVehicle,
}) => {
  if (!vehicle) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-card w-full max-w-4xl max-h-[90vh] rounded-lg shadow-xl overflow-hidden">
        <div className="p-6 flex flex-col h-full max-h-[90vh]">
          {/* Header */}
          <div className="flex justify-between items-center mb-6 pb-4 border-b border-border">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary/10 rounded-lg">
                <Car className="w-6 h-6 text-primary" />
              </div>
              <div>
                <h2 className="text-2xl font-bold">
                  {vehicle.make} {vehicle.model}
                </h2>
                <p className="text-muted-foreground">
                  {vehicle.year} • {vehicle.licensePlate}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span
                className={`py-1 px-3 rounded-full text-sm font-medium ${
                  vehicle.status === 'Active'
                    ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
                    : 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300'
                }`}
              >
                {vehicle.status}
              </span>
              <button
                onClick={closeVehicleDetails}
                className="text-muted-foreground hover:text-foreground transition p-1 rounded-md hover:bg-accent/20"
              >
                <X size={24} />
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="flex flex-col lg:flex-row gap-8 overflow-auto flex-1">
            {/* Left Column - Vehicle Information */}
            <div className="flex-1 space-y-6">
              {/* Basic Information */}
              <div className="bg-accent/10 rounded-lg p-4">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <Car className="w-5 h-5 text-primary" />
                  Vehicle Information
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-3">
                    <div>
                      <p className="text-sm text-muted-foreground font-medium">Vehicle ID</p>
                      <p className="text-lg">{vehicle.id}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground font-medium">VIN</p>
                      <p className="text-lg font-mono">{vehicle.vin}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground font-medium">Color</p>
                      <p className="text-lg">{vehicle.color || 'Not specified'}</p>
                    </div>
                  </div>
                  <div className="space-y-3">
                    <div>
                      <p className="text-sm text-muted-foreground font-medium">Department</p>
                      <p className="text-lg">{vehicle.department}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground font-medium">Acquisition Date</p>
                      <div className="flex items-center gap-2">
                        <Calendar className="w-4 h-4 text-muted-foreground" />
                        <p className="text-lg">{vehicle.acquisitionDate}</p>
                      </div>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground font-medium">Current Mileage</p>
                      <p className="text-lg font-semibold">{vehicle.mileage} km</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Fuel Information */}
              <div className="bg-accent/10 rounded-lg p-4">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <Fuel className="w-5 h-5 text-primary" />
                  Fuel Information
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-muted-foreground font-medium">Fuel Type</p>
                    <p className="text-lg capitalize">{vehicle.fuelType}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground font-medium">Fuel Efficiency</p>
                    <p className="text-lg">{vehicle.fuelEfficiency}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Right Column - Actions */}
            <div className="w-full lg:w-80 flex-shrink-0">
              <div className="bg-accent/10 rounded-lg p-4 sticky top-0">
                <h3 className="text-lg font-semibold mb-4">Actions</h3>
                <div className="space-y-3">
                  <button
                    className="w-full py-3 px-4 bg-primary text-primary-foreground rounded-lg flex items-center justify-center gap-2 hover:bg-primary/90 transition-colors font-medium"
                    onClick={() => {
                      closeVehicleDetails();
                      onEditVehicle?.(vehicle);
                    }}
                  >
                    <Edit2 size={16} />
                    <span>Edit Vehicle</span>
                  </button>
                  <button
                    className="w-full py-3 px-4 border border-destructive text-destructive rounded-lg flex items-center justify-center gap-2 hover:bg-destructive hover:text-destructive-foreground transition-colors font-medium"
                    onClick={() => {
                      if (
                        window.confirm(
                          `Are you sure you want to delete ${vehicle.make} ${vehicle.model}?`
                        )
                      ) {
                        closeVehicleDetails();
                        onDeleteVehicle?.(vehicle.id);
                      }
                    }}
                  >
                    <Trash2 size={16} />
                    <span>Delete Vehicle</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VehicleDetailsModal;
