import React from 'react';
import { Link, Outlet, useLocation } from 'react-router-dom';
import { Button } from './ui/button';
import ThemeToggle from './ThemeToggle';
import Sidebar from './Sidebar';
import MobileNav from './MobileNav';

const Layout = () => {
  const location = useLocation();

  // Function to check if a path is active
  const isActive = path => {
    return location.pathname === path;
  };

  return (
    <div className="min-h-screen flex flex-col">
      {/* Navigation bar */}
      <nav className="bg-card shadow-md border-b border-border">
        <div className="container mx-auto px-4 py-3">
          {' '}
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-2">
              <MobileNav />
              <span className="text-2xl font-bold md:hidden">SAMFMS</span>
            </div>{' '}
            <div className="hidden md:flex space-x-1">
              <NavLink to="/dashboard" isActive={isActive('/dashboard')}>
                Dashboard
              </NavLink>
              <NavLink to="/vehicles" isActive={isActive('/vehicles')}>
                Vehicles
              </NavLink>
              <NavLink to="/drivers" isActive={isActive('/drivers')}>
                Drivers
              </NavLink>
              <NavLink to="/tracking" isActive={isActive('/tracking')}>
                Tracking
              </NavLink>
              <NavLink to="/trips" isActive={isActive('/trips')}>
                Trips
              </NavLink>
              <NavLink to="/maintenance" isActive={isActive('/maintenance')}>
                Maintenance
              </NavLink>
            </div>
            <div className="flex items-center space-x-2">
              <ThemeToggle />
              <Button variant="outline" size="sm" asChild>
                <Link to="/login">Login</Link>
              </Button>
            </div>
          </div>
        </div>
      </nav>{' '}
      {/* Main content area with sidebar */}{' '}
      <div className="flex flex-grow bg-background">
        {/* Sidebar - hidden on mobile screens */}
        <div className="hidden md:block">
          <Sidebar />
        </div>
        <main className="flex-grow p-6">
          <Outlet />
        </main>
      </div>
      {/* Footer */}
      <footer className="bg-card shadow-inner border-t border-border py-4">
        <div className="container mx-auto px-4">
          <p className="text-center text-muted-foreground text-sm">
            &copy; {new Date().getFullYear()} SAMFMS - Smart Fleet Management System
          </p>
        </div>
      </footer>
    </div>
  );
};

// Navigation link component
const NavLink = ({ to, children, isActive }) => {
  return (
    <Link
      to={to}
      className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
        isActive
          ? 'bg-primary/10 text-primary'
          : 'text-foreground hover:bg-accent hover:text-accent-foreground'
      }`}
    >
      {children}
    </Link>
  );
};

export default Layout;
