import React, {useState, useEffect} from 'react';
import {BaseWidget} from '../dashboard/BaseWidget';
import {getNumberOfDrivers} from '../../backend/api/drivers';
import {registerWidget, WIDGET_TYPES, WIDGET_CATEGORIES} from '../../utils/widgetRegistry';
import {LineChart} from 'lucide-react';

// Simple SVG line graph
const LineGraphSVG = ({points, width = 220, height = 100, color = '#22c55e'}) => {
    if (!points || points.length === 0) return <svg width={width} height={height}></svg>;
    // Filter out points with invalid x or y
    const validPoints = points.filter(p => typeof p.x === 'number' && typeof p.y === 'number' && !isNaN(p.x) && !isNaN(p.y));
    if (validPoints.length === 0) return <svg width={width} height={height}></svg>;
    // Normalize points to fit SVG
    const maxY = Math.max(...validPoints.map(p => p.y), 1);
    const minY = Math.min(...validPoints.map(p => p.y), 0);
    const minX = Math.min(...validPoints.map(p => p.x), 0);
    const maxX = Math.max(...validPoints.map(p => p.x), 1);
    const pad = 20;
    const graphW = width - pad * 2;
    const graphH = height - pad * 2;
    // Prevent division by zero
    const xRange = maxX - minX === 0 ? 1 : maxX - minX;
    const yRange = maxY - minY === 0 ? 1 : maxY - minY;
    const getX = x => pad + ((x - minX) / xRange) * graphW;
    const getY = y => height - pad - ((y - minY) / yRange) * graphH;
    return (
        <svg width={width} height={height}>
            <polyline
                fill="none"
                stroke={color}
                strokeWidth="3"
                points={validPoints.map(p => `${getX(p.x)},${getY(p.y)}`).join(' ')}
            />
            {/* Draw axis */}
            <line x1={pad} y1={height - pad} x2={width - pad} y2={height - pad} stroke="#888" />
            <line x1={pad} y1={pad} x2={pad} y2={height - pad} stroke="#888" />
            {/* Draw points */}
            {validPoints.map((p, i) => (
                <circle key={i} cx={getX(p.x)} cy={getY(p.y)} r={3} fill={color} />
            ))}
            {/* Draw labels */}
            {validPoints.length > 0 && (
                <text x={pad} y={pad - 5} fontSize="10" fill="#555">Date</text>
            )}
            {validPoints.length > 0 && (
                <text x={width - pad} y={height - pad + 12} fontSize="10" fill="#555" textAnchor="end">Total Drivers</text>
            )}
        </svg>
    );
};

const DriverGrowthLineGraphWidget = ({id, config = {}}) => {
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchDriverCount = async () => {
            try {
                setLoading(true);
                setError(null);
                // Fetch all driver count history (no date filter)
                const response = await getNumberOfDrivers({});
                // response.data is expected to be an array of objects with _id, number_of_drivers, date
                const driverHistory = Array.isArray(response?.data)
                    ? response.data
                    : [];
                // Map to points for the graph
                const points = driverHistory.map(item => ({
                    x: new Date(item.date).getTime(),
                    y: item.number_of_drivers,
                    date: item.date,
                }));
                setHistory(points);
            } catch (err) {
                console.error('Failed to fetch driver count:', err);
                setError('Failed to load driver growth data');
            } finally {
                setLoading(false);
            }
        };
        fetchDriverCount();
        const refreshInterval = (config.refreshInterval || 60) * 1000;
        const interval = setInterval(fetchDriverCount, refreshInterval);
        return () => clearInterval(interval);
    }, [config.refreshInterval]);

    return (
        <BaseWidget
            id={id}
            title={config.title || 'Driver Growth Over Time'}
            loading={loading}
            error={error}
            className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-950 dark:to-green-900"
        >
            <div className="flex items-center justify-between h-full">
                <div className="flex-1 flex flex-col justify-center">
                    <LineGraphSVG points={history} />
                </div>
                <div className="flex-shrink-0">
                    <div className="w-12 h-12 bg-green-200 dark:bg-green-800 rounded-full flex items-center justify-center">
                        <LineChart className="h-6 w-6 text-green-600 dark:text-green-300" />
                    </div>
                </div>
            </div>
        </BaseWidget>
    );
};

registerWidget(WIDGET_TYPES.DRIVER_GROWTH_LINE_GRAPH || 'driver_growth_line_graph', DriverGrowthLineGraphWidget, {
    title: 'Driver Growth Line Graph',
    description: 'Shows a line graph of total drivers over time',
    category: WIDGET_CATEGORIES.DRIVERS,
    icon: LineChart,
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

export default DriverGrowthLineGraphWidget;
