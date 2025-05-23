import React from 'react';

const Trips = () => {
  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Trip Management</h1>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <div className="bg-card rounded-lg shadow-md p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-semibold">Active & Scheduled Trips</h2>
              <button className="bg-primary text-primary-foreground px-4 py-2 rounded-md hover:bg-primary/90 transition">
                Schedule New Trip
              </button>
            </div>
            
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left py-3 px-4">Trip ID</th>
                    <th className="text-left py-3 px-4">Vehicle</th>
                    <th className="text-left py-3 px-4">Driver</th>
                    <th className="text-left py-3 px-4">Departure</th>
                    <th className="text-left py-3 px-4">Status</th>
                    <th className="text-left py-3 px-4">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b border-border hover:bg-accent/10">
                    <td className="py-3 px-4">T-1001</td>
                    <td className="py-3 px-4">Toyota Camry (VEH-001)</td>
                    <td className="py-3 px-4">John Smith</td>
                    <td className="py-3 px-4">May 23, 2025 - 10:30 AM</td>
                    <td className="py-3 px-4">
                      <span className="bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 py-1 px-2 rounded-full text-xs">
                        In Progress
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <button className="text-primary hover:text-primary/80">Details</button>
                    </td>
                  </tr>
                  <tr className="border-b border-border hover:bg-accent/10">
                    <td className="py-3 px-4">T-1002</td>
                    <td className="py-3 px-4">Ford Transit (VEH-002)</td>
                    <td className="py-3 px-4">Jane Wilson</td>
                    <td className="py-3 px-4">May 24, 2025 - 08:00 AM</td>
                    <td className="py-3 px-4">
                      <span className="bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200 py-1 px-2 rounded-full text-xs">
                        Scheduled
                      </span>
                    </td>
                    <td className="py-3 px-4 space-x-2">
                      <button className="text-primary hover:text-primary/80">Details</button>
                      <button className="text-destructive hover:text-destructive/80">Cancel</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
        
        <div className="lg:col-span-1">
          <div className="bg-card rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4">Trip Statistics</h2>
            
            <div className="space-y-4">
              <div className="p-4 bg-accent/10 rounded-md">
                <p className="text-sm text-muted-foreground">Active Trips</p>
                <p className="text-2xl font-bold">3</p>
              </div>
              
              <div className="p-4 bg-accent/10 rounded-md">
                <p className="text-sm text-muted-foreground">Scheduled Trips</p>
                <p className="text-2xl font-bold">5</p>
              </div>
              
              <div className="p-4 bg-accent/10 rounded-md">
                <p className="text-sm text-muted-foreground">Completed (This Month)</p>
                <p className="text-2xl font-bold">24</p>
              </div>
              
              <div className="p-4 bg-accent/10 rounded-md">
                <p className="text-sm text-muted-foreground">Average Trip Duration</p>
                <p className="text-2xl font-bold">3.5 hrs</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Trips;
