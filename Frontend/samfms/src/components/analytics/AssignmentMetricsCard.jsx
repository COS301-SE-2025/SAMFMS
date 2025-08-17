import React from 'react';

const AssignmentMetricsCard = ({data}) => {
  if (!data) return <div>Loading...</div>;

  return (
    <div className="bg-card rounded-lg shadow-md p-6 border border-border mt-8 max-w-md mx-auto">
      <h3 className="text-xl font-semibold mb-4">Assignment Metrics</h3>
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <tbody>
            <tr className="border-b border-border">
              <th className="py-3 px-4 text-left bg-muted/50 w-1/2">Active Assignments</th>
              <td className="py-3 px-4">{data.active_assignments}</td>
            </tr>
            <tr className="border-b border-border">
              <th className="py-3 px-4 text-left bg-muted/50">Completed Assignments</th>
              <td className="py-3 px-4">{data.completed_assignments}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default AssignmentMetricsCard;

