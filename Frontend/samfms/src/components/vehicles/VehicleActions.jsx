import React from 'react';
import { Users, Download, Upload, FileText, Tag, Trash2 } from 'lucide-react';

const VehicleActions = ({ selectedVehicles, openAssignmentModal, exportSelectedVehicles }) => {
  return (
    <>
      {/* Main Actions */}
      <div className="mb-4 flex flex-col sm:flex-row gap-2">
        {' '}
        <button
          onClick={openAssignmentModal}
          className="flex items-center gap-2 px-3 py-1.5 border border-border rounded-md hover:bg-accent/20 transition"
        >
          <Users size={16} />
          <span>Assign Drivers</span>
        </button>
        <button
          onClick={exportSelectedVehicles}
          className="flex items-center gap-2 px-3 py-1.5 border border-border rounded-md hover:bg-accent/20 transition"
        >
          <Download size={16} />
          <span>Export</span>
        </button>
        <button className="flex items-center gap-2 px-3 py-1.5 border border-border rounded-md hover:bg-accent/20 transition">
          <Upload size={16} />
          <span>Import</span>
        </button>
        <button className="flex items-center gap-2 px-3 py-1.5 border border-border rounded-md hover:bg-accent/20 transition">
          <FileText size={16} />
          <span>Report</span>
        </button>
      </div>

      {/* Selected Vehicles Actions */}
      {selectedVehicles.length > 0 && (
        <div className="bg-accent/20 px-4 py-2 rounded-md mb-4 flex justify-between items-center">
          <span className="text-sm">{selectedVehicles.length} vehicles selected</span>
          <div className="flex gap-2">
            <button
              onClick={openAssignmentModal}
              className="text-sm text-primary hover:text-primary/80 flex items-center gap-1"
            >
              <Users size={14} />
              Assign Driver
            </button>
            <button className="text-sm text-primary hover:text-primary/80 flex items-center gap-1">
              <Tag size={14} />
              Add Tag
            </button>
            <button className="text-sm text-destructive hover:text-destructive/80 flex items-center gap-1">
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
