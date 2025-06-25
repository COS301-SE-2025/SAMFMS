import React, { useEffect, useState } from 'react';
import { getDriverPerformance } from '../../backend/api/analytics';

const DriverPerformanceCard = () => {
  const [stats, setStats] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    getDriverPerformance()
      .then(setStats)
      .catch(setError);
  }, []);

  if (error) return <div>Error loading driver performance.</div>;
  if (!stats) return <div>Loading...</div>;

  return (
    <div className="analytics-card">
      <h3>Driver Performance</h3>
      <table>
        <thead>
          <tr>
            <th>Driver ID</th>
            <th>Trips</th>
            <th>Total Distance</th>
            <th>Avg Distance</th>
            <th>Incidents</th>
          </tr>
        </thead>
        <tbody>
          {stats.map(row => (
            <tr key={row._id}>
              <td>{row._id}</td>
              <td>{row.trip_count}</td>
              <td>{row.total_distance}</td>
              <td>{row.average_distance.toFixed(2)}</td>
              <td>{row.incident_count}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default DriverPerformanceCard;
