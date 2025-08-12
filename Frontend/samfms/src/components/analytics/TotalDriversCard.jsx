import React from 'react';

const TotalDriversCard = ({data}) => {
  if (!data) return <div className="bg-card rounded-lg shadow-md p-6 border border-border mt-8 max-w-md mx-auto">
  <h3 className="text-xl font-semibold mb-4">Total Drivers</h3>
  <div className="overflow-x-auto">
    <table className="w-full border-collapse">
      <tbody>
        <tr className="border-b border-border">
          <th className="py-3 px-4 text-left bg-muted/50 w-1/2">Total Drivers</th>
          <td className="py-3 px-4">{"Error"}</td>
        </tr>
      </tbody>
    </table>
  </div>
</div>;

  return (
    <div className="bg-card rounded-lg shadow-md p-6 border border-border mt-8 max-w-md mx-auto">
      <h3 className="text-xl font-semibold mb-4">Total Drivers</h3>
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <tbody>
            <tr className="border-b border-border">
              <th className="py-3 px-4 text-left bg-muted/50 w-1/2">Total Drivers</th>
              <td className="py-3 px-4">{data.total}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default TotalDriversCard;
