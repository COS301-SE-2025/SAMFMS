import React from 'react';

const DriverPerformanceCard = ({stats}) => {
  if (!stats || !stats.map) return <div>Loading...</div>;

  return (
    <div className="bg-card rounded-lg shadow-md p-6 border border-border mt-8">
      <h3 className="text-xl font-semibold mb-4">Driver Performance</h3>
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr className="bg-muted/50">
              <th className="py-3 px-4 text-left">Driver ID</th>
              <th className="py-3 px-4 text-left">Trips</th>
              <th className="py-3 px-4 text-left">Total Distance</th>
              <th className="py-3 px-4 text-left">Avg Distance</th>
              <th className="py-3 px-4 text-left">Incidents</th>
            </tr>
          </thead>
          <tbody>
            {stats.map(row => (
              <tr key={row._id} className="border-b border-border hover:bg-accent/10">
                <td className="py-3 px-4">{row._id}</td>
                <td className="py-3 px-4">{row.trip_count}</td>
                <td className="py-3 px-4">{row.total_distance}</td>
                <td className="py-3 px-4">{row.average_distance?.toFixed(2) ?? '0.00'}</td>
                <td className="py-3 px-4">{row.incident_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default DriverPerformanceCard;
