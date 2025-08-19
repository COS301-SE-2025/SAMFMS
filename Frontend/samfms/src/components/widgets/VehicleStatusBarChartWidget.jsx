import React, {useState, useEffect} from 'react';
import {BaseWidget} from '../dashboard/BaseWidget';
import {getVehicles} from '../../backend/api/vehicles';
import {registerWidget, WIDGET_TYPES, WIDGET_CATEGORIES} from '../../utils/widgetRegistry';
import {BarChart} from 'lucide-react';

// Simple bar chart using SVG (replace with chart library if available)
const BarChartSVG = ({data, labels, colors}) => {
    const max = Math.max(...data, 1);
    const barSpacing = 90;
    // Remove heading from SVG, keep only chart elements
    return (
        <svg width="100%" height="150" viewBox={`0 0 ${barSpacing * data.length} 150`} className="w-full h-40">
            {data.map((value, i) => {
                const barHeight = (value / max) * 60;
                const xBase = 35 + i * barSpacing;
                return (
                    <g key={i}>
                        {/* Headings with extra vertical space */}
                        <text
                            x={xBase}
                            y={130}
                            textAnchor="middle"
                            fontSize="14"
                            fill="#fff"
                            fontWeight="bold"
                        >
                            {labels[i]}
                        </text>
                        <rect
                            x={xBase - 15}
                            y={115 - barHeight}
                            width={30}
                            height={barHeight}
                            fill={colors[i]}
                            rx={5}
                        />
                        <text
                            x={xBase}
                            y={110 - barHeight}
                            textAnchor="middle"
                            fontSize="14"
                            fontWeight="bold"
                            fill="#fff"
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
    const [counts, setCounts] = useState({available: 0, unavailable: 0});
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchVehicleStatus = async () => {
            try {
                setLoading(true);
                setError(null);
                const response = await getVehicles({limit: 1000});
                console.log('Raw vehicle response:', response);
                let vehiclesArray = [];
                if (response && response.data && response.data.data && Array.isArray(response.data.data.vehicles)) {
                    vehiclesArray = response.data.data.vehicles;
                }
                console.log('Vehicles array:', vehiclesArray);
                if (!Array.isArray(vehiclesArray)) vehiclesArray = [];
                const available = vehiclesArray.filter(v => (v.status || '').toLowerCase() === 'available').length;
                const unavailable = vehiclesArray.filter(v => (v.status || '').toLowerCase() === 'unavailable').length;
                setCounts({available, unavailable});
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
            <div className="flex flex-col items-center justify-center h-full w-full">
                {/* Heading with Tailwind for padding and styling */}
                <div className="pt-12 pb-2">
                    <span className="text-white font-bold text-2xl">Vehicle Status</span>
                </div>
                <div className="flex items-center justify-between w-full">
                    <div className="flex-1 flex flex-col justify-center pb-8">
                        <BarChartSVG
                            data={[counts.available, counts.unavailable]}
                            labels={["Available", "Unavailable"]}
                            colors={["#4ade80", "#fca5a5"]}
                            className=""
                        />
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
    defaultSize: {w: 3, h: 6},
    minSize: {w: 3, h: 3},
    maxSize: {w: 8, h: 8},
});

export default VehicleStatusBarChartWidget;
