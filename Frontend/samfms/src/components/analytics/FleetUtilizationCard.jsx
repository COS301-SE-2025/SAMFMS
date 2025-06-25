import React, { useEffect, useState } from 'react';
import { getFleetUtilization } from '../../backend/api/analytics';

const FleetUtilizationCard = () => {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    getFleetUtilization()
      .then(setData)
      .catch(setError);
  }, []);

  if (error) return <div>Error loading fleet utilization.</div>;
  if (!data) return <div>Loading...</div>;

  return (
    <div className="analytics-card">
      <h3>Fleet Utilization</h3>
      <p>Total Vehicles: {data.total}</p>
      <p>In Use: {data.in_use}</p>
      <p>Utilization Rate: {(data.utilization_rate * 100).toFixed(1)}%</p>
    </div>
  );
};

export default FleetUtilizationCard;
