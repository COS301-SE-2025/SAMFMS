import React from 'react';
import {PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer} from 'recharts';

const COLORS = [
    '#2563eb', // blue-600
    '#22c55e', // green-500
    '#f59e42', // amber-400
    '#ef4444', // red-500
    '#a21caf', // purple-700
    '#eab308', // yellow-500
    '#0ea5e9', // sky-500
    '#f472b6', // pink-400
];

const StatusBreakdownPieChart = ({stats}) => {

    if (!stats || stats.length === 0) {
        return (
            <div className="bg-card rounded-lg border border-border p-6 mt-8 text-center">
                <span className="text-muted-foreground">No status data available.</span>
            </div>
        );
    }

    const chartData = stats.map((item, idx) => ({
        name: item._id,
        value: item.count,
        color: COLORS[idx % COLORS.length],
    }));

    return (
        <div className="bg-card rounded-lg border border-border p-6 mt-8">
            <h2 className="text-xl font-semibold mb-4">Vehicle Status Breakdown</h2>
            <div style={{width: '100%', height: 300}}>
                <ResponsiveContainer>
                    <PieChart>
                        <Pie
                            data={chartData}
                            dataKey="value"
                            nameKey="name"
                            cx="50%"
                            cy="50%"
                            outerRadius={90}
                            label
                        >
                            {chartData.map((entry, idx) => (
                                <Cell key={`cell-${idx}`} fill={entry.color} />
                            ))}
                        </Pie>
                        <Tooltip />
                        <Legend />
                    </PieChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

export default StatusBreakdownPieChart;