import React from 'react';

const Drivers = () => {
  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Fleet Drivers</h1>
      
      <div className="bg-card rounded-lg shadow-md p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold">Manage Drivers</h2>
          <button className="bg-primary text-primary-foreground px-4 py-2 rounded-md hover:bg-primary/90 transition">
            Add New Driver
          </button>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left py-3 px-4">Driver ID</th>
                <th className="text-left py-3 px-4">Name</th>
                <th className="text-left py-3 px-4">License #</th>
                <th className="text-left py-3 px-4">Phone</th>
                <th className="text-left py-3 px-4">Status</th>
                <th className="text-left py-3 px-4">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-border hover:bg-accent/10">
                <td className="py-3 px-4">DRV-001</td>
                <td className="py-3 px-4">John Smith</td>
                <td className="py-3 px-4">DL8976543</td>
                <td className="py-3 px-4">(555) 123-4567</td>
                <td className="py-3 px-4">
                  <span className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 py-1 px-2 rounded-full text-xs">
                    Available
                  </span>
                </td>
                <td className="py-3 px-4 space-x-2">
                  <button className="text-primary hover:text-primary/80">Edit</button>
                  <button className="text-destructive hover:text-destructive/80">Remove</button>
                </td>
              </tr>
              <tr className="border-b border-border hover:bg-accent/10">
                <td className="py-3 px-4">DRV-002</td>
                <td className="py-3 px-4">Jane Wilson</td>
                <td className="py-3 px-4">DL7651234</td>
                <td className="py-3 px-4">(555) 987-6543</td>
                <td className="py-3 px-4">
                  <span className="bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 py-1 px-2 rounded-full text-xs">
                    On Trip
                  </span>
                </td>
                <td className="py-3 px-4 space-x-2">
                  <button className="text-primary hover:text-primary/80">Edit</button>
                  <button className="text-destructive hover:text-destructive/80">Remove</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Drivers;
