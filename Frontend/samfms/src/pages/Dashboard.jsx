import React from 'react';

const Dashboard = () => {
  return (
    <div className="relative container mx-auto py-8 space-y-8">
      {/* Background pattern */}
      <div
        className="absolute inset-0 z-0 opacity-10 pointer-events-none"
        style={{
          backgroundImage: 'url("/logo/logo_icon_dark.svg")',
          backgroundSize: '200px',
          backgroundRepeat: 'repeat',
          filter: 'blur(1px)',
        }}
        aria-hidden="true"
      />
      {/* Content */}
      <div className="relative z-10">
        {/* Header */}
        <header>
          <h1 className="text-4xl font-bold mb-2">Fleet Dashboard</h1>
          <p className="text-muted-foreground">Welcome to SAMFMS - Your Fleet Management System</p>
        </header>

        {/* Simple welcome message */}
        <div className="bg-card rounded-lg border border-border p-8 text-center">
          <h2 className="text-2xl font-semibold mb-4">Dashboard Under Construction</h2>
          <p className="text-muted-foreground">
            Use the navigation menu to access vehicles, drivers, tracking, and other features.
          </p>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
