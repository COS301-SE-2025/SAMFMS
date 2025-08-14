import React, { useEffect } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';
import MobileNav from './MobileNav';
import UserComponent from '../user/UserComponent';

const Layout = () => {
  const location = useLocation();

  // Initialize session monitoring and token refresh when layout loads
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        // Start session monitoring
        const { startSessionMonitoring } = await import('../../utils/sessionMonitor');
        startSessionMonitoring();

        // Start token refresh
        const { startTokenRefresh } = await import('../../utils/tokenManager');
        startTokenRefresh();

        console.log('Authentication monitoring initialized');
      } catch (error) {
        console.error('Failed to initialize authentication monitoring:', error);
      }
    };

    initializeAuth();

    // Cleanup on unmount
    return () => {
      import('../../utils/sessionMonitor')
        .then(({ stopSessionMonitoring }) => {
          stopSessionMonitoring();
        })
        .catch(console.error);

      import('../../utils/tokenManager')
        .then(({ stopTokenRefresh }) => {
          stopTokenRefresh();
        })
        .catch(console.error);
    };
  }, []);

  // Track page views when route changes
  useEffect(() => {
    const trackPage = async () => {
      try {
        const { trackPageView } = await import('../../utils/sessionMonitor');
        trackPageView(location.pathname);
      } catch (error) {
        console.error('Failed to track page view:', error);
      }
    };

    trackPage();
  }, [location.pathname]);

  // Function to get current page title
  const getCurrentPageTitle = () => {
    const path = location.pathname.split('/')[1];
    if (!path) return 'Dashboard';
    if (path === 'driver-home') return 'Home';
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
        <nav className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 shadow-sm border-b border-slate-200 dark:border-slate-800 z-10">
          <div className="px-4 py-3 flex justify-between items-center">
            <div className="flex items-center space-x-4">
              <MobileNav />
              <div className="font-semibold text-lg">{getCurrentPageTitle()}</div>
            </div>
            <UserComponent />
          </div>
        </nav>

        {/* Main content area */}
        <main className="flex-1 overflow-auto bg-background">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default Layout;
