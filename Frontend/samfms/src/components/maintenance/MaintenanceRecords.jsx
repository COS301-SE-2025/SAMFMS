import React, { useState, useEffect } from 'react';
import { Plus, ChevronLeft, ChevronRight } from 'lucide-react';
import { maintenanceAPI } from '../../backend/api/maintenance';
import { getVehicle } from '../../backend/api/vehicles';

// Component to display vehicle details with direct API calls
const VehicleDetailDisplay = ({ vehicleId, fetchVehicleDetails }) => {
  const [vehicleDetails, setVehicleDetails] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    const loadVehicleDetails = async () => {
      if (!vehicleId) {
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(false);
        const details = await fetchVehicleDetails(vehicleId);
        setVehicleDetails(details);
      } catch (err) {
        console.error(`Failed to load vehicle details for ${vehicleId}:`, err);
        setError(true);
      } finally {
        setLoading(false);
      }
    };

    loadVehicleDetails();
  }, [vehicleId, fetchVehicleDetails]);

  if (loading) {
    return (
      <div className="text-sm">
        <div className="flex items-center gap-2">
          <div className="animate-spin w-3 h-3 border border-border rounded-full border-t-transparent"></div>
          <span className="text-muted-foreground">Loading...</span>
        </div>
      </div>
    );
  }

  if (error || !vehicleDetails) {
    return (
      <div className="text-sm">
        <div className="text-muted-foreground">Vehicle {vehicleId.slice(-6)}</div>
        <div className="text-xs text-muted-foreground">Details unavailable</div>
      </div>
    );
  }

  return (
    <div className="text-sm">
      <div className="font-medium">
        {vehicleDetails.year && `${vehicleDetails.year} `}
        {vehicleDetails.make && `${vehicleDetails.make} `}
        {vehicleDetails.model || 'Vehicle'}
      </div>
      {vehicleDetails.license_plate && (
        <div className="text-xs text-muted-foreground">{vehicleDetails.license_plate}</div>
      )}
    </div>
  );
};

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
    size: 5,
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

  // Debug vehicles prop
  useEffect(() => {
    console.log('MaintenanceRecords: Vehicles prop updated:', {
      count: vehicles?.length,
      sampleVehicle: vehicles?.[0],
      vehicleIds: vehicles?.slice(0, 3).map(v => ({ id: v.id, _id: v._id })),
    });
  }, [vehicles]);

  const loadRecords = async () => {
    try {
      setLoading(true);
      setError(null);

      // Calculate skip for pagination
      const skip = (filters.page - 1) * filters.size;

      // Build query parameters matching the API
      const params = {
        skip,
        limit: filters.size,
      };

      // Only add vehicle_id if it exists and is valid
      if (filters.vehicleId && filters.vehicleId.trim()) {
        params.vehicle_id = filters.vehicleId.trim();
      }

      if (filters.status && filters.status.trim()) {
        params.status = filters.status.trim();
      }

      console.log('API Request Parameters:', params);
      console.log('Final API URL will be constructed with:', JSON.stringify(params, null, 2));

      // Call the API with individual parameters instead of an object
      const vehicleIdParam =
        filters.vehicleId && filters.vehicleId.trim() ? filters.vehicleId.trim() : null;
      const statusParam = filters.status && filters.status.trim() ? filters.status.trim() : null;

      console.log('Calling maintenanceAPI.getMaintenanceRecords with parameters:');
      console.log('- vehicleIdParam:', vehicleIdParam, '(type:', typeof vehicleIdParam, ')');
      console.log('- statusParam:', statusParam, '(type:', typeof statusParam, ')');
      console.log('- page:', filters.page);
      console.log('- size:', filters.size);

      const response = await maintenanceAPI.getMaintenanceRecords(
        vehicleIdParam,
        statusParam,
        filters.page,
        filters.size
      );

      console.log('Maintenance Records API Response:', response);

      // Handle the nested response structure from your API
      const outerData = response.data?.data || response.data || {};
      const innerData = outerData.data || outerData;
      const records = innerData.maintenance_records || innerData.records || innerData || [];

      console.log('Extracted records:', records);
      console.log('Total from API:', innerData.total);

      setRecords(records);
      setPagination({
        total: innerData.total || 0,
        pages: Math.ceil((innerData.total || 0) / filters.size),
        current_page: filters.page || 1,
        has_more: innerData.has_more || false,
      });
    } catch (err) {
      console.error('Error loading maintenance records:', err);
      setError('Failed to load maintenance records. Please try again.');
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

  // Fetch vehicle details directly from the management API
  const fetchVehicleDetails = async vehicleId => {
    const vehicleIdStr = vehicleId.toString();

    if (!vehicleId) {
      return null;
    }

    try {
      console.log(`Fetching vehicle details for ID: ${vehicleIdStr}`);
      const response = await getVehicle(vehicleIdStr);

      console.log(`Vehicle API Response for ${vehicleIdStr}:`, response);

      if (response.data && response.data.data) {
        // Handle nested response structure: response.data.data contains the actual vehicle details
        const vehicleDetails = response.data.data;
        console.log(`Extracted vehicle details for ${vehicleIdStr}:`, vehicleDetails);
        return vehicleDetails;
      } else {
        console.warn(`No vehicle details found for ${vehicleIdStr}`);
        return null;
      }
    } catch (error) {
      console.error(`Failed to fetch vehicle details for ${vehicleIdStr}:`, error);
      return null;
    }
  };

  const getVehicleName = vehicleId => {
    if (!vehicleId) return 'Unknown Vehicle';

    // Handle both string and ObjectId formats
    const vehicleIdStr = vehicleId.toString();

    // Fallback to the provided vehicles prop for immediate display
    let vehicle = vehicles?.find(v => v.id?.toString() === vehicleIdStr);
    if (!vehicle) {
      vehicle = vehicles?.find(v => v._id?.toString() === vehicleIdStr);
    }

    if (vehicle) {
      return formatVehicleDisplay(vehicle);
    }

    // If no vehicle found, return truncated ID for readability
    return `Vehicle ${
      vehicleIdStr.length > 8 ? vehicleIdStr.substring(0, 8) + '...' : vehicleIdStr
    }`;
  };

  const formatVehicleDisplay = vehicle => {
    if (!vehicle) return 'Unknown Vehicle';

    const parts = [];

    // Add year if available
    if (vehicle.year) parts.push(vehicle.year);

    // Add make and model
    if (vehicle.make) parts.push(vehicle.make);
    if (vehicle.model) parts.push(vehicle.model);

    // If no make/model, show a generic vehicle name
    if (parts.length === 0 || (parts.length === 1 && vehicle.year)) {
      parts.push('Vehicle');
    }

    const vehicleInfo = parts.join(' ');
    const licensePlate = vehicle.license_plate || vehicle.vin;

    return licensePlate ? `${vehicleInfo} (${licensePlate})` : vehicleInfo;
  };

  const getVehicleDisplay = vehicleId => {
    if (!vehicleId) return 'Unknown Vehicle';

    const vehicleIdStr = vehicleId.toString();

    // Check if we have this vehicle in the fallback data first
    const fallbackVehicle = vehicles?.find(v => {
      const vId = v.id?.toString() || v._id?.toString();
      return vId === vehicleIdStr;
    });

    if (fallbackVehicle) {
      console.log(`Using fallback vehicle for ${vehicleIdStr}:`, fallbackVehicle);
      return (
        <div className="text-sm">
          <div className="font-medium">
            {fallbackVehicle.year && `${fallbackVehicle.year} `}
            {fallbackVehicle.make && `${fallbackVehicle.make} `}
            {fallbackVehicle.model || 'Vehicle'}
          </div>
          {fallbackVehicle.license_plate && (
            <div className="text-xs text-muted-foreground">{fallbackVehicle.license_plate}</div>
          )}
        </div>
      );
    }

    // Return a component that will fetch and display vehicle details
    return (
      <VehicleDetailDisplay vehicleId={vehicleIdStr} fetchVehicleDetails={fetchVehicleDetails} />
    );
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
          className="bg-green-600 text-white p-3 rounded-md hover:bg-green-700 transition-colors"
          title="Add New Record"
        >
          <Plus size={20} />
        </button>
      </div>

      {/* Filters */}
      <div className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 rounded-lg shadow-md p-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Filter by Vehicle</label>
            <select
              value={filters.vehicleId}
              onChange={e => {
                const selectedValue = e.target.value;
                console.log(
                  'Vehicle filter changed to:',
                  selectedValue,
                  '(type:',
                  typeof selectedValue,
                  ')'
                );
                setFilters(prev => ({ ...prev, vehicleId: selectedValue, page: 1 }));
              }}
              className="w-full border border-border rounded-md px-3 py-2"
            >
              <option value="">All Vehicles</option>
              {vehicles && vehicles.length > 0 ? (
                vehicles.map((vehicle, index) => {
                  // More robust vehicle ID extraction
                  let vehicleIdStr = '';

                  if (vehicle.id) {
                    if (typeof vehicle.id === 'string') {
                      vehicleIdStr = vehicle.id;
                    } else if (vehicle.id.$oid) {
                      vehicleIdStr = vehicle.id.$oid;
                    } else {
                      vehicleIdStr = String(vehicle.id);
                    }
                  } else if (vehicle._id) {
                    if (typeof vehicle._id === 'string') {
                      vehicleIdStr = vehicle._id;
                    } else if (vehicle._id.$oid) {
                      vehicleIdStr = vehicle._id.$oid;
                    } else {
                      vehicleIdStr = String(vehicle._id);
                    }
                  } else {
                    vehicleIdStr = `vehicle-${index}`;
                  }

                  console.log(`Vehicle ${index}:`, {
                    original: vehicle,
                    extractedId: vehicleIdStr,
                    idType: typeof vehicleIdStr,
                  });

                  return (
                    <option key={vehicleIdStr} value={vehicleIdStr}>
                      {getVehicleName(vehicle.id || vehicle._id)}
                    </option>
                  );
                })
              ) : (
                <option disabled>No vehicles available</option>
              )}
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
              onClick={() => setFilters({ vehicleId: '', status: '', page: 1, size: 5 })}
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
          {/* Records Table - matching vehicles page structure */}
          <div className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 rounded-lg shadow-md p-6 border border-border">
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="border-b border-border">
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
                        <td className="py-3 px-4">
                          <div className="min-w-0">{getVehicleDisplay(record.vehicle_id)}</div>
                        </td>
                        <td className="py-3 px-4">
                          <div>
                            <p className="font-medium">
                              {record.title ||
                                record.maintenance_type?.replace('_', ' ') ||
                                'Unknown Type'}
                            </p>
                            {record.description && (
                              <p
                                className="text-sm text-muted-foreground truncate max-w-xs"
                                title={record.description}
                              >
                                {record.description}
                              </p>
                            )}
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <div>
                            <p className="text-sm">
                              <span className="font-medium">Scheduled:</span>{' '}
                              {record.scheduled_date
                                ? new Date(record.scheduled_date).toLocaleDateString()
                                : 'Not set'}
                            </p>
                            {record.completed_date && (
                              <p className="text-sm text-muted-foreground">
                                <span className="font-medium">Completed:</span>{' '}
                                {new Date(record.completed_date).toLocaleDateString()}
                              </p>
                            )}
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <div>
                            {record.actual_cost && (
                              <p className="font-medium">R{record.actual_cost?.toLocaleString()}</p>
                            )}
                            {record.estimated_cost && (
                              <p className="text-sm text-muted-foreground">
                                Est: R{record.estimated_cost?.toLocaleString()}
                              </p>
                            )}
                            {!record.actual_cost && !record.estimated_cost && (
                              <span className="text-muted-foreground">-</span>
                            )}
                          </div>
                        </td>
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

            {/* Pagination - Enhanced */}
            {pagination.total > 0 && (
              <div className="mt-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div className="flex items-center gap-4">
                  <select
                    value={filters.size}
                    onChange={e =>
                      setFilters(prev => ({ ...prev, size: Number(e.target.value), page: 1 }))
                    }
                    className="border border-border rounded-md bg-background py-1 pl-2 pr-8"
                  >
                    <option value="5">5 per page</option>
                    <option value="10">10 per page</option>
                    <option value="20">20 per page</option>
                    <option value="50">50 per page</option>
                  </select>
                  <div className="text-sm text-muted-foreground">
                    Showing {(filters.page - 1) * filters.size + 1} to{' '}
                    {Math.min(filters.page * filters.size, pagination.total)} of {pagination.total}{' '}
                    records
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-muted-foreground">
                    Page {pagination.current_page} of {pagination.pages}
                  </span>
                  <div className="flex gap-1">
                    <button
                      onClick={() => setFilters(prev => ({ ...prev, page: 1 }))}
                      disabled={pagination.current_page <= 1}
                      className={`px-2 py-1 rounded text-sm ${
                        pagination.current_page <= 1
                          ? 'text-muted-foreground cursor-not-allowed'
                          : 'hover:bg-accent'
                      }`}
                      title="First page"
                    >
                      First
                    </button>
                    <button
                      onClick={() => setFilters(prev => ({ ...prev, page: prev.page - 1 }))}
                      disabled={pagination.current_page <= 1}
                      className={`p-1 rounded ${
                        pagination.current_page <= 1
                          ? 'text-muted-foreground cursor-not-allowed'
                          : 'hover:bg-accent'
                      }`}
                      title="Previous page"
                    >
                      <ChevronLeft size={18} />
                    </button>
                    <button
                      onClick={() => setFilters(prev => ({ ...prev, page: prev.page + 1 }))}
                      disabled={pagination.current_page >= pagination.pages}
                      className={`p-1 rounded ${
                        pagination.current_page >= pagination.pages
                          ? 'text-muted-foreground cursor-not-allowed'
                          : 'hover:bg-accent'
                      }`}
                      title="Next page"
                    >
                      <ChevronRight size={18} />
                    </button>
                    <button
                      onClick={() => setFilters(prev => ({ ...prev, page: pagination.pages }))}
                      disabled={pagination.current_page >= pagination.pages}
                      className={`px-2 py-1 rounded text-sm ${
                        pagination.current_page >= pagination.pages
                          ? 'text-muted-foreground cursor-not-allowed'
                          : 'hover:bg-accent'
                      }`}
                      title="Last page"
                    >
                      Last
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
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
                    {vehicles && vehicles.length > 0 ? (
                      vehicles.map((vehicle, index) => {
                        // More robust vehicle ID extraction
                        let vehicleIdStr = '';

                        if (vehicle.id) {
                          if (typeof vehicle.id === 'string') {
                            vehicleIdStr = vehicle.id;
                          } else if (vehicle.id.$oid) {
                            vehicleIdStr = vehicle.id.$oid;
                          } else {
                            vehicleIdStr = String(vehicle.id);
                          }
                        } else if (vehicle._id) {
                          if (typeof vehicle._id === 'string') {
                            vehicleIdStr = vehicle._id;
                          } else if (vehicle._id.$oid) {
                            vehicleIdStr = vehicle._id.$oid;
                          } else {
                            vehicleIdStr = String(vehicle._id);
                          }
                        } else {
                          vehicleIdStr = `vehicle-${index}`;
                        }

                        return (
                          <option key={vehicleIdStr} value={vehicleIdStr}>
                            {getVehicleName(vehicle.id || vehicle._id)}
                          </option>
                        );
                      })
                    ) : (
                      <option disabled>No vehicles available</option>
                    )}
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
