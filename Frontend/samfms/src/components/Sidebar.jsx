import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { cn } from '../lib/utils';
import { useTheme } from '../contexts/ThemeContext';
import {
  Home,
  Settings,
  User,
  Package2,
  Car,
  Users,
  Map,
  Navigation,
  Wrench,
  UserPlus,
} from 'lucide-react';
import { Button } from './ui/button';
import { useAuth, PERMISSIONS, ROLES } from './RBACUtils';

const Sidebar = () => {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();
  const { theme } = useTheme();
  const { hasPermission, hasAnyRole } = useAuth();
  // Define navigation items with permission requirements
  const allNavItems = [
    { path: '/dashboard', label: 'Dashboard', icon: <Home size={20} />, permission: null }, // Always visible
    {
      path: '/vehicles',
      label: 'Vehicles',
      icon: <Car size={20} />,
      permission: PERMISSIONS.VEHICLES_READ,
    },
    {
      path: '/drivers',
      label: 'Drivers',
      icon: <Users size={20} />,
      permission: PERMISSIONS.DRIVERS_READ,
    },
    {
      path: '/tracking',
      label: 'Tracking',
      icon: <Map size={20} />,
      permission: PERMISSIONS.VEHICLES_READ,
    },
    {
      path: '/trips',
      label: 'Trips',
      icon: <Navigation size={20} />,
      permission: PERMISSIONS.TRIPS_READ_OWN,
    },
    {
      path: '/maintenance',
      label: 'Maintenance',
      icon: <Wrench size={20} />,
      permission: PERMISSIONS.MAINTENANCE_READ_ASSIGNED,
    },
    {
      path: '/users',
      label: 'User Management',
      icon: <UserPlus size={20} />,
      roles: [ROLES.ADMIN],
    }, // Admin only
    { path: '/plugins', label: 'Plugins', icon: <Package2 size={20} />, roles: [ROLES.ADMIN] }, // Admin only
    { path: '/settings', label: 'Settings', icon: <Settings size={20} />, permission: null }, // Always visible
    { path: '/account', label: 'Account', icon: <User size={20} />, permission: null }, // Always visible
  ];

  // Filter navigation items based on user permissions
  const navItems = allNavItems.filter(item => {
    // If no permission or role required, show the item
    if (!item.permission && !item.roles) return true;

    // Check role-based access
    if (item.roles && !hasAnyRole(item.roles)) return false;

    // Check permission-based access
    if (item.permission && !hasPermission(item.permission)) return false;

    return true;
  });

  const toggleSidebar = () => {
    setCollapsed(prev => !prev);
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
      <div
        className="p-4 flex items-center justify-between border-b border-border cursor-pointer"
        onClick={toggleSidebar}
        tabIndex={0}
        aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        role="button"
      >
        {/* Logo as expand/collapse button */}
        {!collapsed ? (
          <div className="flex items-center w-full">
            <img
              src={
                theme === 'dark'
                  ? '/logo/logo_horisontal_dark.svg'
                  : '/logo/logo_horisontal_light.svg'
              }
              alt="SAMFMS Logo"
              className="h-8"
            />
          </div>
        ) : (
          <div className="w-full flex items-center justify-center">
            <img
              src={theme === 'dark' ? '/logo/logo_icon_dark.svg' : '/logo/logo_icon_light.svg'}
              alt="SAMFMS Icon"
              className="h-8"
            />
          </div>
        )}
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
