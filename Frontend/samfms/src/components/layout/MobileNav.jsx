import React, {useState} from 'react';
import {Link, useLocation, useNavigate} from 'react-router-dom';
import {useTheme} from '../../contexts/ThemeContext';
import {
  Menu,
  X,
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
  LogOut,
} from 'lucide-react';
import {Button} from '../ui/button';
import {cn} from '../../lib/utils';
import {createPortal} from 'react-dom';
import {useAuth, PERMISSIONS, ROLES} from '../auth/RBACUtils';
import SearchBar from './SearchBar';
import {logout} from '../../backend/API.js';

const MobileNav = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const {theme} = useTheme();
  const {hasPermission, hasAnyRole, hasRole} = useAuth();

  // Define navigation items with permission requirements (matching Sidebar)
  const allNavItems = [
    {path: '/dashboard', label: 'Dashboard', icon: <Home size={20} />, permission: null}, // Always visible
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
    {path: '/plugins', label: 'Plugins', icon: <Package2 size={20} />, roles: [ROLES.ADMIN]}, // Admin only
    {path: '/account', label: 'Account', icon: <User size={20} />, permission: null}, // Always visible
    {path: '/help', label: 'Help', icon: <HelpCircle size={20} />, permission: null}, // Always visible to all users
  ];

  // Filter navigation items based on user permissions (matching Sidebar logic)
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

      {/* Mobile navigation overlay - rendered as portal to document body */}
      {isOpen &&
        createPortal(
          <div className="fixed inset-0 z-[9999] md:hidden">
            {/* Background overlay - click to close */}
            <div
              className="fixed inset-0 bg-black/20 backdrop-blur-sm"
              onClick={() => setIsOpen(false)}
            />
            {/* Navigation panel */}
            <div className="fixed inset-y-0 left-0 w-3/4 max-w-xs bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 border-r border-border shadow-xl z-[10000] flex flex-col">
              <div className="flex items-center justify-between p-4 border-b border-border">
                <img
                  src={
                    theme === 'dark'
                      ? '/logo/logo_horisontal_dark.svg'
                      : '/logo/logo_horisontal_light.svg'
                  }
                  alt="SAMFMS Logo"
                  className="h-8"
                />
                <Button variant="ghost" size="sm" onClick={toggleNav} aria-label="Close navigation">
                  <X size={20} />
                </Button>
              </div>

              <nav className="flex-1 p-4 overflow-y-auto">

                <ul className="space-y-2">
                  {navItems.map(item => (
                    <li key={item.path}>
                      <Link
                        to={item.path}
                        className={cn(
                          'flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors',
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

              {/* Footer with logout */}
              <div className="p-4 border-t border-border mt-auto">
                <div className="text-xs text-muted-foreground mb-3">Fleet Management System</div>
                <button
                  onClick={() => {
                    setShowLogoutConfirm(true);
                    setIsOpen(false);
                  }}
                  className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm text-white bg-red-600 hover:bg-red-700 transition-colors"
                >
                  <LogOut size={16} className="text-white" />
                  <span>Logout</span>
                </button>
              </div>
            </div>
          </div>,
          document.body
        )}

      {/* Logout Confirmation Dialog */}
      {showLogoutConfirm &&
        createPortal(
          <div className="fixed inset-0 bg-black/50 z-[10001] flex items-center justify-center p-4">
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
                  onClick={async () => {
                    setShowLogoutConfirm(false);
                    try {
                      await logout();
                      // Navigate to landing page after successful logout
                      navigate('/');
                    } catch (error) {
                      console.error('Logout failed:', error);
                      // Still navigate even if logout fails to prevent stuck state
                      navigate('/');
                    }
                  }}
                  className="px-4 py-2 rounded-md bg-red-600 hover:bg-red-700 transition-colors text-white"
                >
                  Logout
                </button>
              </div>
            </div>
          </div>,
          document.body
        )}
    </>
  );
};

export default MobileNav;
