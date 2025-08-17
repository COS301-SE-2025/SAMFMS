import React from 'react';

const SchedulingPanel = ({ availableVehicles, availableDrivers, onScheduleClick }) => {
  return (
    <div className="bg-card dark:bg-card rounded-lg shadow-md p-6 mb-6 border border-border">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-foreground">Schedule New Trip</h2>
        <div className="flex gap-4">
          <div className="text-sm">
            <span className="font-medium text-foreground">Available Vehicles:</span>{' '}
            <span className="text-muted-foreground">{availableVehicles}</span>
          </div>
          <div className="text-sm">
            <span className="font-medium text-foreground">Available Drivers:</span>{' '}
            <span className="text-muted-foreground">{availableDrivers}</span>
          </div>
        </div>
      </div>
      <button
        onClick={onScheduleClick}
        className="bg-primary text-primary-foreground px-4 py-2 rounded-md hover:bg-primary/90 transition-colors"
      >
        Schedule New Trip
      </button>
    </div>
  );
};

export default SchedulingPanel;
