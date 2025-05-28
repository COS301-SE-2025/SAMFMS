import React, { useState, useEffect } from 'react';
import { updateVehicle } from '../../backend/API';

const EditVehicleModal = ({ vehicle, closeModal, onVehicleUpdated }) => {
  const [form, setForm] = useState({
    make: '',
    model: '',
    year: '',
    vin: '',
    license_plate: '',
    color: '',
    fuel_type: '',
    mileage: '',
    status: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Initialize form with vehicle data
  useEffect(() => {
    if (vehicle) {
      setForm({
        make: vehicle.make || '',
        model: vehicle.model || '',
        year: vehicle.year || '',
        vin: vehicle.vin || '',
        license_plate: vehicle.licensePlate || '',
        color: vehicle.color || '',
        fuel_type: vehicle.fuelType || '',
        mileage: vehicle.mileage ? parseInt(vehicle.mileage) : 0,
        status: vehicle.status?.toLowerCase() || 'active',
      });
    }
  }, [vehicle]);

  const handleChange = e => {
    const { name, value } = e.target;
    setForm(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async e => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      // Validate VIN (should be 17 characters)
      if (form.vin && form.vin.length !== 17) {
        throw new Error('VIN must be exactly 17 characters');
      }

      // Validate license plate
      if (form.license_plate && (form.license_plate.length < 4 || form.license_plate.length > 10)) {
        throw new Error('License plate must be 4-10 characters');
      }

      // Validate year
      const yearValue = parseInt(form.year);
      if (isNaN(yearValue) || yearValue < 1900 || yearValue > 2030) {
        throw new Error('Year must be between 1900 and 2030');
      }

      const response = await updateVehicle(vehicle.id, form);
      onVehicleUpdated(response);
      closeModal();
    } catch (err) {
      console.error('Error updating vehicle:', err);
      setError(err.message || 'Failed to update vehicle');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-card dark:bg-card p-6 rounded-lg shadow-lg w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <h2 className="text-xl font-semibold mb-4 text-card-foreground">Edit Vehicle</h2>

        {error && (
          <div className="bg-destructive/10 border border-destructive text-destructive px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-3">
          {' '}
          <div>
            <label className="block text-sm font-medium text-card-foreground mb-1">Make</label>
            <input
              name="make"
              value={form.make}
              onChange={handleChange}
              className="w-full border p-2 rounded bg-background dark:bg-muted text-foreground dark:text-foreground"
              required
            />
          </div>{' '}
          <div>
            <label className="block text-sm font-medium text-card-foreground mb-1">Model</label>
            <input
              name="model"
              value={form.model}
              onChange={handleChange}
              className="w-full border p-2 rounded bg-background dark:bg-muted text-foreground dark:text-foreground"
              required
            />
          </div>{' '}
          <div>
            <label className="block text-sm font-medium text-card-foreground mb-1">Year</label>
            <input
              name="year"
              value={form.year}
              onChange={handleChange}
              type="number"
              min="1900"
              max="2030"
              className="w-full border p-2 rounded bg-background dark:bg-muted text-foreground dark:text-foreground"
              required
            />
          </div>{' '}
          <div>
            <label className="block text-sm font-medium text-card-foreground mb-1">
              VIN (17 characters)
            </label>
            <input
              name="vin"
              value={form.vin}
              onChange={handleChange}
              className="w-full border p-2 rounded bg-background dark:bg-muted text-foreground dark:text-foreground"
              maxLength="17"
              minLength="17"
              required
            />
          </div>{' '}
          <div>
            <label className="block text-sm font-medium text-card-foreground mb-1">
              License Plate
            </label>
            <input
              name="license_plate"
              value={form.license_plate}
              onChange={handleChange}
              className="w-full border p-2 rounded bg-background dark:bg-muted text-foreground dark:text-foreground"
              required
            />
          </div>{' '}
          <div>
            <label className="block text-sm font-medium text-card-foreground mb-1">Color</label>
            <input
              name="color"
              value={form.color}
              onChange={handleChange}
              className="w-full border p-2 rounded bg-background dark:bg-muted text-foreground dark:text-foreground"
            />
          </div>{' '}
          <div>
            <label className="block text-sm font-medium text-card-foreground mb-1">Fuel Type</label>
            <select
              name="fuel_type"
              value={form.fuel_type}
              onChange={handleChange}
              className="w-full border p-2 rounded bg-background dark:bg-muted text-foreground dark:text-foreground"
              required
            >
              <option value="gasoline">Gasoline</option>
              <option value="diesel">Diesel</option>
              <option value="hybrid">Hybrid</option>
              <option value="electric">Electric</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Mileage</label>
            <input
              name="mileage"
              value={form.mileage}
              onChange={handleChange}
              type="number"
              min="0"
              className="w-full border p-2 rounded"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Status</label>
            <select
              name="status"
              value={form.status}
              onChange={handleChange}
              className="w-full border p-2 rounded"
              required
            >
              <option value="active">Active</option>
              <option value="maintenance">Maintenance</option>
              <option value="inactive">Inactive</option>
            </select>
          </div>
          <div className="flex justify-end gap-2 mt-4">
            <button
              type="button"
              onClick={closeModal}
              className="px-4 py-2 rounded bg-gray-200 hover:bg-gray-300"
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 rounded bg-primary text-white hover:bg-primary/90"
              disabled={loading}
            >
              {loading ? 'Updating...' : 'Update Vehicle'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EditVehicleModal;
