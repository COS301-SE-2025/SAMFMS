import React, {useState, useEffect} from 'react';
import {vehiclesAPI} from '../backend/api/vehicles';
import MaintenanceRecords from '../components/maintenance/MaintenanceRecords';
import MaintenanceSchedules from '../components/maintenance/MaintenanceSchedules';
import MaintenanceAnalytics from '../components/maintenance/MaintenanceAnalytics';
import MaintenanceDashboard from '../components/maintenance/MaintenanceDashboard';

const Maintenance = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [vehicles, setVehicles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      setLoading(true);
      // Load vehicles for dropdowns
      const vehiclesResponse = await vehiclesAPI.getVehicles();

      console.log('Vehicles API Response:', vehiclesResponse);

      // Handle nested response structure similar to Vehicles.jsx
      const vehiclesData =
        vehiclesResponse.data?.data?.vehicles ||
        vehiclesResponse.vehicles ||
        vehiclesResponse.data?.vehicles ||
        [];

      console.log('Processed vehicles data:', vehiclesData);
      console.log('First vehicle structure:', vehiclesData[0]);

      setVehicles(vehiclesData);
    } catch (err) {
      console.error('Error loading initial data:', err);
      setError('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    {id: 'dashboard', label: 'Dashboard', icon: '📊'},
    {id: 'records', label: 'Maintenance Records', icon: '🔧'},
    {id: 'schedules', label: 'Schedules', icon: '📅'},
    {id: 'analytics', label: 'Analytics', icon: '📈'},
  ];

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
          <span className="ml-3 text-lg">Loading maintenance data...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
          <h3 className="text-red-800 dark:text-red-200 font-semibold">Error Loading Data</h3>
          <p className="text-red-600 dark:text-red-400 mt-2">{error}</p>
          <button
            onClick={loadInitialData}
            className="mt-4 bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 transition"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

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
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold">Vehicle Maintenance</h1>
          <div className="text-sm text-muted-foreground">Total Vehicles: {vehicles.length}</div>
        </div>

        {/* Tab Navigation */}
        <div className="border-b border-border mb-6">
          <nav className="flex space-x-8">
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-2 px-1 border-b-2 font-medium text-sm transition ${activeTab === tab.id
                  ? 'border-primary text-primary'
                  : 'border-transparent text-muted-foreground hover:text-foreground hover:border-gray-300'
                  }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="min-h-[600px]">
          {activeTab === 'dashboard' && <MaintenanceDashboard vehicles={vehicles} />}

          {activeTab === 'records' && <MaintenanceRecords vehicles={vehicles} />}

          {activeTab === 'schedules' && <MaintenanceSchedules vehicles={vehicles} />}

          {activeTab === 'analytics' && <MaintenanceAnalytics vehicles={vehicles} />}
        </div>
      </div>
    </div>
  );
};

export default Maintenance;
