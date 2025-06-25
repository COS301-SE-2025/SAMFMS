import React, { useEffect, useState } from 'react';
import { getCostAnalytics } from '../../backend/api/analytics';

const CostAnalyticsCard = () => {
  const [stats, setStats] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    getCostAnalytics()
      .then(setStats)
      .catch(setError);
  }, []);

  if (error) return <div>Error loading cost analytics.</div>;
  if (!stats) return <div>Loading...</div>;

  return (
    <div className="analytics-card">
      <h3>Cost Analytics</h3>
      <table>
        <thead>
          <tr>
            <th>Vehicle ID</th>
            <th>Fuel Budget</th>
            <th>Insurance</th>
            <th>Maintenance</th>
          </tr>
        </thead>
        <tbody>
          {stats.map(row => (
            <tr key={row._id}>
              <td>{row._id}</td>
              <td>{row.fuel_budget}</td>
              <td>{row.insurance}</td>
              <td>{row.maintenance}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default CostAnalyticsCard;
