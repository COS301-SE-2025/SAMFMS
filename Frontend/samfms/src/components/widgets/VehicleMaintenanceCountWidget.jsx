import React, {useState, useEffect} from 'react';
import {BaseWidget} from '../dashboard/BaseWidget';
import {maintenanceAPI} from '../../backend/api/maintenance';
import {registerWidget, WIDGET_TYPES, WIDGET_CATEGORIES} from '../../utils/widgetRegistry';
import {AlertTriangle} from 'lucide-react';

const VehicleMaintenanceCountWidget = ({id, config = {}}) => {
  const [vehicleData, setVehicleData] = useState({maintenance: 0, total: 0});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchVehicleStatus = async () => {
      try {
        setLoading(true);
        setError(null);

        // const response = await getVehicles({limit: 1000});
        const response = await maintenanceAPI.getMaintenanceDashboard();
        const dashboardData = response.data?.data || response.data || {};

        console.log(dashboardData);

        // let vehiclesArray = [];
        // if (response) {
        //   if (Array.isArray(response)) {
        //     vehiclesArray = response;
        //   } else if (response.vehicles && Array.isArray(response.vehicles)) {
        //     vehiclesArray = response.vehicles;
        //   } else if (response.data && Array.isArray(response.data)) {
        //     vehiclesArray = response.data;
        //   } else if (response.items && Array.isArray(response.items)) {
        //     vehiclesArray = response.items;
        //   }
        // }

        // if (!Array.isArray(vehiclesArray)) {
        //   vehiclesArray = [];
        // }

        // const statusCounts = vehiclesArray.reduce(
        //   (acc, vehicle) => {
        //     acc.total++;
        //     if (
        //       vehicle.status?.toLowerCase() === 'maintenance' ||
        //       vehicle.status?.toLowerCase() === 'in_maintenance'
        //     ) {
        //       acc.maintenance++;
        //     }
        //     return acc;
        //   },
        //   {maintenance: 0, total: 0}
        // );

        // setVehicleData(statusCounts);
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
    vehicleData.total > 0 ? Math.round((vehicleData.maintenance / vehicleData.total) * 100) : 0;

  return (
    <BaseWidget
      id={id}
      title={config.title || 'In Maintenance'}
      loading={loading}
      error={error}
      className="bg-gradient-to-br from-yellow-50 to-yellow-100 dark:from-yellow-950 dark:to-yellow-900"
    >
      <div className="flex items-center justify-between h-full">
        <div className="flex-1">
          <div className="text-3xl font-bold text-yellow-800 dark:text-yellow-200 mb-1">
            {vehicleData.maintenance}
          </div>
          <div className="text-sm text-yellow-600 dark:text-yellow-400">Under Maintenance</div>
          <div className="text-xs text-yellow-500 dark:text-yellow-400 mt-1">
            {percentage}% of fleet
          </div>
        </div>
        <div className="flex-shrink-0">
          <div className="w-12 h-12 bg-yellow-200 dark:bg-yellow-800 rounded-full flex items-center justify-center">
            <AlertTriangle className="h-6 w-6 text-yellow-600 dark:text-yellow-300" />
          </div>
        </div>
      </div>
    </BaseWidget>
  );
};

registerWidget(WIDGET_TYPES.VEHICLE_MAINTENANCE_COUNT, VehicleMaintenanceCountWidget, {
  title: 'Vehicle Maintenance Count',
  description: 'Count of vehicles currently under maintenance',
  category: WIDGET_CATEGORIES.VEHICLES,
  icon: AlertTriangle,
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
  defaultSize: {w: 3, h: 2},
  minSize: {w: 2, h: 1},
  maxSize: {w: 4, h: 3},
});

export default VehicleMaintenanceCountWidget;
