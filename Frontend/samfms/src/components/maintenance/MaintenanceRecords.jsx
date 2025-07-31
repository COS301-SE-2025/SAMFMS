import React, { useState, useEffect } from 'react';
import { maintenanceAPI } from '../../backend/api/maintenance';

const MaintenanceRecords = ({ vehicles }) => {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [editingRecord, setEditingRecord] = useState(null);
  const [filters, setFilters] = useState({
    vehicleId: '',
    status: '',
    page: 1,
    size: 20,
  });
  const [pagination, setPagination] = useState({
    total: 0,
    pages: 0,
    current_page: 1,
  });

  const [formData, setFormData] = useState({
    vehicle_id: '',
    maintenance_type: '',
    title: '', // Required field for maintenance record
    description: '',
    cost: '',
    scheduled_date: new Date().toISOString().split('T')[0], // Required field
    date_performed: '',
    next_due_date: '',
    vendor_id: '',
    notes: '',
    priority: 'medium',
    status: 'scheduled',
  });

  const maintenanceTypes = [
    'oil_change',
    'brake_service',
    'tire_rotation',
    'engine_service',
    'transmission_service',
    'coolant_service',
    'battery_service',
    'air_filter',
    'fuel_filter',
    'spark_plugs',
    'belt_replacement',
    'suspension',
    'exhaust_service',
    'electrical',
    'bodywork',
    'other',
  ];

  const statusOptions = ['scheduled', 'in_progress', 'completed', 'cancelled'];
  const priorityOptions = ['low', 'medium', 'high', 'urgent'];

  useEffect(() => {
    loadRecords();
  }, [filters]); // eslint-disable-line react-hooks/exhaustive-deps

  const loadRecords = async () => {
    try {
      setLoading(true);
      const response = await maintenanceAPI.getMaintenanceRecords(
        filters.vehicleId || null,
        filters.status || null,
        filters.page,
        filters.size
      );

      // Handle nested data structure from backend
      const data = response.data?.data || response.data || {};
      const records = data.maintenance_records || data.records || data || [];

      setRecords(records);
      setPagination({
        total: data.total || 0,
        pages: data.pages || Math.ceil((data.total || 0) / filters.size),
        current_page: filters.page || 1,
      });
    } catch (err) {
      console.error('Error loading maintenance records:', err);
      setError('Failed to load maintenance records');
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

      if (editingRecord) {
        await maintenanceAPI.updateMaintenanceRecord(editingRecord.id, submitData);
      } else {
        await maintenanceAPI.createMaintenanceRecord(submitData);
      }

      setShowModal(false);
      setEditingRecord(null);
      resetForm();
      loadRecords();
    } catch (err) {
      console.error('Error saving maintenance record:', err);
      setError('Failed to save maintenance record');
    }
  };

  const handleEdit = record => {
    setEditingRecord(record);
    setFormData({
      vehicle_id: record.vehicle_id || '',
      maintenance_type: record.maintenance_type || '',
      title: record.title || '',
      description: record.description || '',
      cost: record.cost?.toString() || '',
      scheduled_date: record.scheduled_date
        ? new Date(record.scheduled_date).toISOString().split('T')[0]
        : '',
      date_performed: record.date_performed
        ? new Date(record.date_performed).toISOString().split('T')[0]
        : '',
      next_due_date: record.next_due_date
        ? new Date(record.next_due_date).toISOString().split('T')[0]
        : '',
      vendor_id: record.vendor_id || '',
      notes: record.notes || '',
      priority: record.priority || 'medium',
      status: record.status || 'scheduled',
    });
    setShowModal(true);
  };

  const handleDelete = async recordId => {
    if (window.confirm('Are you sure you want to delete this maintenance record?')) {
      try {
        await maintenanceAPI.deleteMaintenanceRecord(recordId);
        loadRecords();
      } catch (err) {
        console.error('Error deleting maintenance record:', err);
        setError('Failed to delete maintenance record');
      }
    }
  };

  const resetForm = () => {
    setFormData({
      vehicle_id: '',
      maintenance_type: '',
      title: '',
      description: '',
      cost: '',
      scheduled_date: new Date().toISOString().split('T')[0],
      date_performed: '',
      next_due_date: '',
      vendor_id: '',
      notes: '',
      priority: 'medium',
      status: 'scheduled',
    });
  };

  const getVehicleName = vehicleId => {
    const vehicle = vehicles.find(v => v.id === vehicleId);
    return vehicle ? `${vehicle.make} ${vehicle.model} (${vehicle.license_plate})` : vehicleId;
  };

  const getStatusBadge = status => {
    const statusConfig = {
      scheduled: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
      in_progress: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
      completed: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
      cancelled: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
    };

    return (
      <span
        className={`px-2 py-1 rounded-full text-xs ${
          statusConfig[status] || statusConfig.scheduled
        }`}
      >
        {status}
      </span>
    );
  };

  const getPriorityBadge = priority => {
    const priorityConfig = {
      low: 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200',
      medium: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
      high: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
      urgent: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
    };

    return (
      <span
        className={`px-2 py-1 rounded-full text-xs ${
          priorityConfig[priority] || priorityConfig.medium
        }`}
      >
        {priority}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header and Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <h2 className="text-xl font-semibold">Maintenance Records</h2>
        <button
          onClick={() => {
            setEditingRecord(null);
            resetForm();
            setShowModal(true);
          }}
          className="bg-primary text-primary-foreground px-4 py-2 rounded-md hover:bg-primary/90 transition"
        >
          Add New Record
        </button>
      </div>

      {/* Filters */}
      <div className="bg-card rounded-lg shadow-md p-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Filter by Vehicle</label>
            <select
              value={filters.vehicleId}
              onChange={e => setFilters(prev => ({ ...prev, vehicleId: e.target.value, page: 1 }))}
              className="w-full border border-border rounded-md px-3 py-2"
            >
              <option value="">All Vehicles</option>
              {vehicles.map((vehicle, index) => (
                <option key={vehicle.id || `filter-vehicle-${index}`} value={vehicle.id}>
                  {getVehicleName(vehicle.id)}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Filter by Status</label>
            <select
              value={filters.status}
              onChange={e => setFilters(prev => ({ ...prev, status: e.target.value, page: 1 }))}
              className="w-full border border-border rounded-md px-3 py-2"
            >
              <option value="">All Statuses</option>
              {statusOptions.map(status => (
                <option key={status} value={status}>
                  {status.replace('_', ' ').toUpperCase()}
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-end">
            <button
              onClick={() => setFilters({ vehicleId: '', status: '', page: 1, size: 20 })}
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
          <span className="ml-3">Loading maintenance records...</span>
        </div>
      ) : (
        <>
          {/* Records Table */}
          <div className="bg-card rounded-lg shadow-md overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-muted">
                  <tr>
                    <th className="text-left py-3 px-4 font-medium">Vehicle</th>
                    <th className="text-left py-3 px-4 font-medium">Type</th>
                    <th className="text-left py-3 px-4 font-medium">Date</th>
                    <th className="text-left py-3 px-4 font-medium">Cost</th>
                    <th className="text-left py-3 px-4 font-medium">Status</th>
                    <th className="text-left py-3 px-4 font-medium">Priority</th>
                    <th className="text-left py-3 px-4 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {records.length > 0 ? (
                    records.map(record => (
                      <tr key={record.id} className="border-b border-border hover:bg-accent/10">
                        <td className="py-3 px-4">{getVehicleName(record.vehicle_id)}</td>
                        <td className="py-3 px-4">
                          <div>
                            <p className="font-medium">
                              {record.maintenance_type?.replace('_', ' ')}
                            </p>
                            {record.description && (
                              <p className="text-sm text-muted-foreground">{record.description}</p>
                            )}
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          {record.date_performed
                            ? new Date(record.date_performed).toLocaleDateString()
                            : 'Not set'}
                        </td>
                        <td className="py-3 px-4">R{record.cost?.toLocaleString() || 0}</td>
                        <td className="py-3 px-4">{getStatusBadge(record.status)}</td>
                        <td className="py-3 px-4">{getPriorityBadge(record.priority)}</td>
                        <td className="py-3 px-4">
                          <div className="flex space-x-2">
                            <button
                              onClick={() => handleEdit(record)}
                              className="text-blue-600 hover:text-blue-800 text-sm"
                            >
                              Edit
                            </button>
                            <button
                              onClick={() => handleDelete(record.id)}
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
                      <td colSpan="7" className="py-8 text-center text-muted-foreground">
                        No maintenance records found
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Pagination */}
          {pagination.pages > 1 && (
            <div className="flex items-center justify-between">
              <div className="text-sm text-muted-foreground">
                Showing {(pagination.current_page - 1) * filters.size + 1} to{' '}
                {Math.min(pagination.current_page * filters.size, pagination.total)} of{' '}
                {pagination.total} records
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={() => setFilters(prev => ({ ...prev, page: prev.page - 1 }))}
                  disabled={pagination.current_page <= 1}
                  className="px-3 py-1 border border-border rounded disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Previous
                </button>
                <span className="px-3 py-1">
                  Page {pagination.current_page} of {pagination.pages}
                </span>
                <button
                  onClick={() => setFilters(prev => ({ ...prev, page: prev.page + 1 }))}
                  disabled={pagination.current_page >= pagination.pages}
                  className="px-3 py-1 border border-border rounded disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </>
      )}

      {/* Modal for Adding/Editing Records */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-900 rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4">
              {editingRecord ? 'Edit Maintenance Record' : 'Add New Maintenance Record'}
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
                    {vehicles.map((vehicle, index) => (
                      <option key={vehicle.id || `vehicle-${index}`} value={vehicle.id}>
                        {getVehicleName(vehicle.id)}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Maintenance Type *</label>
                  <select
                    value={formData.maintenance_type}
                    onChange={e =>
                      setFormData(prev => ({ ...prev, maintenance_type: e.target.value }))
                    }
                    required
                    className="w-full border border-border rounded-md px-3 py-2"
                  >
                    <option value="">Select Type</option>
                    {maintenanceTypes.map(type => (
                      <option key={type} value={type}>
                        {type.replace('_', ' ').toUpperCase()}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Title *</label>
                  <input
                    type="text"
                    value={formData.title}
                    onChange={e => setFormData(prev => ({ ...prev, title: e.target.value }))}
                    required
                    className="w-full border border-border rounded-md px-3 py-2"
                    placeholder="Enter maintenance title (e.g., Oil Change Service)"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Scheduled Date *</label>
                  <input
                    type="date"
                    value={formData.scheduled_date}
                    onChange={e =>
                      setFormData(prev => ({ ...prev, scheduled_date: e.target.value }))
                    }
                    required
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

                <div>
                  <label className="block text-sm font-medium mb-1">Date Performed</label>
                  <input
                    type="date"
                    value={formData.date_performed}
                    onChange={e =>
                      setFormData(prev => ({ ...prev, date_performed: e.target.value }))
                    }
                    className="w-full border border-border rounded-md px-3 py-2"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Next Due Date</label>
                  <input
                    type="date"
                    value={formData.next_due_date}
                    onChange={e =>
                      setFormData(prev => ({ ...prev, next_due_date: e.target.value }))
                    }
                    className="w-full border border-border rounded-md px-3 py-2"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Priority</label>
                  <select
                    value={formData.priority}
                    onChange={e => setFormData(prev => ({ ...prev, priority: e.target.value }))}
                    className="w-full border border-border rounded-md px-3 py-2"
                  >
                    {priorityOptions.map(priority => (
                      <option key={priority} value={priority}>
                        {priority.toUpperCase()}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Status</label>
                  <select
                    value={formData.status}
                    onChange={e => setFormData(prev => ({ ...prev, status: e.target.value }))}
                    className="w-full border border-border rounded-md px-3 py-2"
                  >
                    {statusOptions.map(status => (
                      <option key={status} value={status}>
                        {status.replace('_', ' ').toUpperCase()}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Description</label>
                <textarea
                  value={formData.description}
                  onChange={e => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  className="w-full border border-border rounded-md px-3 py-2"
                  rows="3"
                  placeholder="Describe the maintenance work..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Notes</label>
                <textarea
                  value={formData.notes}
                  onChange={e => setFormData(prev => ({ ...prev, notes: e.target.value }))}
                  className="w-full border border-border rounded-md px-3 py-2"
                  rows="2"
                  placeholder="Additional notes..."
                />
              </div>

              <div className="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowModal(false);
                    setEditingRecord(null);
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
                  {editingRecord ? 'Update' : 'Create'} Record
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default MaintenanceRecords;
