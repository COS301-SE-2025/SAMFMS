import React, { useState, useEffect } from 'react';
import { BaseWidget } from '../dashboard/BaseWidget';
import { getVehicles } from '../../backend/api/vehicles';
import { registerWidget, WIDGET_TYPES, WIDGET_CATEGORIES } from '../../utils/widgetRegistry';
import { Clock } from 'lucide-react';

const VehicleIdleCountWidget = ({ id, config = {} }) => {
  const [vehicleData, setVehicleData] = useState({ idle: 0, total: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchVehicleStatus = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await getVehicles({ limit: 1000 });

        let vehiclesArray = [];
        if (response) {
          if (Array.isArray(response)) {
            vehiclesArray = response;
          } else if (response.vehicles && Array.isArray(response.vehicles)) {
            vehiclesArray = response.vehicles;
          } else if (response.data && Array.isArray(response.data)) {
            vehiclesArray = response.data;
          } else if (response.items && Array.isArray(response.items)) {
            vehiclesArray = response.items;
          }
        }

        if (!Array.isArray(vehiclesArray)) {
          vehiclesArray = [];
        }

        const statusCounts = vehiclesArray.reduce(
          (acc, vehicle) => {
            acc.total++;
            const status = vehicle.status?.toLowerCase();
            if (
              status === 'idle' ||
              status === 'available' ||
              !status ||
              (status !== 'active' &&
                status !== 'operational' &&
                status !== 'maintenance' &&
                status !== 'in_maintenance')
            ) {
              acc.idle++;
            }
            return acc;
          },
          { idle: 0, total: 0 }
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

    const refreshInterval = (config.refreshInterval || 60) * 1000;
    const interval = setInterval(fetchVehicleStatus, refreshInterval);

    return () => clearInterval(interval);
  }, [config.refreshInterval]);

  const percentage =
    vehicleData.total > 0 ? Math.round((vehicleData.idle / vehicleData.total) * 100) : 0;

  return (
    <BaseWidget
      id={id}
      title={config.title || 'Idle Vehicles'}
      loading={loading}
      error={error}
      className="bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-950 dark:to-gray-900"
    >
      <div className="flex items-center justify-between h-full">
        <div className="flex-1">
          <div className="text-3xl font-bold text-gray-800 dark:text-gray-200 mb-1">
            {vehicleData.idle}
          </div>
          <div className="text-sm text-gray-600 dark:text-gray-400">Idle & Available</div>
          <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            {percentage}% of fleet
          </div>
        </div>
        <div className="flex-shrink-0">
          <div className="w-12 h-12 bg-gray-200 dark:bg-gray-800 rounded-full flex items-center justify-center">
            <Clock className="h-6 w-6 text-gray-600 dark:text-gray-300" />
          </div>
        </div>
      </div>
    </BaseWidget>
  );
};

registerWidget(WIDGET_TYPES.VEHICLE_IDLE_COUNT, VehicleIdleCountWidget, {
  title: 'Idle Vehicle Count',
  description: 'Count of idle and available vehicles',
  category: WIDGET_CATEGORIES.VEHICLES,
  icon: Clock,
  defaultConfig: {
    refreshInterval: 60,
  },
  configSchema: {
    refreshInterval: {
      type: 'number',
      label: 'Refresh Interval (seconds)',
      min: 30,
      max: 3600,
      default: 60,
    },
  },
  defaultSize: { w: 3, h: 2 },
  minSize: { w: 2, h: 1 },
  maxSize: { w: 4, h: 3 },
});

export default VehicleIdleCountWidget;
