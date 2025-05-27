import React, { useState } from 'react';

const initialForm = {
  id: '',
  make: '',
  model: '',
  year: '',
  mileage: '',
  driver: '',
  status: '',
  vin: '',
  licensePlate: '',
  fuelType: '',
  department: '',
  lastService: '',
  nextService: '',
  fuelEfficiency: '',
  tags: [],
  acquisitionDate: '',
  insuranceExpiry: '',
  lastDriver: '',
  maintenanceCosts: [],
};

const AddVehicleModal = ({ closeModal, vehicles, setVehicles }) => {
  const [form, setForm] = useState(initialForm);

  const handleChange = e => {
    const { name, value } = e.target;
    setForm(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async e => {
    e.preventDefault();
    const response = await fetch('http://localhost:8000/vehicles', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form),
    });
    const newVehicle = await response.json();
    setVehicles([...vehicles, newVehicle]);
    closeModal();
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white p-6 rounded-lg shadow-lg w-full max-w-lg">
        <h2 className="text-xl font-semibold mb-4">Add New Vehicle</h2>
        <form onSubmit={handleSubmit} className="space-y-3">
          <input
            name="id"
            value={form.id}
            onChange={handleChange}
            placeholder="Vehicle ID"
            className="w-full border p-2 rounded"
            required
          />
          <input
            name="make"
            value={form.make}
            onChange={handleChange}
            placeholder="Make"
            className="w-full border p-2 rounded"
            required
          />
          <input
            name="model"
            value={form.model}
            onChange={handleChange}
            placeholder="Model"
            className="w-full border p-2 rounded"
            required
          />
          <input
            name="year"
            value={form.year}
            onChange={handleChange}
            placeholder="Year"
            className="w-full border p-2 rounded"
            required
          />
          <input
            name="mileage"
            value={form.mileage}
            onChange={handleChange}
            placeholder="Mileage"
            className="w-full border p-2 rounded"
          />
          <input
            name="driver"
            value={form.driver}
            onChange={handleChange}
            placeholder="Driver"
            className="w-full border p-2 rounded"
          />
          {/* Add more fields as needed */}
          <div className="flex justify-end gap-2 mt-4">
            <button
              type="button"
              onClick={closeModal}
              className="px-4 py-2 rounded bg-gray-200 hover:bg-gray-300"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 rounded bg-primary text-white hover:bg-primary/90"
            >
              Add Vehicle
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddVehicleModal;