import React from 'react';

const ActiveTripsPanel = ({ activeTrips }) => {
  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <h2 className="text-xl font-semibold mb-4">Active Trips</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {activeTrips?.map(trip => (
          <div 
            key={trip.id} 
            className={`border rounded-md p-4 ${
              trip.status === 'delayed' ? 'border-red-300 bg-red-50' :
              trip.status === 'on_time' ? 'border-green-300 bg-green-50' :
              'border-gray-300'
            }`}
          >
            <h3 className="font-medium">{trip.name}</h3>
            <p className="text-sm text-gray-600">Started: {new Date(trip.startTime).toLocaleString()}</p>
            <p className="text-sm text-gray-600">ETA: {new Date(trip.estimatedEndTime).toLocaleString()}</p>
            <p className="text-sm text-gray-600">Scheduled: {new Date(trip.scheduledEndTime).toLocaleString()}</p>
            <div className="mt-2 flex justify-between items-center">
              <span className="text-sm">Driver: {trip.driver.name}</span>
              <span className={`text-sm px-2 py-1 rounded-full ${
                trip.status === 'delayed' ? 'bg-red-200 text-red-800' :
                trip.status === 'on_time' ? 'bg-green-200 text-green-800' :
                'bg-gray-200 text-gray-800'
              }`}>
                {trip.status.replace('_', ' ').toUpperCase()}
              </span>
            </div>
          </div>
        ))}
        {!activeTrips?.length && (
          <div className="col-span-full text-center text-gray-500">
            No active trips
          </div>
        )}
      </div>
    </div>
  );
};

export default ActiveTripsPanel;