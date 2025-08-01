import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

const TripsAnalytics = ({ 
  driverData, 
  vehicleData, 
  timeframe, 
  onTimeframeChange 
}) => {
  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold">Trip Analytics</h2>
        <select 
          value={timeframe} 
          onChange={(e) => onTimeframeChange(e.target.value)}
          className="border rounded-md px-3 py-1"
        >
          <option value="week">Last Week</option>
          <option value="month">Last Month</option>
          <option value="year">Last Year</option>
        </select>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Driver Analytics */}
        <div>
          <h3 className="font-medium mb-3">Driver Performance</h3>
          <div className="mb-4">
            <p className="text-sm text-gray-600">
              Total Trips: {driverData?.timeframeSummary?.totalTrips || 0}
            </p>
            <p className="text-sm text-gray-600">
              Completion Rate: {(driverData?.timeframeSummary?.completionRate || 0).toFixed(1)}%
            </p>
            <p className="text-sm text-gray-600">
              Avg Trips/Day: {(driverData?.timeframeSummary?.averageTripsPerDay || 0).toFixed(1)}
            </p>
          </div>
          <BarChart width={400} height={300} data={driverData?.drivers || []}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="driverName" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="completedTrips" fill="#82ca9d" name="Completed Trips" />
            <Bar dataKey="cancelledTrips" fill="#ff8042" name="Cancelled Trips" />
          </BarChart>
        </div>

        {/* Vehicle Analytics */}
        <div>
          <h3 className="font-medium mb-3">Vehicle Usage</h3>
          <div className="mb-4">
            <p className="text-sm text-gray-600">
              Total Distance: {(vehicleData?.timeframeSummary?.totalDistance || 0).toFixed(1)} km
            </p>
          </div>
          <BarChart width={400} height={300} data={vehicleData?.vehicles || []}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="vehicleName" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="totalTrips" fill="#8884d8" name="Total Trips" />
            <Bar dataKey="totalDistance" fill="#82ca9d" name="Distance (km)" />
          </BarChart>
        </div>
      </div>
    </div>
  );
};

export default TripsAnalytics;