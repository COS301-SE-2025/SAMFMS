import React from 'react';

const VehicleUsageStats = ({stats}) => {
  if (!stats) return <div>Loading...</div>;

  return (
    <div className="bg-card rounded-lg shadow-md p-6 border border-border mt-8">
      <h3 className="text-xl font-semibold mb-4">Vehicle Usage Statistics</h3>
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr className="bg-muted/50">
              <th className="py-3 px-4 text-left">Vehicle ID</th>
              <th className="py-3 px-4 text-left">Total Distance (km)</th>
              <th className="py-3 px-4 text-left">Total Fuel</th>
              <th className="py-3 px-4 text-left">Trips</th>
              <th className="py-3 px-4 text-left">Avg Trip Length</th>
            </tr>
          </thead>
          <tbody>
            {stats.map(row => (
              <tr key={row._id} className="border-b border-border hover:bg-accent/10">
                <td className="py-3 px-4">{row._id}</td>
                <td className="py-3 px-4">{row.total_distance}</td>
                <td className="py-3 px-4">{row.total_fuel}</td>
                <td className="py-3 px-4">{row.trip_count}</td>
                <td className="py-3 px-4">{row.average_trip_length?.toFixed(2) ?? '0.00'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default VehicleUsageStats;
