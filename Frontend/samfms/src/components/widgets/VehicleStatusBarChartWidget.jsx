import React, {useState, useEffect} from 'react';
import {BaseWidget} from '../dashboard/BaseWidget';
import {getVehicles} from '../../backend/api/vehicles';
import {registerWidget, WIDGET_TYPES, WIDGET_CATEGORIES} from '../../utils/widgetRegistry';
import {BarChart} from 'lucide-react';

// Simple bar chart using SVG (replace with chart library if available)
const BarChartSVG = ({data, labels, colors}) => {
    const max = Math.max(...data, 1);
    return (
        <svg width="100%" height="80" viewBox="0 0 180 80">
            {data.map((value, i) => {
                const barHeight = (value / max) * 60;
                return (
                    <g key={i}>
                        <rect
                            x={20 + i * 50}
                            y={70 - barHeight}
                            width={30}
                            height={barHeight}
                            fill={colors[i]}
                            rx={5}
                        />
                        <text
                            x={35 + i * 50}
                            y={75}
                            textAnchor="middle"
                            fontSize="12"
                            fill="#555"
                        >
                            {labels[i]}
                        </text>
                        <text
                            x={35 + i * 50}
                            y={65 - barHeight}
                            textAnchor="middle"
                            fontSize="14"
                            fontWeight="bold"
                            fill="#222"
                        >
                            {value}
                        </text>
                    </g>
                );
            })}
        </svg>
    );
};

const VehicleStatusBarChartWidget = ({id, config = {}}) => {
    const [counts, setCounts] = useState({active: 0, inactive: 0, maintenance: 0});
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchVehicleStatus = async () => {
            try {
                setLoading(true);
                setError(null);
                const response = await getVehicles({limit: 1000});
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
                if (!Array.isArray(vehiclesArray)) vehiclesArray = [];
                const active = vehiclesArray.filter(v => (v.status || '').toLowerCase() === 'active').length;
                const inactive = vehiclesArray.filter(v => (v.status || '').toLowerCase() === 'inactive').length;
                const maintenance = vehiclesArray.filter(v => (v.status || '').toLowerCase() === 'maintenance').length;
                setCounts({active, inactive, maintenance});
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
            title={config.title || 'Vehicle Status Overview'}
            loading={loading}
            error={error}
            className="bg-gradient-to-br from-indigo-50 to-indigo-100 dark:from-indigo-950 dark:to-indigo-900"
        >
            <div className="flex items-center justify-between h-full">
                <div className="flex-1 flex flex-col justify-center">
                    <BarChartSVG
                        data={[counts.active, counts.inactive, counts.maintenance]}
                        labels={["Active", "Inactive", "Maintenance"]}
                        colors={["#4ade80", "#fca5a5", "#fbbf24"]}
                    />
                </div>
                <div className="flex-shrink-0">
                    <div className="w-12 h-12 bg-indigo-200 dark:bg-indigo-800 rounded-full flex items-center justify-center">
                        <BarChart className="h-6 w-6 text-indigo-600 dark:text-indigo-300" />
                    </div>
                </div>
            </div>
        </BaseWidget>
    );
};

registerWidget(WIDGET_TYPES.VEHICLE_STATUS_BAR_CHART, VehicleStatusBarChartWidget, {
    title: 'Vehicle Status Bar Chart',
    description: 'Shows active, inactive, and maintenance vehicles as a bar chart',
    category: WIDGET_CATEGORIES.VEHICLES,
    icon: BarChart,
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
    defaultSize: {w: 4, h: 2},
    minSize: {w: 3, h: 1},
    maxSize: {w: 6, h: 4},
});

export default VehicleStatusBarChartWidget;
