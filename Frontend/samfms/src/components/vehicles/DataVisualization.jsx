import React from 'react';

const DataVisualization = () => {
  return (
    <div className="mt-6">
      <div className="bg-card rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold mb-4">Fleet Analytics</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-background p-4 rounded-md border border-border">
            <h3 className="font-medium mb-2">Maintenance Cost Distribution</h3>
            <div className="h-64 flex items-center justify-center border-t border-border pt-4">
              <p className="text-muted-foreground">Chart visualization would appear here</p>
            </div>
          </div>
          <div className="bg-background p-4 rounded-md border border-border">
            <h3 className="font-medium mb-2">Mileage Trends</h3>
            <div className="h-64 flex items-center justify-center border-t border-border pt-4">
              <p className="text-muted-foreground">Chart visualization would appear here</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DataVisualization;
