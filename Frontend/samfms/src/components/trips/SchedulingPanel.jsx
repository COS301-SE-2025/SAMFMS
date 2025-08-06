import React from 'react';

const SchedulingPanel = ({availableVehicles, availableDrivers, onScheduleClick}) => {
  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold">Schedule New Trip</h2>
        <div className="flex gap-4">
          <div className="text-sm">
            <span className="font-medium">Available Vehicles:</span> {availableVehicles}
          </div>
          <div className="text-sm">
            <span className="font-medium">Available Drivers:</span> {availableDrivers}
          </div>
        </div>
      </div>
      <button
        onClick={onScheduleClick}
        className="bg-primary text-white px-4 py-2 rounded-md hover:bg-primary/90"
      >
        Schedule New Trip
      </button>
    </div>
  );
};

export default SchedulingPanel;