import React, { useState, useEffect } from 'react';
import { BaseWidget } from '../dashboard/BaseWidget';
import { getVehicles } from '../../backend/api/vehicles';
import { registerWidget, WIDGET_TYPES, WIDGET_CATEGORIES } from '../../utils/widgetRegistry';
import { Truck, CheckCircle, AlertTriangle, Clock } from 'lucide-react';

const VehicleStatusWidget = ({ id, config = {} }) => {
  const [vehicleData, setVehicleData] = useState({
    total: 0,
    active: 0,
    maintenance: 0,
    idle: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchVehicleStatus = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await getVehicles({ limit: 1000 }); // Get all vehicles
        const vehiclesArray = response.vehicles || response || [];

        // Calculate status counts
        const statusCounts = vehiclesArray.reduce(
          (acc, vehicle) => {
            acc.total++;

            switch (vehicle.status?.toLowerCase()) {
              case 'active':
              case 'operational':
                acc.active++;
                break;
              case 'maintenance':
              case 'in_maintenance':
                acc.maintenance++;
                break;
              case 'idle':
              case 'available':
                acc.idle++;
                break;
              default:
                acc.idle++;
            }

            return acc;
          },
          { total: 0, active: 0, maintenance: 0, idle: 0 }
        );

        setVehicleData(statusCounts);
      } catch (err) {
        console.error('Failed to fetch vehicle status:', err);
        setError('Failed to load vehicle data');
      } finally {
        setLoading(false);
      }
    };

    fetchVehicleStatus();

    // Set up refresh interval
    const refreshInterval = (config.refreshInterval || 60) * 1000;
    const interval = setInterval(fetchVehicleStatus, refreshInterval);

    return () => clearInterval(interval);
  }, [config.refreshInterval]);

  const statusCards = [
    {
      title: 'Total Vehicles',
      value: vehicleData.total,
      icon: <Truck className="h-6 w-6 text-blue-600" />,
      color: 'bg-blue-100 dark:bg-blue-900',
      textColor: 'text-blue-800 dark:text-blue-200',
    },
    {
      title: 'Active',
      value: vehicleData.active,
      icon: <CheckCircle className="h-6 w-6 text-green-600" />,
      color: 'bg-green-100 dark:bg-green-900',
      textColor: 'text-green-800 dark:text-green-200',
    },
    {
      title: 'Maintenance',
      value: vehicleData.maintenance,
      icon: <AlertTriangle className="h-6 w-6 text-yellow-600" />,
      color: 'bg-yellow-100 dark:bg-yellow-900',
      textColor: 'text-yellow-800 dark:text-yellow-200',
    },
    {
      title: 'Idle',
      value: vehicleData.idle,
      icon: <Clock className="h-6 w-6 text-gray-600" />,
      color: 'bg-gray-100 dark:bg-gray-900',
      textColor: 'text-gray-800 dark:text-gray-200',
    },
  ];

  return (
    <BaseWidget
      id={id}
      title={config.title || 'Vehicle Status Overview'}
      config={config}
      loading={loading}
      error={error}
    >
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 h-full">
        {statusCards.map((card, index) => (
          <div key={index} className="flex items-center space-x-2 min-h-0">
            <div className={`p-2 rounded-lg ${card.color} flex-shrink-0`}>{card.icon}</div>
            <div className="min-w-0 flex-1">
              <p className="text-xs text-muted-foreground truncate">{card.title}</p>
              <p className={`text-lg font-bold ${card.textColor}`}>{card.value}</p>
            </div>
          </div>
        ))}
      </div>
    </BaseWidget>
  );
};

// Register the widget
registerWidget(WIDGET_TYPES.VEHICLE_STATUS, VehicleStatusWidget, {
  title: 'Vehicle Status',
  description: 'Overview of vehicle statuses across your fleet',
  category: WIDGET_CATEGORIES.VEHICLES,
  defaultSize: { w: 3, h: 2 },
  minSize: { w: 2, h: 2 },
  maxSize: { w: 4, h: 3 },
  icon: <Truck size={20} />,
  configSchema: {
    title: { type: 'string', default: 'Vehicle Status Overview' },
    refreshInterval: { type: 'number', default: 60, min: 30 },
  },
});

export default VehicleStatusWidget;
