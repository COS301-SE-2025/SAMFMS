import React, {useState, useEffect} from 'react';
import {useRef} from 'react';
import {BaseWidget} from '../dashboard/BaseWidget';
import {getNumberOfDrivers} from '../../backend/api/drivers';
import {registerWidget, WIDGET_TYPES, WIDGET_CATEGORIES} from '../../utils/widgetRegistry';
import {LineChart} from 'lucide-react';

// Simple SVG line graph
const LineGraphSVG = ({points, width = 220, height = 100, color = '#22c55e'}) => {
    const [hoveredIdx, setHoveredIdx] = React.useState(null);
    if (!points || points.length === 0) return <svg width={width} height={height}></svg>;
    // Filter out points with invalid x or y
    const validPoints = points.filter(p => p && typeof p.x === 'number' && typeof p.y === 'number' && !isNaN(p.x) && !isNaN(p.y));
    if (validPoints.length === 0) return <svg width={width} height={height}></svg>;
    // Normalize points to fit SVG
    const maxY = Math.max(...validPoints.map(p => p.y), 1);
    const minY = Math.min(...validPoints.map(p => p.y), 0);
    const minX = Math.min(...validPoints.map(p => p.x), 0);
    const maxX = Math.max(...validPoints.map(p => p.x), 1);
    const pad = 28;
    const graphW = width - pad * 2;
    const graphH = height - pad * 2;
    // Prevent division by zero
    const xRange = maxX - minX === 0 ? 1 : maxX - minX;
    const yRange = maxY - minY === 0 ? 1 : maxY - minY;
    const getX = x => pad + ((x - minX) / xRange) * graphW;
    const getY = y => height - pad - ((y - minY) / yRange) * graphH;
    // Format date for x axis
    const formatDate = d => {
        const date = new Date(d);
        return date.toLocaleDateString(undefined, {month: 'short', day: 'numeric'});
    };
    // X axis ticks (show up to 5 evenly spaced dates)
    const xTickCount = Math.min(5, validPoints.length);
    const xTickIndexes = xTickCount > 1 ? Array.from({length: xTickCount}, (_, i) => Math.round(i * (validPoints.length - 1) / (xTickCount - 1))) : [];
    const xTicks = xTickIndexes.map(idx => validPoints[idx]).filter(Boolean);
    return (
        <svg width={width} height={height}>
            {/* Axes */}
            <line x1={pad} y1={height - pad} x2={width - pad} y2={height - pad} stroke="#888" />
            <line x1={pad} y1={pad} x2={pad} y2={height - pad} stroke="#888" />
            {/* Y axis label */}
            <text x={pad - 10} y={pad} fontSize="12" fill="#fff" textAnchor="middle" fontWeight="bold" transform={`rotate(-90,${pad - 10},${pad})`}>Number of Drivers</text>
            {/* X axis label */}
            <text x={width / 2} y={height - 8} fontSize="12" fill="#fff" textAnchor="middle" fontWeight="bold">Date</text>
            {/* X axis ticks */}
            {xTicks.map((p, i) => (
                p ? <text key={i} x={getX(p.x)} y={height - pad + 14} fontSize="9" fill="#888" textAnchor="middle">{formatDate(p.date)}</text> : null
            ))}
            {/* Line and points */}
            <polyline
                fill="none"
                stroke={color}
                strokeWidth="3"
                points={validPoints.map(p => `${getX(p.x)},${getY(p.y)}`).join(' ')}
            />
            {validPoints.map((p, i) => (
                <g key={i}>
                    <circle
                        cx={getX(p.x)}
                        cy={getY(p.y)}
                        r={4}
                        fill={color}
                        style={{cursor: 'pointer'}}
                        onMouseEnter={() => setHoveredIdx(i)}
                        onMouseLeave={() => setHoveredIdx(null)}
                    />
                    {hoveredIdx === i && (
                        <rect
                            x={getX(p.x) - 18}
                            y={getY(p.y) - 30}
                            width={36}
                            height={18}
                            rx={4}
                            fill="#fff"
                            stroke="#888"
                            strokeWidth={0.5}
                        />
                    )}
                    {hoveredIdx === i && (
                        <text
                            x={getX(p.x)}
                            y={getY(p.y) - 18}
                            fontSize="11"
                            fill="#222"
                            textAnchor="middle"
                            fontWeight="bold"
                        >
                            {p.y}
                        </text>
                    )}
                </g>
            ))}
        </svg>
    );
};

const DriverGrowthLineGraphWidget = ({id, config = {}}) => {
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filter, setFilter] = useState('day'); // day, month, year
    const graphContainerRef = useRef(null);
    const [graphSize, setGraphSize] = useState({width: 220, height: 100});

    useEffect(() => {
        const fetchDriverCount = async () => {
            try {
                setLoading(true);
                setError(null);
                // Fetch all driver count history (no date filter)
                const response = await getNumberOfDrivers({});
                // response.data is expected to be an array of objects with _id, number_of_drivers, date
                const driverHistory = Array.isArray(response?.data?.data)
                    ? response.data.data
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

    // Responsive graph size
    useEffect(() => {
        const handleResize = () => {
            if (graphContainerRef.current) {
                const rect = graphContainerRef.current.getBoundingClientRect();
                setGraphSize({
                    width: Math.max(220, Math.floor(rect.width)),
                    height: Math.max(100, Math.floor(rect.height)),
                });
            }
        };
        handleResize();
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    // Filter points by day, month, year
    const filteredHistory = React.useMemo(() => {
        if (filter === 'day') return history;
        if (filter === 'month') {
            // Group by month
            const map = new Map();
            history.forEach(p => {
                const d = new Date(p.date);
                const key = `${d.getFullYear()}-${d.getMonth()}`;
                if (!map.has(key) || d.getTime() > map.get(key).x) {
                    map.set(key, p);
                }
            });
            return Array.from(map.values());
        }
        if (filter === 'year') {
            // Group by year
            const map = new Map();
            history.forEach(p => {
                const d = new Date(p.date);
                const key = `${d.getFullYear()}`;
                if (!map.has(key) || d.getTime() > map.get(key).x) {
                    map.set(key, p);
                }
            });
            return Array.from(map.values());
        }
        return history;
    }, [history, filter]);

    return (
        <BaseWidget
            id={id}
            title={config.title || 'Driver Growth Over Time'}
            loading={loading}
            error={error}
            className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-950 dark:to-green-900"
        >
            <div className="flex flex-col h-full w-full" ref={graphContainerRef}>
                <div className="flex justify-end mb-2">
                    <select
                        value={filter}
                        onChange={e => setFilter(e.target.value)}
                        className="border rounded px-2 py-1 text-xs bg-white dark:bg-gray-900"
                        style={{minWidth: 80}}
                    >
                        <option value="day">Day</option>
                        <option value="month">Month</option>
                        <option value="year">Year</option>
                    </select>
                </div>
                <div className="flex-1 flex flex-col justify-center items-center w-full h-full">
                    <LineGraphSVG points={filteredHistory} width={graphSize.width} height={graphSize.height} />
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
