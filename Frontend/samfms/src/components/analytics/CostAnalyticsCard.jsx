import React from 'react';

const CostAnalyticsCard = ({stats}) => {
  if (!stats || !stats.map) return <div>Loading...</div>;

  return (
    <div className="bg-card rounded-lg shadow-md p-6 border border-border mt-8">
      <h3 className="text-xl font-semibold mb-4">Cost Analytics</h3>
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr className="bg-muted/50">
              <th className="py-3 px-4 text-left">Vehicle ID</th>
              <th className="py-3 px-4 text-left">Fuel Budget</th>
              <th className="py-3 px-4 text-left">Insurance</th>
              <th className="py-3 px-4 text-left">Maintenance</th>
            </tr>
          </thead>
          <tbody>
            {stats.map(row => (
              <tr key={row._id} className="border-b border-border hover:bg-accent/10">
                <td className="py-3 px-4">{row._id}</td>
                <td className="py-3 px-4">{row.fuel_budget}</td>
                <td className="py-3 px-4">{row.insurance}</td>
                <td className="py-3 px-4">{row.maintenance}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default CostAnalyticsCard;
