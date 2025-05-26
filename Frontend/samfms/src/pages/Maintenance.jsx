import React from 'react';

const Maintenance = () => {
  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Vehicle Maintenance</h1>
      
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-3">
          <div className="bg-card rounded-lg shadow-md p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-semibold">Maintenance Schedule</h2>
              <button className="bg-primary text-primary-foreground px-4 py-2 rounded-md hover:bg-primary/90 transition">
                Schedule Maintenance
              </button>
            </div>
            
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left py-3 px-4">ID</th>
                    <th className="text-left py-3 px-4">Vehicle</th>
                    <th className="text-left py-3 px-4">Service Type</th>
                    <th className="text-left py-3 px-4">Due Date</th>
                    <th className="text-left py-3 px-4">Status</th>
                    <th className="text-left py-3 px-4">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b border-border hover:bg-accent/10">
                    <td className="py-3 px-4">M-2001</td>
                    <td className="py-3 px-4">Toyota Camry (VEH-001)</td>
                    <td className="py-3 px-4">Oil Change</td>
                    <td className="py-3 px-4">June 15, 2025</td>
                    <td className="py-3 px-4">
                      <span className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 py-1 px-2 rounded-full text-xs">
                        Scheduled
                      </span>
                    </td>
                    <td className="py-3 px-4 space-x-2">
                      <button className="text-primary hover:text-primary/80">Edit</button>
                      <button className="text-blue-600 hover:text-blue-700">Complete</button>
                    </td>
                  </tr>
                  <tr className="border-b border-border hover:bg-accent/10">
                    <td className="py-3 px-4">M-2002</td>
                    <td className="py-3 px-4">Ford Transit (VEH-002)</td>
                    <td className="py-3 px-4">Brake Service</td>
                    <td className="py-3 px-4">May 25, 2025</td>
                    <td className="py-3 px-4">
                      <span className="bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200 py-1 px-2 rounded-full text-xs">
                        In Progress
                      </span>
                    </td>
                    <td className="py-3 px-4 space-x-2">
                      <button className="text-primary hover:text-primary/80">Edit</button>
                      <button className="text-blue-600 hover:text-blue-700">Complete</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
        
        <div className="lg:col-span-1">
          <div className="bg-card rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4">Maintenance Alerts</h2>
            
            <div className="space-y-4">
              <div className="p-3 border-l-4 border-red-500 bg-red-50 dark:bg-red-950/20 rounded-r-md">
                <p className="font-medium">Urgent: Brake Inspection</p>
                <p className="text-sm text-muted-foreground mt-1">VEH-003: Due overdue by 2 days</p>
              </div>
              
              <div className="p-3 border-l-4 border-yellow-500 bg-yellow-50 dark:bg-yellow-950/20 rounded-r-md">
                <p className="font-medium">Upcoming: Oil Change</p>
                <p className="text-sm text-muted-foreground mt-1">VEH-001: Due in 5 days</p>
              </div>
              
              <div className="p-3 border-l-4 border-yellow-500 bg-yellow-50 dark:bg-yellow-950/20 rounded-r-md">
                <p className="font-medium">Upcoming: Tire Rotation</p>
                <p className="text-sm text-muted-foreground mt-1">VEH-002: Due in 7 days</p>
              </div>
              
              <div className="p-3 border-l-4 border-blue-500 bg-blue-50 dark:bg-blue-950/20 rounded-r-md">
                <p className="font-medium">Reminder: Annual Inspection</p>
                <p className="text-sm text-muted-foreground mt-1">VEH-001: Due in 30 days</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Maintenance;
