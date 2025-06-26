import React from 'react';

const StatusBreakdownCard = ({stats}) => {
  if (!stats) return <div>Loading...</div>;

  return (
    <div className="bg-card rounded-lg shadow-md p-6 border border-border mt-8 max-w-md mx-auto">
      <h3 className="text-xl font-semibold mb-4">Vehicle Status Breakdown</h3>
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr className="bg-muted/50">
              <th className="py-3 px-4 text-left">Status</th>
              <th className="py-3 px-4 text-left">Count</th>
            </tr>
          </thead>
          <tbody>
            {stats.map(row => (
              <tr key={row._id} className="border-b border-border hover:bg-accent/10">
                <td className="py-3 px-4">{row._id}</td>
                <td className="py-3 px-4">{row.count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default StatusBreakdownCard;
