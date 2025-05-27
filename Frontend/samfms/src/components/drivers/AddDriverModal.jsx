import React, { useState } from 'react';

const initialForm = {
  idNumber: '',
  name: '',
  middlenames: '',
  surname: '',
  email: '',
  phone: '',
  licenseNumber: '',
};

const AddDriverModal = ({ closeModal, drivers, setDrivers }) => {
  const [form, setForm] = useState(initialForm);

  const handleChange = e => {
    const { name, value } = e.target;
    setForm(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async e => {
    e.preventDefault();
    const response = await fetch('http://localhost:8000/drivers', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form),
    });
    const newDriver = await response.json();
    setDrivers([...drivers, newDriver]);
    closeModal();
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white p-6 rounded-lg shadow-lg w-full max-w-lg">
        <h2 className="text-xl font-semibold mb-4">Add New Vehicle</h2>
        <form onSubmit={handleSubmit} className="space-y-3">
          <input
            name="idNumber"
            value={form.idNumber}
            onChange={handleChange}
            placeholder="Driver ID"
            className="w-full border p-2 rounded"
            required
          />
          <input
            name="name"
            value={form.name}
            onChange={handleChange}
            placeholder="Name"
            className="w-full border p-2 rounded"
            required
          />
          <input
            name="middlenames"
            value={form.middlenames}
            onChange={handleChange}
            placeholder="Middle names"
            className="w-full border p-2 rounded"
          />
          <input
            name="surname"
            value={form.surname}
            onChange={handleChange}
            placeholder="Surname"
            className="w-full border p-2 rounded"
          />
          <input
            name="email"
            value={form.email}
            onChange={handleChange}
            placeholder="Email"
            className="w-full border p-2 rounded"
            required
          />
          <input
            name="phone"
            value={form.phone}
            onChange={handleChange}
            placeholder="Phone"
            className="w-full border p-2 rounded"
            required
          />
          <input
            name="licenseNumber"
            value={form.licenseNumber}
            onChange={handleChange}
            placeholder="License Number"
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

export default AddDriverModal;