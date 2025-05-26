import React from 'react';
import { Users, Car, AlertCircle, CheckCircle } from 'lucide-react';

const DataVisualization = () => {
  // In a real app, this data would come from props or API calls
  const stats = [
    {
      title: 'Active Drivers',
      value: 24,
      change: '+2',
      icon: <Users size={20} className="text-primary" />,
      color: 'bg-primary-50 dark:bg-primary-950',
    },
    {
      title: 'Assigned Vehicles',
      value: 18,
      change: '+3',
      icon: <Car size={20} className="text-blue-600" />,
      color: 'bg-blue-50 dark:bg-blue-950',
    },
    {
      title: 'License Expiring Soon',
      value: 4,
      change: '-1',
      icon: <AlertCircle size={20} className="text-amber-600" />,
      color: 'bg-amber-50 dark:bg-amber-950',
    },
    {
      title: 'Completed Trainings',
      value: 56,
      change: '+8',
      icon: <CheckCircle size={20} className="text-green-600" />,
      color: 'bg-green-50 dark:bg-green-950',
    },
  ];

  // Dummy data for driver distribution
  const driverDistribution = {
    departments: [
      { name: 'Sales', count: 8, color: 'bg-blue-500' },
      { name: 'Operations', count: 5, color: 'bg-green-500' },
      { name: 'Delivery', count: 7, color: 'bg-amber-500' },
      { name: 'Executive', count: 2, color: 'bg-purple-500' },
      { name: 'Support', count: 2, color: 'bg-pink-500' },
    ],
    licenseTypes: [
      { name: 'Class A', count: 4, color: 'bg-blue-500' },
      { name: 'Class B', count: 6, color: 'bg-green-500' },
      { name: 'CDL', count: 10, color: 'bg-amber-500' },
      { name: 'Class C', count: 4, color: 'bg-purple-500' },
    ],
  };

  const calculatePercentage = (count, total) => {
    return ((count / total) * 100).toFixed(0);
  };

  const totalDrivers = driverDistribution.departments.reduce((sum, dept) => sum + dept.count, 0);
  const totalLicenses = driverDistribution.licenseTypes.reduce((sum, type) => sum + type.count, 0);

  return (
    <div className="mt-8">
      <h2 className="text-xl font-semibold mb-6">Driver Analytics</h2>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {stats.map((stat, index) => (
          <div key={index} className={`rounded-lg p-6 border border-border ${stat.color}`}>
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">{stat.title}</p>
                <h3 className="text-2xl font-bold mt-1">{stat.value}</h3>
                <p
                  className={`text-xs mt-1 ${
                    stat.change.startsWith('+')
                      ? 'text-green-600 dark:text-green-500'
                      : 'text-red-600 dark:text-red-500'
                  }`}
                >
                  {stat.change} from last month
                </p>
              </div>
              <div className="rounded-full p-2 bg-background">{stat.icon}</div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Department Distribution */}
        <div className="bg-card rounded-lg shadow-sm p-6 border border-border">
          <h3 className="font-medium mb-4">Driver Department Distribution</h3>
          <div className="space-y-4">
            {driverDistribution.departments.map((dept, index) => (
              <div key={index}>
                <div className="flex justify-between mb-1 text-sm">
                  <span>{dept.name}</span>
                  <span className="font-medium">
                    {dept.count} ({calculatePercentage(dept.count, totalDrivers)}%)
                  </span>
                </div>
                <div className="w-full bg-muted rounded-full h-2">
                  <div
                    className={`${dept.color} h-2 rounded-full`}
                    style={{ width: `${calculatePercentage(dept.count, totalDrivers)}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* License Type Distribution */}
        <div className="bg-card rounded-lg shadow-sm p-6 border border-border">
          <h3 className="font-medium mb-4">Driver License Distribution</h3>
          <div className="space-y-4">
            {driverDistribution.licenseTypes.map((license, index) => (
              <div key={index}>
                <div className="flex justify-between mb-1 text-sm">
                  <span>{license.name}</span>
                  <span className="font-medium">
                    {license.count} ({calculatePercentage(license.count, totalLicenses)}%)
                  </span>
                </div>
                <div className="w-full bg-muted rounded-full h-2">
                  <div
                    className={`${license.color} h-2 rounded-full`}
                    style={{ width: `${calculatePercentage(license.count, totalLicenses)}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DataVisualization;
