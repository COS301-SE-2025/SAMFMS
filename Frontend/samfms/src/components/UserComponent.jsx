import React, {useState} from 'react';
import {Button} from './ui/button';
import {LogOut, User} from 'lucide-react';
import {Link} from 'react-router-dom';

const UserComponent = () => {
  // In a real application, this would come from authentication context or state
  const user = {
    name: 'John Doe',
    email: 'john.doe@example.com',
    role: 'Administrator',
    avatar: null, // Would be a URL to the user's avatar image
  };

  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  // Handlers for mouse events
  const handleMouseEnter = () => {
    setIsDropdownOpen(true);
    console.log("Set to true");
  };

  const handleMouseLeave = () => {
    setIsDropdownOpen(false);
    console.log("Set to false");
  };

  return (
    <div className="flex items-center gap-3">

      <div className="hidden sm:flex flex-col items-end mr-2">
        <p className="text-sm font-medium">{user.name}</p>
        <p className="text-xs text-muted-foreground">{user.role}</p>
      </div>

      <div className="relative" onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave}>

        <div className="h-10 w-10 rounded-full bg-primary/20 flex items-center justify-center text-primary font-semibold">
          {user.avatar ? (
            <img
              src={user.avatar}
              alt={user.name}
              className="h-full w-full rounded-full object-cover"
            />
          ) : (
            <User size={20} />
          )}
        </div>

        {isDropdownOpen && (
          <div className="absolute right-0 top-full w-48 rounded-md shadow-lg bg-card border border-border group-hover:block z-50">
            <div className="py-1">
              <Link
                to="/account"
                className="px-4 py-2 text-sm text-foreground hover:bg-accent flex items-center gap-2"
              >
                <User size={16} />
                Profile
              </Link>
              <Button
                variant="ghost"
                className="w-full justify-start text-sm px-4 py-2 text-destructive hover:bg-destructive/10 flex items-center gap-2"
              >
                <LogOut size={16} />
                Logout
              </Button>
            </div>
          </div>)}

      </div>
    </div>
  );
};

export default UserComponent;