import React, { useState, useEffect } from 'react';
import { maintenanceAPI } from '../backend/api/maintenance';

const LicenseManagement = ({ vehicles }) => {
  const [licenses, setLicenses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [editingLicense, setEditingLicense] = useState(null);
  const [filters, setFilters] = useState({
    vehicleId: '',
    licenseType: '',
  });

  const [formData, setFormData] = useState({
    vehicle_id: '',
    license_type: '',
    license_number: '',
    issued_date: '',
    expiry_date: '',
    issuing_authority: '',
    cost: '',
    notes: '',
    is_active: true,
  });

  const licenseTypes = [
    'registration',
    'license_disk',
    'roadworthy_certificate',
    'insurance',
    'permit',
    'inspection_certificate',
    'other',
  ];

  useEffect(() => {
    loadLicenses();
  }, [filters]);

  const loadLicenses = async () => {
    try {
      setLoading(true);
      const response = await maintenanceAPI.getLicenseRecords(
        filters.vehicleId || null,
        filters.licenseType || null
      );
      setLicenses(response.data || []);
    } catch (err) {
      console.error('Error loading license records:', err);
      setError('Failed to load license records');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async e => {
    e.preventDefault();
    try {
      const submitData = {
        ...formData,
        cost: parseFloat(formData.cost) || 0,
      };

      if (editingLicense) {
        await maintenanceAPI.updateLicenseRecord(editingLicense.id, submitData);
      } else {
        await maintenanceAPI.createLicenseRecord(submitData);
      }

      setShowModal(false);
      setEditingLicense(null);
      resetForm();
      loadLicenses();
    } catch (err) {
      console.error('Error saving license record:', err);
      setError('Failed to save license record');
    }
  };

  const handleEdit = license => {
    setEditingLicense(license);
    setFormData({
      vehicle_id: license.vehicle_id || '',
      license_type: license.license_type || '',
      license_number: license.license_number || '',
      issued_date: license.issued_date
        ? new Date(license.issued_date).toISOString().split('T')[0]
        : '',
      expiry_date: license.expiry_date
        ? new Date(license.expiry_date).toISOString().split('T')[0]
        : '',
      issuing_authority: license.issuing_authority || '',
      cost: license.cost?.toString() || '',
      notes: license.notes || '',
      is_active: license.is_active !== false,
    });
    setShowModal(true);
  };

  const handleDelete = async licenseId => {
    if (window.confirm('Are you sure you want to delete this license record?')) {
      try {
        await maintenanceAPI.deleteLicenseRecord(licenseId);
        loadLicenses();
      } catch (err) {
        console.error('Error deleting license record:', err);
        setError('Failed to delete license record');
      }
    }
  };

  const resetForm = () => {
    setFormData({
      vehicle_id: '',
      license_type: '',
      license_number: '',
      issued_date: '',
      expiry_date: '',
      issuing_authority: '',
      cost: '',
      notes: '',
      is_active: true,
    });
  };

  const getVehicleName = vehicleId => {
    const vehicle = vehicles.find(v => v.id === vehicleId);
    return vehicle ? `${vehicle.make} ${vehicle.model} (${vehicle.license_plate})` : vehicleId;
  };

  const getExpiryStatus = expiryDate => {
    if (!expiryDate) return null;

    const now = new Date();
    const expiry = new Date(expiryDate);
    const daysUntilExpiry = Math.ceil((expiry - now) / (1000 * 60 * 60 * 24));

    if (daysUntilExpiry < 0) {
      return (
        <span className="px-2 py-1 rounded-full text-xs bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">
          Expired
        </span>
      );
    } else if (daysUntilExpiry <= 7) {
      return (
        <span className="px-2 py-1 rounded-full text-xs bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">
          Expires Soon
        </span>
      );
    } else if (daysUntilExpiry <= 30) {
      return (
        <span className="px-2 py-1 rounded-full text-xs bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200">
          Expires This Month
        </span>
      );
    } else if (daysUntilExpiry <= 90) {
      return (
        <span className="px-2 py-1 rounded-full text-xs bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
          Expires Soon
        </span>
      );
    }

    return (
      <span className="px-2 py-1 rounded-full text-xs bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
        Valid
      </span>
    );
  };

  const getDaysUntilExpiry = expiryDate => {
    if (!expiryDate) return null;

    const now = new Date();
    const expiry = new Date(expiryDate);
    const daysUntilExpiry = Math.ceil((expiry - now) / (1000 * 60 * 60 * 24));

    if (daysUntilExpiry < 0) {
      return `${Math.abs(daysUntilExpiry)} days overdue`;
    } else if (daysUntilExpiry === 0) {
      return 'Expires today';
    } else if (daysUntilExpiry === 1) {
      return 'Expires tomorrow';
    } else {
      return `${daysUntilExpiry} days remaining`;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header and Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <h2 className="text-xl font-semibold">License & Permit Management</h2>
        <button
          onClick={() => {
            setEditingLicense(null);
            resetForm();
            setShowModal(true);
          }}
          className="bg-primary text-primary-foreground px-4 py-2 rounded-md hover:bg-primary/90 transition"
        >
          Add New License
        </button>
      </div>

      {/* Filters */}
      <div className="bg-card rounded-lg shadow-md p-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Filter by Vehicle</label>
            <select
              value={filters.vehicleId}
              onChange={e => setFilters(prev => ({ ...prev, vehicleId: e.target.value }))}
              className="w-full border border-border rounded-md px-3 py-2"
            >
              <option value="">All Vehicles</option>
              {vehicles.map(vehicle => (
                <option key={vehicle.id} value={vehicle.id}>
                  {getVehicleName(vehicle.id)}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Filter by License Type</label>
            <select
              value={filters.licenseType}
              onChange={e => setFilters(prev => ({ ...prev, licenseType: e.target.value }))}
              className="w-full border border-border rounded-md px-3 py-2"
            >
              <option value="">All Types</option>
              {licenseTypes.map(type => (
                <option key={type} value={type}>
                  {type.replace('_', ' ').toUpperCase()}
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-end">
            <button
              onClick={() => setFilters({ vehicleId: '', licenseType: '' })}
              className="bg-gray-500 text-white px-4 py-2 rounded-md hover:bg-gray-600 transition"
            >
              Clear Filters
            </button>
          </div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <p className="text-red-600 dark:text-red-400">{error}</p>
          <button
            onClick={() => setError(null)}
            className="text-red-800 dark:text-red-200 hover:underline text-sm mt-2"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Loading State */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          <span className="ml-3">Loading license records...</span>
        </div>
      ) : (
        <div className="bg-card rounded-lg shadow-md overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-muted">
                <tr>
                  <th className="text-left py-3 px-4 font-medium">Vehicle</th>
                  <th className="text-left py-3 px-4 font-medium">License Type</th>
                  <th className="text-left py-3 px-4 font-medium">License Number</th>
                  <th className="text-left py-3 px-4 font-medium">Issued Date</th>
                  <th className="text-left py-3 px-4 font-medium">Expiry Date</th>
                  <th className="text-left py-3 px-4 font-medium">Status</th>
                  <th className="text-left py-3 px-4 font-medium">Cost</th>
                  <th className="text-left py-3 px-4 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {licenses.length > 0 ? (
                  licenses.map(license => (
                    <tr key={license.id} className="border-b border-border hover:bg-accent/10">
                      <td className="py-3 px-4">{getVehicleName(license.vehicle_id)}</td>
                      <td className="py-3 px-4">
                        <div>
                          <p className="font-medium">{license.license_type?.replace('_', ' ')}</p>
                          {license.issuing_authority && (
                            <p className="text-sm text-muted-foreground">
                              {license.issuing_authority}
                            </p>
                          )}
                        </div>
                      </td>
                      <td className="py-3 px-4">{license.license_number || 'N/A'}</td>
                      <td className="py-3 px-4">
                        {license.issued_date
                          ? new Date(license.issued_date).toLocaleDateString()
                          : 'N/A'}
                      </td>
                      <td className="py-3 px-4">
                        <div>
                          <p>
                            {license.expiry_date
                              ? new Date(license.expiry_date).toLocaleDateString()
                              : 'N/A'}
                          </p>
                          {license.expiry_date && (
                            <p className="text-xs text-muted-foreground">
                              {getDaysUntilExpiry(license.expiry_date)}
                            </p>
                          )}
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <div className="space-y-1">
                          {getExpiryStatus(license.expiry_date)}
                          {!license.is_active && (
                            <span className="px-2 py-1 rounded-full text-xs bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200 block">
                              Inactive
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="py-3 px-4">R{license.cost?.toLocaleString() || 0}</td>
                      <td className="py-3 px-4">
                        <div className="flex space-x-2">
                          <button
                            onClick={() => handleEdit(license)}
                            className="text-blue-600 hover:text-blue-800 text-sm"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => handleDelete(license.id)}
                            className="text-red-600 hover:text-red-800 text-sm"
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="8" className="py-8 text-center text-muted-foreground">
                      No license records found
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Modal for Adding/Editing Licenses */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-900 rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4">
              {editingLicense ? 'Edit License Record' : 'Add New License Record'}
            </h3>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Vehicle *</label>
                  <select
                    value={formData.vehicle_id}
                    onChange={e => setFormData(prev => ({ ...prev, vehicle_id: e.target.value }))}
                    required
                    className="w-full border border-border rounded-md px-3 py-2"
                  >
                    <option value="">Select Vehicle</option>
                    {vehicles.map(vehicle => (
                      <option key={vehicle.id} value={vehicle.id}>
                        {getVehicleName(vehicle.id)}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">License Type *</label>
                  <select
                    value={formData.license_type}
                    onChange={e => setFormData(prev => ({ ...prev, license_type: e.target.value }))}
                    required
                    className="w-full border border-border rounded-md px-3 py-2"
                  >
                    <option value="">Select Type</option>
                    {licenseTypes.map(type => (
                      <option key={type} value={type}>
                        {type.replace('_', ' ').toUpperCase()}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">License Number</label>
                  <input
                    type="text"
                    value={formData.license_number}
                    onChange={e =>
                      setFormData(prev => ({ ...prev, license_number: e.target.value }))
                    }
                    className="w-full border border-border rounded-md px-3 py-2"
                    placeholder="Enter license number"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Issuing Authority</label>
                  <input
                    type="text"
                    value={formData.issuing_authority}
                    onChange={e =>
                      setFormData(prev => ({ ...prev, issuing_authority: e.target.value }))
                    }
                    className="w-full border border-border rounded-md px-3 py-2"
                    placeholder="e.g., Department of Transport"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Issued Date</label>
                  <input
                    type="date"
                    value={formData.issued_date}
                    onChange={e => setFormData(prev => ({ ...prev, issued_date: e.target.value }))}
                    className="w-full border border-border rounded-md px-3 py-2"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Expiry Date</label>
                  <input
                    type="date"
                    value={formData.expiry_date}
                    onChange={e => setFormData(prev => ({ ...prev, expiry_date: e.target.value }))}
                    className="w-full border border-border rounded-md px-3 py-2"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Cost</label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.cost}
                    onChange={e => setFormData(prev => ({ ...prev, cost: e.target.value }))}
                    className="w-full border border-border rounded-md px-3 py-2"
                    placeholder="0.00"
                  />
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="is_active"
                    checked={formData.is_active}
                    onChange={e => setFormData(prev => ({ ...prev, is_active: e.target.checked }))}
                    className="rounded border-border"
                  />
                  <label htmlFor="is_active" className="ml-2 text-sm font-medium">
                    Active License
                  </label>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Notes</label>
                <textarea
                  value={formData.notes}
                  onChange={e => setFormData(prev => ({ ...prev, notes: e.target.value }))}
                  className="w-full border border-border rounded-md px-3 py-2"
                  rows="3"
                  placeholder="Additional notes about this license..."
                />
              </div>

              <div className="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowModal(false);
                    setEditingLicense(null);
                    resetForm();
                  }}
                  className="px-4 py-2 border border-border rounded-md hover:bg-accent transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition"
                >
                  {editingLicense ? 'Update' : 'Create'} License
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default LicenseManagement;
