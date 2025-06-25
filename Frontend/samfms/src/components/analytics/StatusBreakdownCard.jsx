import React, { useEffect, useState } from 'react';
import { getStatusBreakdown } from '../../backend/api/analytics';

const StatusBreakdownCard = () => {
  const [stats, setStats] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    getStatusBreakdown()
      .then(setStats)
      .catch(setError);
  }, []);

  if (error) return <div>Error loading status breakdown.</div>;
  if (!stats) return <div>Loading...</div>;

  return (
    <div className="analytics-card">
      <h3>Vehicle Status Breakdown</h3>
      <table>
        <thead>
          <tr>
            <th>Status</th>
            <th>Count</th>
          </tr>
        </thead>
        <tbody>
          {stats.map(row => (
            <tr key={row._id}>
              <td>{row._id}</td>
              <td>{row.count}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default StatusBreakdownCard;
