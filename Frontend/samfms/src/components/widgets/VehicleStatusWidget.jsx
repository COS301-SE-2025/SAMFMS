import React, {useState, useEffect} from 'react';
import {BaseWidget} from '../dashboard/BaseWidget';
import {getVehicles} from '../../backend/api/vehicles';
import {registerWidget, WIDGET_TYPES, WIDGET_CATEGORIES} from '../../utils/widgetRegistry';
import {Truck, CheckCircle, XCircle} from 'lucide-react';

const VehicleStatusWidget = ({id, config = {}}) => {
  const [vehicleData, setVehicleData] = useState({
    total: 0,
    available: 0,
    unavailable: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchVehicleStatus = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await getVehicles({limit: 1000}); // Get all vehicles

        // Extract vehicles from response.data.data.vehicles as specified
        let vehiclesArray = [];
        if (response?.data?.data?.vehicles && Array.isArray(response.data.data.vehicles)) {
          vehiclesArray = response.data.data.vehicles;
        }

        console.log('Processed vehicles array:', vehiclesArray, 'Length:', vehiclesArray.length);

        // Calculate status counts for available/unavailable only
        const statusCounts = vehiclesArray.reduce(
          (acc, vehicle) => {
            acc.total++;

            const status = vehicle.status?.toLowerCase();
            if (status === 'available') {
              acc.available++;
            } else if (status === 'unavailable') {
              acc.unavailable++;
            } else {
              // Default unknown statuses to unavailable
              acc.unavailable++;
            }

            return acc;
          },
          {total: 0, available: 0, unavailable: 0}
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
      icon: <Truck className="h-4 w-4 text-blue-600" />,
      color: 'bg-blue-100 dark:bg-blue-900',
      textColor: 'text-blue-800 dark:text-blue-200',
    },
    {
      title: 'Available',
      value: vehicleData.available,
      icon: <CheckCircle className="h-4 w-4 text-green-600" />,
      color: 'bg-green-100 dark:bg-green-900',
      textColor: 'text-green-800 dark:text-green-200',
    },
    {
      title: 'Unavailable',
      value: vehicleData.unavailable,
      icon: <XCircle className="h-4 w-4 text-red-600" />,
      color: 'bg-red-100 dark:bg-red-900',
      textColor: 'text-red-800 dark:text-red-200',
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
      <div className="flex flex-col justify-center gap-2 h-full p-1 overflow-hidden">
        {statusCards.map((card, index) => (
          <div key={index} className="flex items-center space-x-2 min-h-0 flex-shrink">
            <div className={`p-1.5 rounded-md ${card.color} flex-shrink-0`}>
              {card.icon}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs text-muted-foreground truncate leading-tight">{card.title}</p>
              <p className={`text-sm font-bold ${card.textColor} truncate leading-tight`}>{card.value}</p>
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
  defaultSize: {w: 3, h: 6},
  minSize: {w: 3, h: 3},
  maxSize: {w: 8, h: 8},
  icon: Truck,
  configSchema: {
    title: {type: 'string', default: 'Vehicle Status Overview'},
    refreshInterval: {type: 'number', default: 60, min: 30},
  },
});

export default VehicleStatusWidget;
