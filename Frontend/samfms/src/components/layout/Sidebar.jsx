import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { cn } from '../../lib/utils';
import { useTheme } from '../../contexts/ThemeContext';
import {
  Home,
  User,
  Package2,
  Car,
  Users,
  Map,
  Navigation,
  Wrench,
  UserPlus,
  HelpCircle,
  ChevronLeft,
  ChevronRight,
  LogOut,
} from 'lucide-react';
import { useAuth, PERMISSIONS, ROLES } from '../auth/RBACUtils';
import { logout } from '../../backend/API.js';

const Sidebar = () => {
  const [collapsed, setCollapsed] = useState(false);
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { theme } = useTheme();
  const { hasPermission, hasAnyRole, hasRole } = useAuth();
  // Define navigation items with permission requirements
  const allNavItems = [
    {
      path: '/dashboard',
      label: 'Dashboard',
      icon: <Home size={20} />,
      permission: null,
      excludeRoles: [ROLES.DRIVER],
    }, // Hidden for drivers
    { path: '/driver-home', label: 'Home', icon: <Home size={20} />, roles: [ROLES.DRIVER] }, // Driver only
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
    { path: '/account', label: 'Account', icon: <User size={20} />, permission: null }, // Always visible
    { path: '/help', label: 'Help', icon: <HelpCircle size={20} />, permission: null }, // Always visible to all users
  ];

  // Filter navigation items based on user permissions
  const navItems = allNavItems.filter(item => {
    // Check if current user role is excluded from this item
    if (item.excludeRoles && item.excludeRoles.some(role => hasRole(role))) {
      return false;
    }

    // If no permission or role required, show the item
    if (!item.permission && !item.roles && !item.excludeRoles) return true;

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
        collapsed
          ? 'w-16 hover:w-24 group' // Collapsed: w-16, expand to w-24 on hover
          : 'w-64'
      )}
    >
      {/* Sidebar header */}
      <div
        className="p-4 flex items-center border-b border-border cursor-pointer group/sidebar"
        onClick={toggleSidebar}
        tabIndex={0}
        aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        role="button"
      >
        {!collapsed ? (
          <>
            <div className="flex items-center">
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
            {/* Collapse arrow at far right */}
            <ChevronLeft
              className="ml-auto text-muted-foreground hover:text-primary transition-colors"
              size={22}
              aria-label="Collapse sidebar"
            />
          </>
        ) : (
          <div className="w-full flex items-center justify-between relative">
            <img
              src={theme === 'dark' ? '/logo/logo_icon_dark.svg' : '/logo/logo_icon_light.svg'}
              alt="SAMFMS Icon"
              className="h-8"
            />
            {/* Show right arrow on hover, always visible next to logo */}
            <ChevronRight
              className="ml-2 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity duration-200"
              size={22}
              aria-label="Expand sidebar"
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
        {!collapsed ? (
          <>
            <div className="text-xs text-muted-foreground mb-3">Fleet Management System</div>
            <button
              onClick={() => setShowLogoutConfirm(true)}
              className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm text-white bg-red-600 hover:bg-red-700 transition-colors"
            >
              <LogOut size={16} className="text-white" />
              <span>Logout</span>
            </button>
          </>
        ) : (
          <button
            onClick={() => setShowLogoutConfirm(true)}
            className="flex w-full items-center justify-center rounded-md py-2 text-white bg-red-600 hover:bg-red-700 transition-colors"
            title="Logout"
          >
            <LogOut size={16} className="text-white" />
          </button>
        )}

        {/* Logout Confirmation Dialog */}
        {showLogoutConfirm && (
          <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
            <div className="bg-card rounded-lg shadow-lg border border-border p-6 max-w-sm w-full">
              <h3 className="text-lg font-medium mb-4">Confirm Logout</h3>
              <p className="text-muted-foreground mb-6">Are you sure you want to logout?</p>
              <div className="flex justify-end gap-3">
                <button
                  onClick={() => setShowLogoutConfirm(false)}
                  className="px-4 py-2 rounded-md border border-input bg-background hover:bg-accent transition-colors text-foreground"
                >
                  Cancel
                </button>
                <button
                  onClick={() => {
                    logout();
                    navigate('/logout');
                  }}
                  className="px-4 py-2 rounded-md bg-red-600 hover:bg-red-700 transition-colors text-white"
                >
                  Logout
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Sidebar;
