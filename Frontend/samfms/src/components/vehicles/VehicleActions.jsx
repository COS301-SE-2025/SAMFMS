import React from 'react';
import { Trash2 } from 'lucide-react';

const VehicleActions = ({
  selectedVehicles,
  onDeleteSelected,
}) => {
  return (
    <>
      {/* Main Actions */}
      <div className="mb-4 flex flex-col sm:flex-row gap-2">
        {/* No main action buttons left as per requirements */}
      </div>

      {/* Selected Vehicles Actions */}
      {selectedVehicles.length > 0 && (
        <div className="bg-accent/20 px-4 py-2 rounded-md mb-4 flex justify-between items-center">
          <span className="text-sm">{selectedVehicles.length} vehicles selected</span>
          <div className="flex gap-2">
            <button
              onClick={onDeleteSelected}
              className="text-sm text-destructive hover:text-destructive/80 flex items-center gap-1"
            >
              <Trash2 size={14} />
              Delete
            </button>
          </div>
        </div>
      )}
    </>
  );
};

export default VehicleActions;
