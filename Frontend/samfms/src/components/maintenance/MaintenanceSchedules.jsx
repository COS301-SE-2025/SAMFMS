import React, { useState, useEffect } from 'react';
import { Plus, ChevronLeft, ChevronRight } from 'lucide-react';
import { maintenanceAPI } from '../../backend/api/maintenance';

const MaintenanceSchedules = ({ vehicles }) => {
  const [schedules, setSchedules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [editingSchedule, setEditingSchedule] = useState(null);
  const [filters, setFilters] = useState({
    vehicleId: '',
  });

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);

  // Calculate pagination
  const indexOfLastItem = currentPage * itemsPerPage;
  const indexOfFirstItem = indexOfLastItem - itemsPerPage;
  const currentSchedules = schedules.slice(indexOfFirstItem, indexOfLastItem);
  const totalPages = Math.ceil(schedules.length / itemsPerPage);

  // Pagination functions
  const goToNextPage = () => {
    setCurrentPage(prev => Math.min(prev + 1, totalPages));
  };

  const goToPrevPage = () => {
    setCurrentPage(prev => Math.max(prev - 1, 1));
  };

  const changeItemsPerPage = e => {
    setItemsPerPage(Number(e.target.value));
    setCurrentPage(1);
  };

  const [formData, setFormData] = useState({
    vehicle_id: '',
    maintenance_type: '',
    title: '', // Required field for schedule creation
    description: '',
    scheduled_date: new Date().toISOString().split('T')[0], // Required field
    interval_type: 'mileage',
    interval_value: '',
    last_service_date: '',
    last_service_mileage: '',
    next_due_date: '',
    next_due_mileage: '',
    is_active: true,
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

  const intervalTypes = ['mileage', 'time', 'both'];

  useEffect(() => {
    loadSchedules();
  }, [filters]); // eslint-disable-line react-hooks/exhaustive-deps

  const loadSchedules = async () => {
    try {
      setLoading(true);
      const response = await maintenanceAPI.getMaintenanceSchedules(filters.vehicleId || null);

      // Handle nested data structure from backend
      const data = response.data?.data || response.data || {};
      const schedules = data.schedules || data || [];

      setSchedules(schedules);
    } catch (err) {
      console.error('Error loading maintenance schedules:', err);
      setError('Failed to load maintenance schedules');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async e => {
    e.preventDefault();
    try {
      const submitData = {
        ...formData,
        interval_value: parseInt(formData.interval_value) || 0,
        last_service_mileage: parseInt(formData.last_service_mileage) || 0,
        next_due_mileage: parseInt(formData.next_due_mileage) || 0,
      };

      if (editingSchedule) {
        await maintenanceAPI.updateMaintenanceSchedule(editingSchedule.id, submitData);
      } else {
        await maintenanceAPI.createMaintenanceSchedule(submitData);
      }

      setShowModal(false);
      setEditingSchedule(null);
      resetForm();
      loadSchedules();
    } catch (err) {
      console.error('Error saving maintenance schedule:', err);
      setError('Failed to save maintenance schedule');
    }
  };

  const handleEdit = schedule => {
    setEditingSchedule(schedule);
    setFormData({
      vehicle_id: schedule.vehicle_id || '',
      maintenance_type: schedule.maintenance_type || '',
      title: schedule.title || '',
      description: schedule.description || '',
      scheduled_date: schedule.scheduled_date
        ? new Date(schedule.scheduled_date).toISOString().split('T')[0]
        : new Date().toISOString().split('T')[0],
      interval_type: schedule.interval_type || 'mileage',
      interval_value: schedule.interval_value?.toString() || '',
      last_service_date: schedule.last_service_date
        ? new Date(schedule.last_service_date).toISOString().split('T')[0]
        : '',
      last_service_mileage: schedule.last_service_mileage?.toString() || '',
      next_due_date: schedule.next_due_date
        ? new Date(schedule.next_due_date).toISOString().split('T')[0]
        : '',
      next_due_mileage: schedule.next_due_mileage?.toString() || '',
      is_active: schedule.is_active !== false,
    });
    setShowModal(true);
  };

  const handleDelete = async scheduleId => {
    if (window.confirm('Are you sure you want to delete this maintenance schedule?')) {
      try {
        await maintenanceAPI.deleteMaintenanceSchedule(scheduleId);
        loadSchedules();
      } catch (err) {
        console.error('Error deleting maintenance schedule:', err);
        setError('Failed to delete maintenance schedule');
      }
    }
  };

  const resetForm = () => {
    setFormData({
      vehicle_id: '',
      maintenance_type: '',
      title: '',
      description: '',
      scheduled_date: new Date().toISOString().split('T')[0],
      interval_type: 'mileage',
      interval_value: '',
      last_service_date: '',
      last_service_mileage: '',
      next_due_date: '',
      next_due_mileage: '',
      is_active: true,
    });
  };

  const getVehicleName = vehicleId => {
    const vehicle = vehicles.find(v => v.id === vehicleId);
    return vehicle ? `${vehicle.make} ${vehicle.model} (${vehicle.license_plate})` : vehicleId;
  };

  const getStatusIndicator = schedule => {
    const now = new Date();
    const nextDueDate = schedule.next_due_date ? new Date(schedule.next_due_date) : null;
    const daysUntilDue = nextDueDate
      ? Math.ceil((nextDueDate - now) / (1000 * 60 * 60 * 24))
      : null;

    if (!schedule.is_active) {
      return (
        <span className="px-2 py-1 rounded-full text-xs bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200">
          Inactive
        </span>
      );
    }

    if (daysUntilDue !== null) {
      if (daysUntilDue < 0) {
        return (
          <span className="px-2 py-1 rounded-full text-xs bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">
            Overdue
          </span>
        );
      } else if (daysUntilDue <= 7) {
        return (
          <span className="px-2 py-1 rounded-full text-xs bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200">
            Due Soon
          </span>
        );
      } else if (daysUntilDue <= 30) {
        return (
          <span className="px-2 py-1 rounded-full text-xs bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
            Upcoming
          </span>
        );
      }
    }

    return (
      <span className="px-2 py-1 rounded-full text-xs bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
        Active
      </span>
    );
  };

  const calculateNextDueDate = () => {
    if (
      formData.last_service_date &&
      formData.interval_value &&
      formData.interval_type === 'time'
    ) {
      const lastDate = new Date(formData.last_service_date);
      const intervalDays = parseInt(formData.interval_value);
      const nextDate = new Date(lastDate.getTime() + intervalDays * 24 * 60 * 60 * 1000);
      return nextDate.toISOString().split('T')[0];
    }
    return '';
  };

  const calculateNextDueMileage = () => {
    if (
      formData.last_service_mileage &&
      formData.interval_value &&
      formData.interval_type === 'mileage'
    ) {
      const lastMileage = parseInt(formData.last_service_mileage);
      const intervalMileage = parseInt(formData.interval_value);
      return (lastMileage + intervalMileage).toString();
    }
    return '';
  };

  // Auto-calculate next due when relevant fields change
  useEffect(() => {
    if (
      formData.interval_type === 'time' &&
      formData.last_service_date &&
      formData.interval_value
    ) {
      const nextDate = calculateNextDueDate();
      if (nextDate && nextDate !== formData.next_due_date) {
        setFormData(prev => ({ ...prev, next_due_date: nextDate }));
      }
    }
  }, [formData.last_service_date, formData.interval_value, formData.interval_type]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (
      formData.interval_type === 'mileage' &&
      formData.last_service_mileage &&
      formData.interval_value
    ) {
      const nextMileage = calculateNextDueMileage();
      if (nextMileage && nextMileage !== formData.next_due_mileage) {
        setFormData(prev => ({ ...prev, next_due_mileage: nextMileage }));
      }
    }
  }, [formData.last_service_mileage, formData.interval_value, formData.interval_type]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="space-y-6">
      {/* Header and Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <h2 className="text-xl font-semibold">Maintenance Schedules</h2>
        <button
          onClick={() => {
            setEditingSchedule(null);
            resetForm();
            setShowModal(true);
          }}
          className="bg-green-600 text-white p-3 rounded-md hover:bg-green-700 transition-colors"
          title="Create New Schedule"
        >
          <Plus size={20} />
        </button>
      </div>

      {/* Filters */}
      <div className="bg-card rounded-lg shadow-md p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Filter by Vehicle</label>
            <select
              value={filters.vehicleId}
              onChange={e => setFilters(prev => ({ ...prev, vehicleId: e.target.value }))}
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
          <div className="flex items-end">
            <button
              onClick={() => setFilters({ vehicleId: '' })}
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
          <span className="ml-3">Loading maintenance schedules...</span>
        </div>
      ) : (
        <div className="bg-card rounded-lg shadow-md p-6 border border-border">
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left py-3 px-4 font-medium">Vehicle</th>
                  <th className="text-left py-3 px-4 font-medium">Maintenance Type</th>
                  <th className="text-left py-3 px-4 font-medium">Interval</th>
                  <th className="text-left py-3 px-4 font-medium">Last Service</th>
                  <th className="text-left py-3 px-4 font-medium">Next Due</th>
                  <th className="text-left py-3 px-4 font-medium">Status</th>
                  <th className="text-left py-3 px-4 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {currentSchedules.length > 0 ? (
                  currentSchedules.map(schedule => (
                    <tr key={schedule.id} className="border-b border-border hover:bg-accent/10">
                      <td className="py-3 px-4">{getVehicleName(schedule.vehicle_id)}</td>
                      <td className="py-3 px-4">
                        <div>
                          <p className="font-medium">
                            {schedule.maintenance_type?.replace('_', ' ')}
                          </p>
                          {schedule.description && (
                            <p className="text-sm text-muted-foreground">{schedule.description}</p>
                          )}
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <div className="text-sm">
                          <p>
                            Every {schedule.interval_value}{' '}
                            {schedule.interval_type === 'mileage' ? 'km' : 'days'}
                          </p>
                          <p className="text-muted-foreground">({schedule.interval_type})</p>
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <div className="text-sm">
                          {schedule.last_service_date && (
                            <p>{new Date(schedule.last_service_date).toLocaleDateString()}</p>
                          )}
                          {schedule.last_service_mileage && (
                            <p className="text-muted-foreground">
                              {schedule.last_service_mileage.toLocaleString()} km
                            </p>
                          )}
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <div className="text-sm">
                          {schedule.next_due_date && (
                            <p>{new Date(schedule.next_due_date).toLocaleDateString()}</p>
                          )}
                          {schedule.next_due_mileage && (
                            <p className="text-muted-foreground">
                              {schedule.next_due_mileage.toLocaleString()} km
                            </p>
                          )}
                        </div>
                      </td>
                      <td className="py-3 px-4">{getStatusIndicator(schedule)}</td>
                      <td className="py-3 px-4">
                        <div className="flex space-x-2">
                          <button
                            onClick={() => handleEdit(schedule)}
                            className="text-blue-600 hover:text-blue-800 text-sm"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => handleDelete(schedule.id)}
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
                      No maintenance schedules found
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Pagination - matching vehicles page style */}
      {totalPages > 1 && (
        <div className="mt-6 flex items-center justify-between">
          <div>
            <select
              value={itemsPerPage}
              onChange={changeItemsPerPage}
              className="border border-border rounded-md bg-background py-1 pl-2 pr-8"
            >
              <option value="5">5 per page</option>
              <option value="10">10 per page</option>
              <option value="20">20 per page</option>
              <option value="50">50 per page</option>
            </select>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">
              Page {currentPage} of {totalPages}
            </span>
            <div className="flex gap-1">
              <button
                onClick={goToPrevPage}
                disabled={currentPage === 1}
                className={`p-1 rounded ${
                  currentPage === 1 ? 'text-muted-foreground cursor-not-allowed' : 'hover:bg-accent'
                }`}
                title="Previous page"
              >
                <ChevronLeft size={18} />
              </button>
              <button
                onClick={goToNextPage}
                disabled={currentPage === totalPages}
                className={`p-1 rounded ${
                  currentPage === totalPages
                    ? 'text-muted-foreground cursor-not-allowed'
                    : 'hover:bg-accent'
                }`}
                title="Next page"
              >
                <ChevronRight size={18} />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal for Adding/Editing Schedules */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-900 rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4">
              {editingSchedule ? 'Edit Maintenance Schedule' : 'Create New Maintenance Schedule'}
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
                    placeholder="Enter schedule title (e.g., Oil Change Schedule)"
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
                  <label className="block text-sm font-medium mb-1">Interval Type *</label>
                  <select
                    value={formData.interval_type}
                    onChange={e =>
                      setFormData(prev => ({ ...prev, interval_type: e.target.value }))
                    }
                    required
                    className="w-full border border-border rounded-md px-3 py-2"
                  >
                    {intervalTypes.map(type => (
                      <option key={type} value={type}>
                        {type.toUpperCase()}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">
                    Interval Value * ({formData.interval_type === 'mileage' ? 'km' : 'days'})
                  </label>
                  <input
                    type="number"
                    value={formData.interval_value}
                    onChange={e =>
                      setFormData(prev => ({ ...prev, interval_value: e.target.value }))
                    }
                    required
                    className="w-full border border-border rounded-md px-3 py-2"
                    placeholder={formData.interval_type === 'mileage' ? 'e.g., 10000' : 'e.g., 90'}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Last Service Date</label>
                  <input
                    type="date"
                    value={formData.last_service_date}
                    onChange={e =>
                      setFormData(prev => ({ ...prev, last_service_date: e.target.value }))
                    }
                    className="w-full border border-border rounded-md px-3 py-2"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">
                    Last Service Mileage (km)
                  </label>
                  <input
                    type="number"
                    value={formData.last_service_mileage}
                    onChange={e =>
                      setFormData(prev => ({ ...prev, last_service_mileage: e.target.value }))
                    }
                    className="w-full border border-border rounded-md px-3 py-2"
                    placeholder="e.g., 50000"
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
                  <label className="block text-sm font-medium mb-1">Next Due Mileage (km)</label>
                  <input
                    type="number"
                    value={formData.next_due_mileage}
                    onChange={e =>
                      setFormData(prev => ({ ...prev, next_due_mileage: e.target.value }))
                    }
                    className="w-full border border-border rounded-md px-3 py-2"
                    placeholder="e.g., 60000"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Description</label>
                <textarea
                  value={formData.description}
                  onChange={e => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  className="w-full border border-border rounded-md px-3 py-2"
                  rows="3"
                  placeholder="Describe the scheduled maintenance..."
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
                  Active Schedule
                </label>
              </div>

              <div className="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowModal(false);
                    setEditingSchedule(null);
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
                  {editingSchedule ? 'Update' : 'Create'} Schedule
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default MaintenanceSchedules;
