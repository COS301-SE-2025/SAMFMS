import React from 'react';
import { Download, UserPlus, Trash2 } from 'lucide-react';

const DriverActions = ({ selectedDrivers, exportSelectedDrivers, onDeleteSelected }) => {
  return (
    <div className="mb-6">
      {selectedDrivers.length > 0 ? (
        <div className="flex gap-2 items-center animate-in fade-in-0 slide-in-from-top-5 duration-150">
          <span className="text-sm font-medium">{selectedDrivers.length} drivers selected</span>
          <button
            onClick={exportSelectedDrivers}
            className="flex items-center gap-1 text-sm px-3 py-1.5 border border-input rounded-md hover:bg-accent hover:text-accent-foreground"
          >
            <Download size={16} />
            Export
          </button>
          <button className="flex items-center gap-1 text-sm px-3 py-1.5 border border-input rounded-md hover:bg-accent hover:text-accent-foreground">
            <UserPlus size={16} />
            Assign Vehicle
          </button>
          <button
            onClick={onDeleteSelected}
            className="flex items-center gap-1 text-sm px-3 py-1.5 border border-destructive text-destructive rounded-md hover:bg-destructive/10"
          >
            <Trash2 size={16} />
            Delete
          </button>
        </div>
      ) : null}
    </div>
  );
};

export default DriverActions;
