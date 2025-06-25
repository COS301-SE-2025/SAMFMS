import React, { useEffect, useState } from 'react';
import { getAssignmentMetrics } from '../../backend/api/analytics';

const AssignmentMetricsCard = () => {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    getAssignmentMetrics()
      .then(setData)
      .catch(setError);
  }, []);

  if (error) return <div>Error loading assignment metrics.</div>;
  if (!data) return <div>Loading...</div>;

  return (
    <div className="analytics-card">
      <h3>Assignment Metrics</h3>
      <p>Active Assignments: {data.active}</p>
      <p>Completed Assignments: {data.completed}</p>
      <p>Average Duration: {(data.average_duration_ms / (1000 * 60 * 60)).toFixed(2)} hours</p>
    </div>
  );
};

export default AssignmentMetricsCard;
