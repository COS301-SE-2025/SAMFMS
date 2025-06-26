import React from 'react';

const FleetUtilizationCard = ({data}) => {
  if (!data) return <div>Loading...</div>;

  return (
    <div className="bg-card rounded-lg shadow-md p-6 border border-border mt-8 max-w-md mx-auto">
      <h3 className="text-xl font-semibold mb-4">Fleet Utilization</h3>
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <tbody>
            <tr className="border-b border-border">
              <th className="py-3 px-4 text-left bg-muted/50 w-1/2">Total Vehicles</th>
              <td className="py-3 px-4">{data.total}</td>
            </tr>
            <tr className="border-b border-border">
              <th className="py-3 px-4 text-left bg-muted/50">In Use</th>
              <td className="py-3 px-4">{data.in_use}</td>
            </tr>
            <tr>
              <th className="py-3 px-4 text-left bg-muted/50">Utilization Rate</th>
              <td className="py-3 px-4">{(data.utilization_rate * 100).toFixed(1)}%</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default FleetUtilizationCard;
