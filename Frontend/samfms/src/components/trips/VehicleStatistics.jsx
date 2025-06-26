import React from 'react';
import { Car, Clock } from 'lucide-react';

const VehicleStatistics = ({ stats }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
      <div className="bg-card rounded-lg shadow-sm p-4 border border-border flex items-center">
        <div className="rounded-full bg-green-100 dark:bg-green-900 p-3 mr-4">
          <Car className="h-6 w-6 text-green-600 dark:text-green-300" />
        </div>
        <div>
          <p className="text-sm text-muted-foreground">Active Vehicles</p>
          <div className="flex items-baseline">
            <p className="text-2xl font-bold">{stats.activeVehicles}</p>
            <p className="text-sm text-muted-foreground ml-2">vehicles</p>
          </div>
        </div>
      </div>

      <div className="bg-card rounded-lg shadow-sm p-4 border border-border flex items-center">
        <div className="rounded-full bg-blue-100 dark:bg-blue-900 p-3 mr-4">
          <Clock className="h-6 w-6 text-blue-600 dark:text-blue-300" />
        </div>
        <div>
          <p className="text-sm text-muted-foreground">Idle Vehicles</p>
          <div className="flex items-baseline">
            <p className="text-2xl font-bold">{stats.idleVehicles}</p>
            <p className="text-sm text-muted-foreground ml-2">vehicles</p>
          </div>
        </div>
      </div>

      {/* <div className="bg-card rounded-lg shadow-sm p-4 border border-border flex items-center">
        <div className="rounded-full bg-red-100 dark:bg-red-900 p-3 mr-4">
          <AlertTriangle className="h-6 w-6 text-red-600 dark:text-red-300" />
        </div>
        <div>
          <p className="text-sm text-muted-foreground">Non-operational</p>
          <div className="flex items-baseline">
            <p className="text-2xl font-bold">{stats.nonOperationalVehicles}</p>
            <p className="text-sm text-muted-foreground ml-2">vehicles</p>
          </div>
        </div>
      </div> */}
    </div>
  );
};

export default VehicleStatistics;
