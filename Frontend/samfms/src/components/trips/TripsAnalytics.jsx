import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

const TripsAnalytics = ({ driverData, vehicleData, timeframe, onTimeframeChange }) => {
  return (
    <div className="bg-card dark:bg-card rounded-lg shadow-md p-6 mb-6 border border-border">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-foreground">Trip Analytics</h2>
        <select
          value={timeframe}
          onChange={e => onTimeframeChange(e.target.value)}
          className="border border-input rounded-md px-3 py-1 bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
        >
          <option value="week">Last Week</option>
          <option value="month">Last Month</option>
          <option value="year">Last Year</option>
        </select>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Driver Analytics */}
        <div>
          <h3 className="font-medium mb-3 text-foreground">Driver Performance</h3>
          <div className="mb-4">
            <p className="text-sm text-muted-foreground">
              Total Trips: {driverData?.timeframeSummary?.totalTrips || 0}
            </p>
            <p className="text-sm text-muted-foreground">
              Completion Rate: {(driverData?.timeframeSummary?.completionRate || 0).toFixed(1)}%
            </p>
            <p className="text-sm text-muted-foreground">
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
          <h3 className="font-medium mb-3 text-foreground">Vehicle Usage</h3>
          <div className="mb-4">
            <p className="text-sm text-muted-foreground">
              Total Distance: {(vehicleData?.timeframeSummary?.totalDistance || 0).toFixed(1)} km
            </p>
          </div>
          <BarChart width={400} height={300} data={vehicleData?.vehicles || []}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="vehicleName" />
            <YAxis yAxisId="left" orientation="left" />
            <YAxis yAxisId="right" orientation="right" />
            <Tooltip />
            <Legend />
            <Bar yAxisId="left" dataKey="totalTrips" fill="#8884d8" name="Total Trips" />
            <Bar yAxisId="right" dataKey="totalDistance" fill="#82ca9d" name="Distance (km)" />
          </BarChart>
        </div>
      </div>
    </div>
  );
};

export default TripsAnalytics;
