import React, {useState} from 'react';
import {Link, useLocation} from 'react-router-dom';
import {useTheme} from '../../contexts/ThemeContext';
import {Menu, X, Home, User, Package2, Car, Users, Map, Navigation, Wrench} from 'lucide-react';
import {Button} from '../ui/button';
import {cn} from '../../lib/utils';
import {createPortal} from 'react-dom';

const MobileNav = () => {
  const [isOpen, setIsOpen] = useState(false);
  const location = useLocation();
  const {theme} = useTheme();
  const navItems = [
    {path: '/dashboard', label: 'Dashboard', icon: <Home size={20} />},
    {path: '/vehicles', label: 'Vehicles', icon: <Car size={20} />},
    {path: '/drivers', label: 'Drivers', icon: <Users size={20} />},
    {path: '/tracking', label: 'Tracking', icon: <Map size={20} />},
    {path: '/trips', label: 'Trips', icon: <Navigation size={20} />},
    {path: '/maintenance', label: 'Maintenance', icon: <Wrench size={20} />},
    {path: '/plugins', label: 'Plugins', icon: <Package2 size={20} />},
    {path: '/account', label: 'Account', icon: <User size={20} />},
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

      {/* Mobile navigation overlay - rendered as portal to document body */}
      {isOpen && createPortal(
        <div className="fixed inset-0 z-[9999] md:hidden">
          {/* Background overlay - click to close */}
          <div
            className="fixed inset-0 bg-black/20 backdrop-blur-sm"
            onClick={() => setIsOpen(false)}
          />
          {/* Navigation panel */}
          <div className="fixed inset-y-0 left-0 w-3/4 max-w-xs bg-card border-r border-border shadow-xl z-[10000]">
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
        </div>,
        document.body
      )}
    </>
  );
};

export default MobileNav;
