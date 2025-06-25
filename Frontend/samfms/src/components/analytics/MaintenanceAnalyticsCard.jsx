import React, { useEffect, useState } from 'react';
import { getMaintenanceAnalytics } from '../../backend/api/analytics';

const MaintenanceAnalyticsCard = () => {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    getMaintenanceAnalytics()
      .then(setData)
      .catch(setError);
  }, []);

  if (error) return <div>Error loading maintenance analytics.</div>;
  if (!data) return <div>Loading...</div>;

  return (
    <div className="analytics-card">
      <h3>Maintenance Analytics</h3>
      <p>Vehicles in Maintenance: {data.in_maintenance}</p>
      <p>Maintenance Frequency: {data.maintenance_frequency}</p>
      <p>Average Duration: {(data.average_duration_ms / (1000 * 60 * 60)).toFixed(2)} hours</p>
    </div>
  );
};

export default MaintenanceAnalyticsCard;
