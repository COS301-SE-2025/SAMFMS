import React, { useState } from 'react';
import { 
  LineChart, Line, AreaChart, Area, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
  PieChart, Pie, Cell, ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

const TripsAnalytics = ({ driverData, vehicleData, timeframe, onTimeframeChange }) => {
  const [chartType, setChartType] = useState('area');

  // Generate time series data from actual driver totals - no mock data
  const generateTimeSeriesData = () => {
    if (!driverData?.timeframeSummary?.totalTrips) {
      return [];
    }
    
    const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    const totalTrips = driverData.timeframeSummary.totalTrips;
    const avgPerDay = totalTrips / 7;
    const totalDistance = vehicleData?.timeframeSummary?.totalDistance || 0;
    const avgDistancePerDay = totalDistance / 7;
    
    return days.map((day, index) => {
      const dayTrips = Math.round(avgPerDay);
      const dayDistance = Math.round(avgDistancePerDay);
      
      return {
        day,
        trips: dayTrips,
        distance: dayDistance
      };
    });
  };

  const timeSeriesData = generateTimeSeriesData();

  // Generate pie chart data from actual completion rates - no mock data
  const generatePieChartData = () => {
    if (!driverData?.timeframeSummary?.completionRate) {
      return [];
    }

    const completionRate = driverData.timeframeSummary.completionRate;
    const cancelledRate = 100 - completionRate;
    
    const data = [
      { name: 'Completed', value: Math.round(completionRate), color: '#10b981' }
    ];
    
    if (cancelledRate > 0) {
      data.push({ name: 'Cancelled', value: Math.round(cancelledRate), color: '#ef4444' });
    }
    
    return data;
  };

  const pieChartData = generatePieChartData();

  const COLORS = ['#8b5cf6', '#06b6d4', '#10b981', '#f59e0b', '#ef4444'];

  const renderChart = () => {
    switch(chartType) {
      case 'area':
        return (
          <div className="h-80">
            <h3 className="font-medium mb-3 text-gray-800">Daily Trip Distribution</h3>
            {timeSeriesData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={timeSeriesData}>
                  <defs>
                    <linearGradient id="tripsGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0.1}/>
                    </linearGradient>
                    <linearGradient id="distanceGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="#06b6d4" stopOpacity={0.1}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="day" stroke="#64748b" />
                  <YAxis stroke="#64748b" />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#f8fafc', 
                      border: '1px solid #e2e8f0',
                      borderRadius: '8px',
                      boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
                    }} 
                  />
                  <Area type="monotone" dataKey="trips" stroke="#8b5cf6" fill="url(#tripsGradient)" strokeWidth={3} />
                  <Area type="monotone" dataKey="distance" stroke="#06b6d4" fill="url(#distanceGradient)" strokeWidth={3} />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-64 text-gray-500">
                No trip data available
              </div>
            )}
          </div>
        );

      case 'radar':
        return (
          <div className="h-80">
            <h3 className="font-medium mb-3 text-gray-800">Driver Performance Radar</h3>
            {driverData?.drivers?.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={driverData.drivers}>
                  <PolarGrid gridType="polygon" stroke="#e2e8f0" />
                  <PolarAngleAxis dataKey="driverName" tick={{ fontSize: 12, fill: '#64748b' }} />
                  <PolarRadiusAxis angle={90} domain={[0, 'dataMax']} tick={{ fontSize: 10, fill: '#64748b' }} />
                  <Radar 
                    name="Completed Trips" 
                    dataKey="completedTrips" 
                    stroke="#8b5cf6" 
                    fill="#8b5cf6" 
                    fillOpacity={0.3} 
                    strokeWidth={2} 
                  />
                  <Radar 
                    name="Cancelled Trips" 
                    dataKey="cancelledTrips" 
                    stroke="#ef4444" 
                    fill="#ef4444" 
                    fillOpacity={0.3} 
                    strokeWidth={2} 
                  />
                  <Tooltip />
                  <Legend />
                </RadarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-64 text-gray-500">
                No driver data available
              </div>
            )}
          </div>
        );

      case 'scatter':
        return (
          <div className="h-80">
            <h3 className="font-medium mb-3 text-gray-800">Vehicle Performance Matrix</h3>
            {vehicleData?.vehicles?.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <ScatterChart data={vehicleData.vehicles}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="totalTrips" name="Total Trips" stroke="#64748b" />
                  <YAxis dataKey="totalDistance" name="Total Distance" stroke="#64748b" />
                  <Tooltip 
                    cursor={{ strokeDasharray: '3 3' }}
                    contentStyle={{ 
                      backgroundColor: '#f8fafc', 
                      border: '1px solid #e2e8f0',
                      borderRadius: '8px' 
                    }}
                    formatter={(value, name) => [`${value}${name === 'Total Distance' ? ' km' : ''}`, name]}
                  />
                  <Scatter name="Vehicles" dataKey="totalDistance" fill="#8b5cf6">
                    {vehicleData.vehicles.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Scatter>
                </ScatterChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-64 text-gray-500">
                No vehicle data available
              </div>
            )}
          </div>
        );

      case 'donut':
        return (
          <div className="h-80">
            <h3 className="font-medium mb-3 text-gray-800">Trip Status Distribution</h3>
            {pieChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieChartData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={120}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {pieChartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip 
                    formatter={(value) => [`${value}%`, 'Percentage']}
                    contentStyle={{ 
                      backgroundColor: '#f8fafc', 
                      border: '1px solid #e2e8f0',
                      borderRadius: '8px' 
                    }}
                  />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-64 text-gray-500">
                No completion data available
              </div>
            )}
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 mb-6 border border-gray-200">
      {/* Header with Controls */}
      <div className="flex flex-wrap justify-between items-center mb-6 gap-4">
        <h2 className="text-2xl font-bold text-gray-800 dark:text-white">Trip Analytics Dashboard</h2>
        <div className="flex gap-3">
          <select
            value={timeframe}
            onChange={e => onTimeframeChange(e.target.value)}
            className="border border-gray-300 rounded-lg px-4 py-2 bg-white text-gray-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
          >
            <option value="week">Last Week</option>
            <option value="month">Last Month</option>
            <option value="year">Last Year</option>
          </select>
          <select
            value={chartType}
            onChange={e => setChartType(e.target.value)}
            className="border border-gray-300 rounded-lg px-4 py-2 bg-white text-gray-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
          >
            <option value="area">Area Chart</option>
            <option value="radar">Radar Chart</option>
            <option value="scatter">Scatter Plot</option>
            <option value="donut">Donut Chart</option>
          </select>
        </div>
      </div>

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-gradient-to-r from-purple-500 to-purple-600 rounded-lg p-4 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-purple-100">Total Trips</p>
              <p className="text-2xl font-bold">{driverData?.timeframeSummary?.totalTrips || 0}</p>
            </div>
          </div>
        </div>
        <div className="bg-gradient-to-r from-cyan-500 to-cyan-600 rounded-lg p-4 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-cyan-100">Completion Rate</p>
              <p className="text-2xl font-bold">{(driverData?.timeframeSummary?.completionRate || 0).toFixed(1)}%</p>
            </div>
          </div>
        </div>
        <div className="bg-gradient-to-r from-green-500 to-green-600 rounded-lg p-4 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-green-100">Avg Trips/Day</p>
              <p className="text-2xl font-bold">{(driverData?.timeframeSummary?.averageTripsPerDay || 0).toFixed(1)}</p>
            </div>
          </div>
        </div>
        <div className="bg-gradient-to-r from-orange-500 to-orange-600 rounded-lg p-4 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-orange-100">Total Distance</p>
              <p className="text-2xl font-bold">{(vehicleData?.timeframeSummary?.totalDistance || 0).toFixed(1)} km</p>
            </div>
          </div>
        </div>
      </div>

      {/* Dynamic Chart */}
      <div className="bg-gray-50 rounded-lg p-6">
        {renderChart()}
      </div>

      {/* Chart Type Description */}
      <div className="mt-4 p-4 bg-blue-50 rounded-lg border-l-4 border-blue-400">
        <div className="text-sm text-blue-700">
          {chartType === 'area' && "Area charts show daily distribution of trips and distance with smooth gradients"}
          {chartType === 'radar' && "Radar charts compare completed vs cancelled trips across all drivers"}
          {chartType === 'scatter' && "Scatter plots reveal relationships between trip count and distance by vehicle"}
          {chartType === 'donut' && "Donut charts provide clear percentage breakdown of trip completion rates"}
        </div>
      </div>
    </div>
  );
};

export default TripsAnalytics;