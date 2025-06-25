import React, { useEffect, useState } from 'react';
import { getVehicleUsage } from '../../backend/api/analytics';

const VehicleUsageStats = () => {
  const [stats, setStats] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    getVehicleUsage()
      .then(setStats)
      .catch(setError);
  }, []);

  if (error) return <div>Error loading vehicle usage stats.</div>;
  if (!stats) return <div>Loading...</div>;

  return (
    <div className="analytics-card">
      <h3>Vehicle Usage Statistics</h3>
      <table>
        <thead>
          <tr>
            <th>Vehicle ID</th>
            <th>Total Distance (km)</th>
            <th>Total Fuel</th>
            <th>Trips</th>
            <th>Avg Trip Length</th>
          </tr>
        </thead>
        <tbody>
          {stats.map(row => (
            <tr key={row._id}>
              <td>{row._id}</td>
              <td>{row.total_distance}</td>
              <td>{row.total_fuel}</td>
              <td>{row.trip_count}</td>
              <td>{row.average_trip_length.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default VehicleUsageStats;
