import React, { useState, useCallback } from 'react';
import DriverBehaviorDashboard from '../components/driver-behavior/DriverBehaviorDashboard';
import DriverBehaviorDrivers from '../components/driver-behavior/DriverBehaviorDrivers';
import DriverBehaviorAnalytics from '../components/driver-behavior/DriverBehaviorAnalytics';

const DriverBehavior = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [driverData, setDriverData] = useState([]);

  // Handle data updates from child components - memoized to prevent infinite re-renders
  const handleDataUpdate = useCallback((newDriverData) => {
    setDriverData(newDriverData || []);
  }, []);

  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: '📊' },
    { id: 'drivers', label: 'Drivers', icon: '👥' },
    { id: 'analytics', label: 'Analytics', icon: '📈' },
  ];

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
            Total Drivers: {driverData.length || 'Loading...'}
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
          {activeTab === 'dashboard' && <DriverBehaviorDashboard onDataUpdate={handleDataUpdate} />}
          {activeTab === 'drivers' && <DriverBehaviorDrivers onDataUpdate={handleDataUpdate} />}
          {activeTab === 'analytics' && <DriverBehaviorAnalytics driverData={driverData} />}
        </div>
      </div>
    </div>
  );
};

export default DriverBehavior;