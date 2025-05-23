import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  Menu,
  X,
  Home,
  Settings,
  User,
  Package2,
  Car,
  Users,
  Map,
  Navigation,
  Wrench,
} from 'lucide-react';
import { Button } from './ui/button';
import { cn } from '../lib/utils';

const MobileNav = () => {
  const [isOpen, setIsOpen] = useState(false);
  const location = useLocation();
  const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: <Home size={20} /> },
    { path: '/vehicles', label: 'Vehicles', icon: <Car size={20} /> },
    { path: '/drivers', label: 'Drivers', icon: <Users size={20} /> },
    { path: '/tracking', label: 'Tracking', icon: <Map size={20} /> },
    { path: '/trips', label: 'Trips', icon: <Navigation size={20} /> },
    { path: '/maintenance', label: 'Maintenance', icon: <Wrench size={20} /> },
    { path: '/plugins', label: 'Plugins', icon: <Package2 size={20} /> },
    { path: '/settings', label: 'Settings', icon: <Settings size={20} /> },
    { path: '/account', label: 'Account', icon: <User size={20} /> },
  ];

  // Check if a path is active
  const isActive = path => {
    return location.pathname === path;
  };

  const toggleNav = () => {
    setIsOpen(!isOpen);
  };

  return (
    <>
      <Button
        variant="ghost"
        size="sm"
        className="md:hidden"
        onClick={toggleNav}
        aria-label="Toggle navigation"
      >
        <Menu size={20} />
      </Button>

      {/* Mobile navigation overlay */}
      {isOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          {/* Background overlay */}
          <div
            className="fixed inset-0 bg-background/80 backdrop-blur-sm"
            onClick={() => setIsOpen(false)}
          />

          {/* Navigation panel */}
          <div className="fixed inset-y-0 left-0 w-3/4 max-w-xs bg-card border-r border-border shadow-lg">
            <div className="flex items-center justify-between p-4 border-b border-border">
              <span className="font-bold text-xl">SAMFMS</span>
              <Button variant="ghost" size="sm" onClick={toggleNav} aria-label="Close navigation">
                <X size={20} />
              </Button>
            </div>

            <nav className="p-4">
              <ul className="space-y-3">
                {navItems.map(item => (
                  <li key={item.path}>
                    <Link
                      to={item.path}
                      className={cn(
                        'flex items-center gap-3 px-4 py-3 rounded-md text-sm font-medium transition-colors',
                        isActive(item.path)
                          ? 'bg-primary/10 text-primary'
                          : 'text-foreground hover:bg-accent hover:text-accent-foreground'
                      )}
                      onClick={() => setIsOpen(false)}
                    >
                      {item.icon}
                      <span>{item.label}</span>
                    </Link>
                  </li>
                ))}
              </ul>
            </nav>
          </div>
        </div>
      )}
    </>
  );
};

export default MobileNav;
