import React from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';
import MobileNav from './MobileNav';
import UserComponent from './UserComponent';

const Layout = () => {
  const location = useLocation();
  // Function to get current page title
  const getCurrentPageTitle = () => {
    const path = location.pathname.split('/')[1];
    if (!path) return 'Dashboard';
    return path.charAt(0).toUpperCase() + path.slice(1);
  };
  return (
    <div className="h-screen flex overflow-hidden">
      {/* Sidebar - hidden on mobile screens */}
      <div className="hidden md:block h-full">
        <Sidebar />
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top navigation bar */}
        <nav className="bg-card shadow-sm border-b border-border z-10">
          <div className="px-4 py-3 flex justify-between items-center">
            <div className="flex items-center space-x-4">
              <MobileNav />
              <div className="font-semibold text-lg">{getCurrentPageTitle()}</div>
            </div>
            <UserComponent />
          </div>
        </nav>

        {/* Main content area */}
        <main className="flex-1 overflow-auto bg-background p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default Layout;
