import React, {useState} from 'react';

const vehicles = [
  {id: 'VEH-001', name: 'Toyota Camry'},
  {id: 'VEH-002', name: 'Ford Transit'},
  {id: 'VEH-003', name: 'Nissan NP200'},
];

const serviceTypes = ['Oil Change', 'Brake Service', 'Tire Rotation', 'Annual Inspection'];

// Mock analytics data
const mockAnalytics = {
  costs: {
    'VEH-001': {monthly: 1200, quarterly: 3400, yearly: 13500},
    'VEH-002': {monthly: 900, quarterly: 2600, yearly: 10500},
    'VEH-003': {monthly: 700, quarterly: 2100, yearly: 8500},
  },
  faults: [
    // Each entry is for a month, for all vehicles
    {
      month: 'Jan',
      faults: {'VEH-001': 1, 'VEH-002': 0, 'VEH-003': 1},
      repairs: {'VEH-001': 1, 'VEH-002': 0, 'VEH-003': 1},
    },
    {
      month: 'Feb',
      faults: {'VEH-001': 0, 'VEH-002': 1, 'VEH-003': 0},
      repairs: {'VEH-001': 0, 'VEH-002': 1, 'VEH-003': 0},
    },
    {
      month: 'Mar',
      faults: {'VEH-001': 2, 'VEH-002': 1, 'VEH-003': 0},
      repairs: {'VEH-001': 2, 'VEH-002': 1, 'VEH-003': 0},
    },
    {
      month: 'Apr',
      faults: {'VEH-001': 0, 'VEH-002': 0, 'VEH-003': 1},
      repairs: {'VEH-001': 0, 'VEH-002': 0, 'VEH-003': 1},
    },
  ],
};

const Maintenance = () => {
  // Example scheduled maintenance data
  const [maintenanceList, setMaintenanceList] = useState([
    {
      id: 'M-2001',
      vehicle: 'VEH-001',
      serviceType: 'Oil Change',
      dueDate: '2025-06-15',
      status: 'Scheduled',
    },
    {
      id: 'M-2002',
      vehicle: 'VEH-002',
      serviceType: 'Brake Service',
      dueDate: '2025-05-25',
      status: 'In Progress',
    },
  ]);

  const [showPopup, setShowPopup] = useState(false);
  const [editIndex, setEditIndex] = useState(null);
  const [form, setForm] = useState({
    vehicle: '',
    serviceType: '',
    dueDate: '',
  });

  const handleChange = e => {
    setForm({...form, [e.target.name]: e.target.value});
  };

  // Open popup for new or edit
  const openPopup = (index = null) => {
    setEditIndex(index);
    if (index !== null) {
      // Editing: populate form with existing data
      const item = maintenanceList[index];
      setForm({
        vehicle: item.vehicle,
        serviceType: item.serviceType,
        dueDate: item.dueDate,
      });
    } else {
      // New: reset form
      setForm({vehicle: '', serviceType: '', dueDate: ''});
    }
    setShowPopup(true);
  };

  // Add or update maintenance
  const handleSubmit = e => {
    e.preventDefault();
    if (editIndex !== null) {
      // Update existing
      const updated = [...maintenanceList];
      updated[editIndex] = {
        ...updated[editIndex],
        vehicle: form.vehicle,
        serviceType: form.serviceType,
        dueDate: form.dueDate,
      };
      setMaintenanceList(updated);
    } else {
      // Add new
      setMaintenanceList([
        ...maintenanceList,
        {
          id: `M-${2000 + maintenanceList.length + 1}`,
          vehicle: form.vehicle,
          serviceType: form.serviceType,
          dueDate: form.dueDate,
          status: 'Scheduled',
        },
      ]);
    }
    setShowPopup(false);
    setEditIndex(null);
    setForm({vehicle: '', serviceType: '', dueDate: ''});
  };

  // Mocked functionality for completing maintenance
  const handleComplete = index => {
    const updated = [...maintenanceList];
    updated[index] = {
      ...updated[index],
      status: 'Completed',
    };
    setMaintenanceList(updated);
  };

  // Helper to get vehicle display name
  const getVehicleName = id => {
    const v = vehicles.find(v => v.id === id);
    return v ? `${v.name} (${v.id})` : id;
  };

  // Helper to format date
  const formatDate = dateStr => {
    const d = new Date(dateStr);
    return d.toLocaleDateString(undefined, {year: 'numeric', month: 'long', day: 'numeric'});
  };

  // Analytics helpers
  const getServiceCount = vehicleId => maintenanceList.filter(m => m.vehicle === vehicleId).length;

  // Calculate total faults and repairs for each vehicle over the last 4 months
  const getTotalFaults = vehicleId =>
    mockAnalytics.faults.reduce((sum, month) => sum + (month.faults[vehicleId] || 0), 0);

  const getTotalRepairs = vehicleId =>
    mockAnalytics.faults.reduce((sum, month) => sum + (month.repairs[vehicleId] || 0), 0);

  // Calculate grand totals for blocks
  const totalFaults = vehicles.reduce((sum, v) => sum + getTotalFaults(v.id), 0);
  const totalRepairs = vehicles.reduce((sum, v) => sum + getTotalRepairs(v.id), 0);
  const totalServices = vehicles.reduce((sum, v) => sum + getServiceCount(v.id), 0);

  return (
    <div className="relative container mx-auto px-4 py-8">
      {/* Background pattern */}
      <div
        className="absolute inset-0 z-0 opacity-10 pointer-events-none"
        style={{
          backgroundImage: 'url("/logo/logo_icon_dark.svg")',
          backgroundSize: '200px',
          backgroundRepeat: 'repeat',
          filter: 'blur(1px)',
        }}
        aria-hidden="true"
      />

      <div className="relative z-10">
        <h1 className="text-3xl font-bold mb-6">Vehicle Maintenance</h1>
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          <div className="lg:col-span-3">
            <div className="bg-card rounded-lg shadow-md p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-semibold">Maintenance Schedule</h2>
                <button
                  className="bg-primary text-primary-foreground px-4 py-2 rounded-md hover:bg-primary/90 transition"
                  onClick={() => openPopup()}
                >
                  Schedule Maintenance
                </button>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full border-collapse">
                  <thead>
                    <tr className="border-b border-border">
                      <th className="text-left py-3 px-4">ID</th>
                      <th className="text-left py-3 px-4">Vehicle</th>
                      <th className="text-left py-3 px-4">Service Type</th>
                      <th className="text-left py-3 px-4">Due Date</th>
                      <th className="text-left py-3 px-4">Status</th>
                      <th className="text-left py-3 px-4">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {maintenanceList.map((item, idx) => (
                      <tr key={item.id} className="border-b border-border hover:bg-accent/10">
                        <td className="py-3 px-4">{item.id}</td>
                        <td className="py-3 px-4">{getVehicleName(item.vehicle)}</td>
                        <td className="py-3 px-4">{item.serviceType}</td>
                        <td className="py-3 px-4">{formatDate(item.dueDate)}</td>
                        <td className="py-3 px-4">
                          {item.status === 'Scheduled' ? (
                            <span className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 py-1 px-2 rounded-full text-xs">
                              Scheduled
                            </span>
                          ) : item.status === 'In Progress' ? (
                            <span className="bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200 py-1 px-2 rounded-full text-xs">
                              In Progress
                            </span>
                          ) : (
                            <span className="bg-gray-200 text-gray-800 dark:bg-gray-700 dark:text-gray-200 py-1 px-2 rounded-full text-xs">
                              Completed
                            </span>
                          )}
                        </td>
                        <td className="py-3 px-4 space-x-2">
                          <button
                            className="text-primary hover:text-primary/80"
                            onClick={() => openPopup(idx)}
                          >
                            Edit
                          </button>
                          <button
                            className="text-blue-600 hover:text-blue-700"
                            onClick={() => handleComplete(idx)}
                            disabled={item.status === 'Completed'}
                          >
                            Complete
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
            {/* Maintenance Analytics Section */}
            <div className="bg-card rounded-lg shadow-md p-6 mt-8">
              <h2 className="text-xl font-semibold mb-4">Maintenance Analytics</h2>
              {/* Analytics summary blocks */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
                <div className="bg-gray-100 dark:bg-gray-800 rounded-lg p-4 flex flex-col items-center">
                  <span className="text-2xl font-bold text-blue-700 dark:text-blue-300">
                    {totalFaults}
                  </span>
                  <span className="text-sm text-gray-600 dark:text-gray-300">
                    Total Faults (4 months)
                  </span>
                </div>
                <div className="bg-gray-100 dark:bg-gray-800 rounded-lg p-4 flex flex-col items-center">
                  <span className="text-2xl font-bold text-green-700 dark:text-green-300">
                    {totalRepairs}
                  </span>
                  <span className="text-sm text-gray-600 dark:text-gray-300">
                    Total Repairs (4 months)
                  </span>
                </div>
                <div className="bg-gray-100 dark:bg-gray-800 rounded-lg p-4 flex flex-col items-center">
                  <span className="text-2xl font-bold text-indigo-700 dark:text-indigo-300">
                    {totalServices}
                  </span>
                  <span className="text-sm text-gray-600 dark:text-gray-300">Total Services</span>
                </div>
              </div>
              {/* Analytics Table */}
              <div className="overflow-x-auto">
                <table className="w-full text-sm border font-sans">
                  <thead>
                    <tr>
                      <th className="py-1 px-2 border font-semibold">Vehicle</th>
                      <th className="py-1 px-2 border font-semibold">Monthly Cost</th>
                      <th className="py-1 px-2 border font-semibold">Quarterly Cost</th>
                      <th className="py-1 px-2 border font-semibold">Yearly Cost</th>
                      <th className="py-1 px-2 border font-semibold"># Services</th>
                      <th className="py-1 px-2 border font-semibold">Faults (4 mo)</th>
                      <th className="py-1 px-2 border font-semibold">Repairs (4 mo)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {vehicles.map(v => (
                      <tr key={v.id}>
                        <td className="py-1 px-2 border">{getVehicleName(v.id)}</td>
                        <td className="py-1 px-2 border">
                          R{mockAnalytics.costs[v.id]?.monthly ?? '-'}
                        </td>
                        <td className="py-1 px-2 border">
                          R{mockAnalytics.costs[v.id]?.quarterly ?? '-'}
                        </td>
                        <td className="py-1 px-2 border">
                          R{mockAnalytics.costs[v.id]?.yearly ?? '-'}
                        </td>
                        <td className="py-1 px-2 border">{getServiceCount(v.id)}</td>
                        <td className="py-1 px-2 border">{getTotalFaults(v.id)}</td>
                        <td className="py-1 px-2 border">{getTotalRepairs(v.id)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
          {/* Alerts Section */}
          <div className="lg:col-span-1">
            <div className="bg-card rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold mb-4">Maintenance Alerts</h2>
              <div className="space-y-4">
                <div className="p-3 border-l-4 border-red-500 bg-red-50 dark:bg-red-950/20 rounded-r-md">
                  <p className="font-medium">Urgent: Brake Inspection</p>
                  <p className="text-sm text-muted-foreground mt-1">VEH-003: Due overdue by 2 days</p>
                </div>
                <div className="p-3 border-l-4 border-yellow-500 bg-yellow-50 dark:bg-yellow-950/20 rounded-r-md">
                  <p className="font-medium">Upcoming: Oil Change</p>
                  <p className="text-sm text-muted-foreground mt-1">VEH-001: Due in 5 days</p>
                </div>
                <div className="p-3 border-l-4 border-yellow-500 bg-yellow-50 dark:bg-yellow-950/20 rounded-r-md">
                  <p className="font-medium">Upcoming: Tire Rotation</p>
                  <p className="text-sm text-muted-foreground mt-1">VEH-002: Due in 7 days</p>
                </div>
                <div className="p-3 border-l-4 border-blue-500 bg-blue-50 dark:bg-blue-950/20 rounded-r-md">
                  <p className="font-medium">Reminder: Annual Inspection</p>
                  <p className="text-sm text-muted-foreground mt-1">VEH-001: Due in 30 days</p>
                </div>
              </div>
            </div>
          </div>
        </div>
        {/* Popup for scheduling/editing maintenance */}
        {showPopup && (
          <div className="fixed inset-0 bg-black bg-opacity-30 flex items-center justify-center z-50">
            <div className="bg-white dark:bg-gray-900 rounded-lg p-6 w-full max-w-md shadow-lg">
              <h3 className="text-lg font-semibold mb-4">
                {editIndex !== null ? 'Edit Maintenance' : 'Schedule Maintenance'}
              </h3>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block font-medium mb-1">Vehicle</label>
                  <select
                    name="vehicle"
                    value={form.vehicle}
                    onChange={handleChange}
                    required
                    className="w-full border rounded p-2"
                  >
                    <option value="">Select vehicle</option>
                    {vehicles.map(v => (
                      <option key={v.id} value={v.id}>
                        {v.name} ({v.id})
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block font-medium mb-1">Service Type</label>
                  <select
                    name="serviceType"
                    value={form.serviceType}
                    onChange={handleChange}
                    required
                    className="w-full border rounded p-2"
                  >
                    <option value="">Select service</option>
                    {serviceTypes.map(type => (
                      <option key={type} value={type}>
                        {type}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block font-medium mb-1">Due Date</label>
                  <input
                    type="date"
                    name="dueDate"
                    value={form.dueDate}
                    onChange={handleChange}
                    required
                    className="w-full border rounded p-2"
                  />
                </div>
                <div className="flex justify-end space-x-2">
                  <button
                    type="button"
                    className="px-4 py-2 rounded bg-gray-200 dark:bg-gray-700"
                    onClick={() => {
                      setShowPopup(false);
                      setEditIndex(null);
                    }}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 rounded bg-primary text-primary-foreground"
                  >
                    {editIndex !== null ? 'Save' : 'Schedule'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Maintenance;
