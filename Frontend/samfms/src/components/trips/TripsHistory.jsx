import React from 'react';

const TripsHistory = ({trips}) => {
  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-semibold mb-4">Trip History</h2>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b">
              <th className="text-left py-3 px-4">Trip Name</th>
              <th className="text-left py-3 px-4">Driver</th>
              <th className="text-left py-3 px-4">Vehicle</th>
              <th className="text-left py-3 px-4">Start Time</th>
              <th className="text-left py-3 px-4">End Time</th>
              <th className="text-left py-3 px-4">Status</th>
            </tr>
          </thead>
          <tbody>
            {trips?.map(trip => (
              <tr key={trip.id} className="border-b">
                <td className="py-3 px-4">{trip.name}</td>
                <td className="py-3 px-4">{trip.driver}</td>
                <td className="py-3 px-4">{trip.vehicle}</td>
                <td className="py-3 px-4">{trip.startTime}</td>
                <td className="py-3 px-4">{trip.endTime}</td>
                <td className="py-3 px-4">{trip.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default TripsHistory;