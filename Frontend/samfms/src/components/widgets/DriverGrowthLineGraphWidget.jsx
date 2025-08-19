import React, {useState, useEffect} from 'react';
import {useRef} from 'react';
import {BaseWidget} from '../dashboard/BaseWidget';
import {getNumberOfDrivers} from '../../backend/api/drivers';
import {registerWidget, WIDGET_TYPES, WIDGET_CATEGORIES} from '../../utils/widgetRegistry';
import {LineChart} from 'lucide-react';



const DriverGrowthLineGraphWidget = ({id, config = {}}) => {
    const [dataPoints, setDataPoints] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [hoveredIndex, setHoveredIndex] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                setError(null);
                const response = await getNumberOfDrivers();
                const vehicles = response?.data?.data || [];
                setDataPoints(
                    vehicles.map(v => {
                        // Format date as 'DD/MM'
                        let formattedDate = '';
                        if (v.date) {
                            const d = new Date(v.date);
                            formattedDate = `${d.getDate().toString().padStart(2, '0')}/${(d.getMonth() + 1).toString().padStart(2, '0')}`;
                        }
                        return {
                            drivers: v.number_of_drivers ?? 0,
                            date: formattedDate,
                        };
                    })
                );
            } catch (err) {
                setError('Failed to load driver growth data');
            } finally {
                setLoading(false);
            }
        };
        fetchData();
        const refreshInterval = (config.refreshInterval || 60) * 1000;
        const interval = setInterval(fetchData, refreshInterval);
        return () => clearInterval(interval);
    }, [config.refreshInterval]);

    // Graph dimensions
    const width = 340;
    const height = 140;
    const paddingLeft = 32;
    const paddingRight = 18;
    const paddingTop = 24;
    const paddingBottom = 38;
    const pointRadius = 5;

    // Prepare graph data
    const dates = dataPoints.map(d => d.date);
    const values = dataPoints.map(d => d.drivers);
    const minY = Math.min(...values, 0);
    const maxY = Math.max(...values, 10);

    // X/Y scales
    const xStep = (width - paddingLeft - paddingRight) / Math.max(dataPoints.length - 1, 1);
    const yScale = (height - paddingTop - paddingBottom) / (maxY - minY || 1);

    // SVG points
    const points = dataPoints.map((d, i) => {
        const x = paddingLeft + i * xStep;
        const y = height - paddingBottom - (d.drivers - minY) * yScale;
        return {x, y, value: d.drivers, date: d.date};
    });

    // Line path
    const linePath = points
        .map((p, i) => (i === 0 ? `M${p.x},${p.y}` : `L${p.x},${p.y}`))
        .join(' ');

    return (
        <BaseWidget
            id={id}
            title={config.title || 'Driver Growth'}
            loading={loading}
            error={error}
            className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-950 dark:to-blue-900"
        >
            <div className="flex flex-col items-center w-full">
                <div className="flex items-center gap-2 mb-1">
                    <LineChart className="w-5 h-5 text-blue-600 dark:text-blue-300" />
                    <span className="font-semibold text-blue-800 dark:text-blue-200 text-base">Driver Growth</span>
                </div>
                <div className="w-full flex justify-center items-center">
                    <svg
                        width={width}
                        height={height}
                        viewBox={`0 0 ${width} ${height}`}
                        className="block"
                        style={{maxWidth: '100%', height: 'auto'}}
                    >
                        {/* Axes */}
                        <line x1={paddingLeft} y1={height - paddingBottom} x2={width - paddingRight} y2={height - paddingBottom} stroke="#888" strokeWidth={1} />
                        <line x1={paddingLeft} y1={paddingTop} x2={paddingLeft} y2={height - paddingBottom} stroke="#888" strokeWidth={1} />
                        {/* Line */}
                        <path d={linePath} fill="none" stroke="#2563eb" strokeWidth={2} />
                        {/* Points */}
                        {points.map((p, i) => (
                            <circle
                                key={i}
                                cx={p.x}
                                cy={p.y}
                                r={pointRadius}
                                fill={hoveredIndex === i ? '#2563eb' : '#60a5fa'}
                                stroke="#2563eb"
                                strokeWidth={hoveredIndex === i ? 2 : 1}
                                onMouseEnter={() => setHoveredIndex(i)}
                                onMouseLeave={() => setHoveredIndex(null)}
                            />
                        ))}
                        {/* Hover tooltip: just the number */}
                        {hoveredIndex !== null && (
                            <g>
                                <rect
                                    x={Math.max(points[hoveredIndex].x - 18, paddingLeft)}
                                    y={Math.max(points[hoveredIndex].y - 32, paddingTop)}
                                    width={36}
                                    height={22}
                                    rx={5}
                                    fill="#fff"
                                    stroke="#2563eb"
                                    strokeWidth={1}
                                    opacity={0.95}
                                />
                                <text
                                    x={points[hoveredIndex].x}
                                    y={Math.max(points[hoveredIndex].y - 16, paddingTop + 12)}
                                    textAnchor="middle"
                                    fontSize={14}
                                    fill="#2563eb"
                                    fontWeight="bold"
                                >
                                    {points[hoveredIndex].value}
                                </text>
                            </g>
                        )}
                        {/* Date labels below x axis */}
                        {points.map((p, i) => (
                            <text
                                key={i}
                                x={p.x}
                                y={height - paddingBottom + 18}
                                textAnchor="middle"
                                fontSize={12}
                                fill="#444"
                                style={{pointerEvents: 'none'}}
                            >
                                {p.date}
                            </text>
                        ))}
                        {/* Axis labels */}
                        {/* Y axis label */}
                        <text
                            x={paddingLeft - 22}
                            y={height / 2}
                            textAnchor="middle"
                            fontSize={12}
                            fill="#2563eb"
                            fontWeight="bold"
                            transform={`rotate(-90,${paddingLeft - 22},${height / 2})`}
                        >
                            Number of Drivers
                        </text>
                        {/* X axis label */}
                        <text
                            x={width / 2}
                            y={height - 8}
                            textAnchor="middle"
                            fontSize={12}
                            fill="#2563eb"
                            fontWeight="bold"
                        >
                            Date (Day/Month)
                        </text>
                    </svg>
                </div>
            </div>
        </BaseWidget>
    );
};

registerWidget(WIDGET_TYPES.DRIVER_GROWTH_LINE_GRAPH, DriverGrowthLineGraphWidget, {
    title: 'Driver Growth Over Time',
    description: 'Line graph showing the number of drivers over time',
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
    maxSize: {w: 6, h: 3},
});
export default DriverGrowthLineGraphWidget;
