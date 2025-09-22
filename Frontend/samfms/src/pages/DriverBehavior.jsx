import React, { useState, useEffect } from 'react';
import DriverBehaviorDashboard from '../components/driver-behavior/DriverBehaviorDashboard';
import DriverBehaviorDrivers from '../components/driver-behavior/DriverBehaviorDrivers';
import DriverBehaviorAnalytics from '../components/driver-behavior/DriverBehaviorAnalytics';

const DriverBehavior = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [driverData, setDriverData] = useState([]);

  useEffect(() => {
    // Load initial driver behavior data (mock for now)
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      setLoading(true);
      // Mock data - in a real implementation this would fetch from API
      const mockDriverData = [
        {
          id: 1,
          name: 'John Smith',
          employeeId: 'EMP001',
          overallScore: 8.5,
          speedingEvents: 2,
          harshBraking: 1,
          rapidAcceleration: 0,
          distraction: 3
        },
        {
          id: 2,
          name: 'Sarah Johnson',
          employeeId: 'EMP002',
          overallScore: 9.2,
          speedingEvents: 0,
          harshBraking: 0,
          rapidAcceleration: 1,
          distraction: 1
        },
        {
          id: 3,
          name: 'Mike Wilson',
          employeeId: 'EMP003',
          overallScore: 7.1,
          speedingEvents: 5,
          harshBraking: 3,
          rapidAcceleration: 2,
          distraction: 4
        }
      ];
      
      setDriverData(mockDriverData);
    } catch (err) {
      console.error('Error loading driver behavior data:', err);
      setError('Failed to load driver behavior data');
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: '📊' },
    { id: 'drivers', label: 'Drivers', icon: '👥' },
    { id: 'analytics', label: 'Analytics', icon: '📈' },
  ];

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
          <span className="ml-3 text-lg">Loading driver behavior data...</span>
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
          <h1 className="text-3xl font-bold">Driver Behavior Monitoring</h1>
          <div className="text-sm text-muted-foreground">
            Total Drivers: {driverData.length}
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="border-b border-border mb-6">
          <nav className="flex space-x-8">
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-2 px-1 border-b-2 font-medium text-sm transition ${
                  activeTab === tab.id
                    ? 'border-primary text-primary'
                    : 'border-transparent text-muted-foreground hover:text-foreground hover:border-gray-300'
                }`}
              >
                <span className="mr-2">{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="min-h-[600px]">
          {activeTab === 'dashboard' && <DriverBehaviorDashboard driverData={driverData} />}
          {activeTab === 'drivers' && <DriverBehaviorDrivers driverData={driverData} />}
          {activeTab === 'analytics' && <DriverBehaviorAnalytics driverData={driverData} />}
        </div>
      </div>
    </div>
  );
};

export default DriverBehavior;