import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

const DriverTripsChart = ({ data, timeframe }) => {
  // Expected data format:
  // [
  //   { driverName: "John Doe", completedTrips: 12, cancelledTrips: 1 },
  //   { driverName: "Jane Smith", completedTrips: 15, cancelledTrips: 0 },
  // ]

  return (
    <BarChart width={600} height={300} data={data}>
      <CartesianGrid strokeDasharray="3 3" />
      <XAxis dataKey="driverName" />
      <YAxis />
      <Tooltip />
      <Legend />
      <Bar dataKey="completedTrips" fill="#82ca9d" name="Completed Trips" />
      <Bar dataKey="cancelledTrips" fill="#ff8042" name="Cancelled Trips" />
    </BarChart>
  );
};

export default DriverTripsChart;