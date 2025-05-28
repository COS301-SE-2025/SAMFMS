import React from 'react';
import { X, Calendar, AlertTriangle, RefreshCw, Edit2, Trash2, Users } from 'lucide-react';
import TagList from './TagList';

const VehicleDetailsModal = ({ vehicle, closeVehicleDetails, openAssignmentModal }) => {
  if (!vehicle) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-card w-full max-w-4xl max-h-[90vh] rounded-lg shadow-xl overflow-hidden">
        <div className="p-6 flex flex-col h-full max-h-[90vh]">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-2xl font-semibold">Vehicle Details</h2>
            <button
              onClick={closeVehicleDetails}
              className="text-muted-foreground hover:text-foreground transition"
            >
              <X size={24} />
            </button>
          </div>

          <div className="flex flex-col md:flex-row gap-6 overflow-auto pb-6">
            {/* Left column - Vehicle info */}
            <div className="w-full md:w-2/3">
              <div className="flex items-center mb-4">
                <span
                  className={`py-1 px-2 rounded-full text-xs mr-2 ${
                    vehicle.status === 'Active'
                      ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                      : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                  }`}
                >
                  {vehicle.status}
                </span>
                <h3 className="text-xl font-medium">
                  {vehicle.make} {vehicle.model} ({vehicle.year})
                </h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                <div className="space-y-2">
                  <div>
                    <p className="text-sm text-muted-foreground">Vehicle ID</p>
                    <p className="font-medium">{vehicle.id}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">VIN</p>
                    <p className="font-medium">{vehicle.vin}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">License Plate</p>
                    <p className="font-medium">{vehicle.licensePlate}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Department</p>
                    <p className="font-medium">{vehicle.department}</p>
                  </div>
                </div>
                <div className="space-y-2">
                  <div>
                    <p className="text-sm text-muted-foreground">Current Mileage</p>
                    <p className="font-medium">{vehicle.mileage} km</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Fuel Type</p>
                    <p className="font-medium">{vehicle.fuelType}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Fuel Efficiency</p>
                    <p className="font-medium">{vehicle.fuelEfficiency}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Acquisition Date</p>
                    <p className="font-medium">{vehicle.acquisitionDate}</p>
                  </div>
                </div>
              </div>

              <div className="mb-6">
                <h4 className="font-medium mb-2">Tags</h4>
                <TagList tags={vehicle.tags} onAddTag={() => {}} />
              </div>

              <div className="mb-6">
                <h4 className="font-medium mb-2">Driver Information</h4>
                <div className="p-4 border border-border rounded-md">
                  {' '}
                  <div className="flex items-center mb-2">
                    <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center text-sm font-medium mr-3">
                      {vehicle.driver && vehicle.driver !== 'Unassigned'
                        ? vehicle.driver
                            .split(' ')
                            .map(n => n[0])
                            .join('')
                        : 'UA'}
                    </div>
                    <div>
                      <p className="font-medium">{vehicle.driver}</p>
                      <p className="text-sm text-muted-foreground">Current Driver</p>
                    </div>
                  </div>
                  <div className="text-sm">
                    <p className="text-muted-foreground">Last Driver: {vehicle.lastDriver}</p>
                  </div>
                  <button
                    onClick={openAssignmentModal}
                    className="mt-3 text-primary text-sm flex items-center hover:text-primary/80"
                  >
                    <Users size={14} className="mr-1" />
                    Change Driver
                  </button>
                </div>
              </div>

              <div>
                <h4 className="font-medium mb-2">Maintenance History</h4>
                <div className="border border-border rounded-md overflow-hidden">
                  <table className="w-full border-collapse">
                    <thead>
                      <tr className="border-b border-border bg-accent/20">
                        <th className="text-left py-2 px-4 font-medium text-sm">Date</th>
                        <th className="text-left py-2 px-4 font-medium text-sm">Service</th>
                        <th className="text-left py-2 px-4 font-medium text-sm">Cost</th>
                      </tr>
                    </thead>
                    <tbody>
                      {vehicle.maintenanceCosts.map((record, index) => (
                        <tr key={index} className="border-b border-border">
                          <td className="py-2 px-4 text-sm">{record.date}</td>
                          <td className="py-2 px-4 text-sm">{record.type}</td>
                          <td className="py-2 px-4 text-sm">${record.cost}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            {/* Right column - Status & Actions */}
            <div className="w-full md:w-1/3">
              <div className="border border-border rounded-md p-4 mb-6">
                <h4 className="font-medium mb-2">Maintenance Status</h4>
                <div className="space-y-3">
                  <div>
                    <p className="text-sm text-muted-foreground">Last Service</p>
                    <p className="font-medium">{vehicle.lastService}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Next Service</p>
                    <div className="flex items-center">
                      <Calendar size={14} className="mr-2 text-muted-foreground" />
                      <p className="font-medium">{vehicle.nextService}</p>
                    </div>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Insurance Expiry</p>
                    <div className="flex items-center">
                      <AlertTriangle size={14} className="mr-2 text-yellow-500" />
                      <p className="font-medium">{vehicle.insuranceExpiry}</p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="mb-6">
                <h4 className="font-medium mb-2">Actions</h4>
                <div className="space-y-2">
                  <button className="w-full py-2 border border-border rounded-md flex items-center justify-center gap-2 hover:bg-accent/20 transition">
                    <RefreshCw size={14} />
                    <span>Update Status</span>
                  </button>
                  <button className="w-full py-2 border border-border rounded-md flex items-center justify-center gap-2 hover:bg-accent/20 transition">
                    <Edit2 size={14} />
                    <span>Edit Details</span>
                  </button>
                  <button className="w-full py-2 border border-destructive text-destructive rounded-md flex items-center justify-center gap-2 hover:bg-destructive/10 transition">
                    <Trash2 size={14} />
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
