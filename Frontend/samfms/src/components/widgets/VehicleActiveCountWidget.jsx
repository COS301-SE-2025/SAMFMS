import React, { useState, useEffect } from 'react';
import { BaseWidget } from '../dashboard/BaseWidget';
import { getVehicles } from '../../backend/api/vehicles';
import { registerWidget, WIDGET_TYPES, WIDGET_CATEGORIES } from '../../utils/widgetRegistry';
import { CheckCircle } from 'lucide-react';

const VehicleActiveCountWidget = ({ id, config = {} }) => {
  const [vehicleData, setVehicleData] = useState({ active: 0, total: 0 });
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
            if (
              vehicle.status?.toLowerCase() === 'active' ||
              vehicle.status?.toLowerCase() === 'operational'
            ) {
              acc.active++;
            }
            return acc;
          },
          { active: 0, total: 0 }
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
    vehicleData.total > 0 ? Math.round((vehicleData.active / vehicleData.total) * 100) : 0;

  return (
    <BaseWidget
      id={id}
      title={config.title || 'Active Vehicles'}
      loading={loading}
      error={error}
      className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-950 dark:to-green-900"
    >
      <div className="flex items-center justify-between h-full">
        <div className="flex-1">
          <div className="text-3xl font-bold text-green-800 dark:text-green-200 mb-1">
            {vehicleData.active}
          </div>
          <div className="text-sm text-green-600 dark:text-green-400">Active & Operational</div>
          <div className="text-xs text-green-500 dark:text-green-400 mt-1">
            {percentage}% of fleet
          </div>
        </div>
        <div className="flex-shrink-0">
          <div className="w-12 h-12 bg-green-200 dark:bg-green-800 rounded-full flex items-center justify-center">
            <CheckCircle className="h-6 w-6 text-green-600 dark:text-green-300" />
          </div>
        </div>
      </div>
    </BaseWidget>
  );
};

registerWidget(WIDGET_TYPES.VEHICLE_ACTIVE_COUNT, VehicleActiveCountWidget, {
  title: 'Active Vehicle Count',
  description: 'Count of active and operational vehicles',
  category: WIDGET_CATEGORIES.VEHICLES,
  icon: CheckCircle,
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

export default VehicleActiveCountWidget;
