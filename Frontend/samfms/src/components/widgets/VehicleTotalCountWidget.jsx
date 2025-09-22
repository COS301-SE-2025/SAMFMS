import React, {useState, useEffect} from 'react';
import {BaseWidget} from '../dashboard/BaseWidget';
import {getVehicles} from '../../backend/api/vehicles';
import {registerWidget, WIDGET_TYPES, WIDGET_CATEGORIES} from '../../utils/widgetRegistry';
import {Truck} from 'lucide-react';

const VehicleTotalCountWidget = ({id, config = {}}) => {
  const [vehicleData, setVehicleData] = useState({total: 0});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchVehicleStatus = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await getVehicles({limit: 1000});
        const vehiclesData =
          response.data?.data?.vehicles || response.vehicles || response.data?.vehicles || [];

        const transformedVehicles = vehiclesData.filter(vehicle => vehicle !== null);

        setVehicleData({total: transformedVehicles.length});
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

  return (
    <BaseWidget
      id={id}
      title={config.title || 'Total Vehicles'}
      loading={loading}
      error={error}
      className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-950 dark:to-blue-900"
    >
      <div className="flex items-center justify-between h-full">
        <div className="flex-1">
          <div className="text-3xl font-bold text-blue-800 dark:text-blue-200 mb-1">
            {vehicleData.total}
          </div>
          <div className="text-sm text-blue-600 dark:text-blue-400">
            {vehicleData.total === 1 ? 'Vehicle' : 'Vehicles'} in Fleet
          </div>
        </div>
        <div className="flex-shrink-0">
          <div className="w-12 h-12 bg-blue-200 dark:bg-blue-800 rounded-full flex items-center justify-center">
            <Truck className="h-6 w-6 text-blue-600 dark:text-blue-300" />
          </div>
        </div>
      </div>
    </BaseWidget>
  );
};

registerWidget(WIDGET_TYPES.VEHICLE_TOTAL_COUNT, VehicleTotalCountWidget, {
  title: 'Total Vehicle Count',
  description: 'Total count of vehicles in the fleet',
  category: WIDGET_CATEGORIES.VEHICLES,
  icon: Truck,
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

export default VehicleTotalCountWidget;
