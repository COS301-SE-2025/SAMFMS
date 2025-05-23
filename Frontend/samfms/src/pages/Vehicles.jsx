import React from 'react';

const Vehicles = () => {
  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Fleet Vehicles</h1>
      
      <div className="bg-card rounded-lg shadow-md p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold">Manage Vehicles</h2>
          <button className="bg-primary text-primary-foreground px-4 py-2 rounded-md hover:bg-primary/90 transition">
            Add New Vehicle
          </button>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left py-3 px-4">Vehicle ID</th>
                <th className="text-left py-3 px-4">Make</th>
                <th className="text-left py-3 px-4">Model</th>
                <th className="text-left py-3 px-4">Year</th>
                <th className="text-left py-3 px-4">Status</th>
                <th className="text-left py-3 px-4">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-border hover:bg-accent/10">
                <td className="py-3 px-4">VEH-001</td>
                <td className="py-3 px-4">Toyota</td>
                <td className="py-3 px-4">Camry</td>
                <td className="py-3 px-4">2023</td>
                <td className="py-3 px-4">
                  <span className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 py-1 px-2 rounded-full text-xs">
                    Active
                  </span>
                </td>
                <td className="py-3 px-4 space-x-2">
                  <button className="text-primary hover:text-primary/80">Edit</button>
                  <button className="text-destructive hover:text-destructive/80">Remove</button>
                </td>
              </tr>
              <tr className="border-b border-border hover:bg-accent/10">
                <td className="py-3 px-4">VEH-002</td>
                <td className="py-3 px-4">Ford</td>
                <td className="py-3 px-4">Transit</td>
                <td className="py-3 px-4">2022</td>
                <td className="py-3 px-4">
                  <span className="bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200 py-1 px-2 rounded-full text-xs">
                    Maintenance
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

export default Vehicles;
