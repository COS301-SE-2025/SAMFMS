import React from 'react';

const Tracking = () => {
  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Vehicle Tracking</h1>
      
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-3">
          <div className="bg-card rounded-lg shadow-md p-4 h-[600px] flex items-center justify-center">
            {/* This would be replaced with an actual map component */}
            <div className="text-center">
              <div className="text-4xl mb-4">🗺️</div>
              <p className="text-muted-foreground">
                Interactive map would be displayed here showing vehicle locations
              </p>
              <p className="text-xs text-muted-foreground mt-2">
                Map integration with location services would be implemented here
              </p>
            </div>
          </div>
        </div>
        
        <div className="lg:col-span-1">
          <div className="bg-card rounded-lg shadow-md p-4">
            <h2 className="text-xl font-semibold mb-4">Vehicle Status</h2>
            
            <div className="space-y-4">
              <div className="p-3 border border-border rounded-md">
                <div className="flex justify-between">
                  <span className="font-medium">VEH-001</span>
                  <span className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 py-1 px-2 rounded-full text-xs">
                    Active
                  </span>
                </div>
                <p className="text-sm text-muted-foreground mt-1">Toyota Camry</p>
                <div className="flex justify-between text-sm mt-2">
                  <span>Driver: John Smith</span>
                  <span>Speed: 45 mph</span>
                </div>
              </div>
              
              <div className="p-3 border border-border rounded-md">
                <div className="flex justify-between">
                  <span className="font-medium">VEH-002</span>
                  <span className="bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 py-1 px-2 rounded-full text-xs">
                    Idle
                  </span>
                </div>
                <p className="text-sm text-muted-foreground mt-1">Ford Transit</p>
                <div className="flex justify-between text-sm mt-2">
                  <span>Driver: Jane Wilson</span>
                  <span>Speed: 0 mph</span>
                </div>
              </div>
              
              <div className="p-3 border border-border rounded-md">
                <div className="flex justify-between">
                  <span className="font-medium">VEH-003</span>
                  <span className="bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200 py-1 px-2 rounded-full text-xs">
                    Maintenance
                  </span>
                </div>
                <p className="text-sm text-muted-foreground mt-1">Chevrolet Express</p>
                <div className="flex justify-between text-sm mt-2">
                  <span>Driver: N/A</span>
                  <span>Speed: 0 mph</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Tracking;
