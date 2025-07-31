import React, { useState, useEffect } from 'react';
import { X } from 'lucide-react';
import { getDrivers } from '../../backend/api/drivers';
import { createVehicleAssignment } from '../../backend/api/assignments';
import { useNotification } from '../../contexts/NotificationContext';

const DriverAssignmentModal = ({
  closeAssignmentModal,
  selectedVehicles,
  handleSelectVehicle,
  vehicles,
  currentVehicle,
  onAssignmentComplete,
}) => {
  const [drivers, setDrivers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    driverId: '',
    assignmentDate: new Date().toISOString().split('T')[0],
    notes: '',
    purpose: '',
  });

  const { showNotification } = useNotification();

  // Fetch drivers on component mount
  useEffect(() => {
    const fetchDrivers = async () => {
      try {
        const response = await getDrivers();
        setDrivers(response.drivers || []);
      } catch (error) {
        console.error('Error fetching drivers:', error);
        showNotification('Failed to load drivers', 'error');
      } finally {
        setLoading(false);
      }
    };

    fetchDrivers();
  }, [showNotification]);

  const handleSubmit = async e => {
    e.preventDefault();

    if (!formData.driverId) {
      showNotification('Please select a driver', 'error');
      return;
    }

    const vehiclesToAssign =
      selectedVehicles.length > 0 ? selectedVehicles : currentVehicle ? [currentVehicle.id] : [];

    if (vehiclesToAssign.length === 0) {
      showNotification('No vehicles selected for assignment', 'error');
      return;
    }

    setSubmitting(true);

    try {
      // Create assignments for each selected vehicle
      const assignmentPromises = vehiclesToAssign.map(vehicleId => {
        const assignmentData = {
          vehicle_id: vehicleId,
          driver_id: formData.driverId,
          purpose: formData.purpose,
          notes: formData.notes,
          start_date: new Date(formData.assignmentDate).toISOString(),
          status: 'active',
        };

        return createVehicleAssignment(assignmentData);
      });

      await Promise.all(assignmentPromises);

      showNotification(
        `Successfully assigned ${vehiclesToAssign.length} vehicle(s) to driver`,
        'success'
      );

      // Call callback to refresh vehicle data
      if (onAssignmentComplete) {
        onAssignmentComplete();
      }

      closeAssignmentModal();
    } catch (error) {
      console.error('Error creating assignment:', error);
      showNotification('Failed to create assignment', 'error');
    } finally {
      setSubmitting(false);
    }
  };

  const getDriverName = driver => {
    return `${driver.first_name} ${driver.last_name}`;
  };

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

          <form onSubmit={handleSubmit}>
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
                          type="button"
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
              {loading ? (
                <div className="w-full border border-border bg-background rounded-md p-2 text-center">
                  Loading drivers...
                </div>
              ) : (
                <select
                  className="w-full border border-border bg-background rounded-md p-2"
                  value={formData.driverId}
                  onChange={e => setFormData({ ...formData, driverId: e.target.value })}
                  required
                >
                  <option value="">Select a driver...</option>
                  {drivers.map(driver => (
                    <option key={driver._id} value={driver._id}>
                      {getDriverName(driver)} - {driver.license_number || 'No License'}
                    </option>
                  ))}
                  <option value="unassigned">Unassigned</option>
                </select>
              )}
            </div>

            <div className="mb-6">
              <label className="block text-sm font-medium mb-2">Purpose</label>
              <input
                type="text"
                className="w-full border border-border bg-background rounded-md p-2"
                placeholder="Purpose of assignment (e.g., Daily Operations, Project XYZ)"
                value={formData.purpose}
                onChange={e => setFormData({ ...formData, purpose: e.target.value })}
              />
            </div>

            <div className="mb-6">
              <label className="block text-sm font-medium mb-2">Assignment Date</label>
              <input
                type="date"
                className="w-full border border-border bg-background rounded-md p-2"
                value={formData.assignmentDate}
                onChange={e => setFormData({ ...formData, assignmentDate: e.target.value })}
                required
              />
            </div>

            <div className="mb-6">
              <label className="block text-sm font-medium mb-2">Notes</label>
              <textarea
                className="w-full border border-border bg-background rounded-md p-2 min-h-[80px]"
                placeholder="Add any notes about this assignment..."
                value={formData.notes}
                onChange={e => setFormData({ ...formData, notes: e.target.value })}
              />
            </div>

            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={closeAssignmentModal}
                className="px-4 py-2 border border-border rounded-md hover:bg-accent/10 transition"
                disabled={submitting}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition disabled:opacity-50"
                disabled={submitting || loading}
              >
                {submitting ? 'Assigning...' : 'Assign Driver'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default DriverAssignmentModal;
