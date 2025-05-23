import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { cn } from '../lib/utils';
import {
  ChevronLeft,
  ChevronRight,
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

const Sidebar = () => {
  const [collapsed, setCollapsed] = useState(false);
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

  const toggleSidebar = () => {
    setCollapsed(!collapsed);
  };

  // Check if a path is active
  const isActive = path => {
    return location.pathname === path;
  };

  return (
    <div
      className={cn(
        'h-full bg-card border-r border-border transition-all duration-300 ease-in-out flex flex-col',
        collapsed ? 'w-16' : 'w-64'
      )}
    >
      {/* Sidebar header */}
      <div className="p-4 flex items-center justify-between border-b border-border">
        {!collapsed && <span className="font-bold text-xl">SAMFMS</span>}
        <Button
          variant="ghost"
          size="sm"
          onClick={toggleSidebar}
          className={cn('ml-auto', collapsed && 'mx-auto')}
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
        </Button>
      </div>

      {/* Navigation links */}
      <nav className="flex-1 py-4">
        <ul className="space-y-1 px-2">
          {navItems.map(item => (
            <li key={item.path}>
              <Link
                to={item.path}
                className={cn(
                  'flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                  isActive(item.path)
                    ? 'bg-primary/10 text-primary'
                    : 'text-foreground hover:bg-accent hover:text-accent-foreground',
                  collapsed && 'justify-center px-2'
                )}
              >
                <span>{item.icon}</span>
                {!collapsed && <span>{item.label}</span>}
              </Link>
            </li>
          ))}
        </ul>
      </nav>

      {/* Sidebar footer */}
      <div className="p-4 border-t border-border">
        {!collapsed && <div className="text-xs text-muted-foreground">Fleet Management System</div>}
      </div>
    </div>
  );
};

export default Sidebar;
