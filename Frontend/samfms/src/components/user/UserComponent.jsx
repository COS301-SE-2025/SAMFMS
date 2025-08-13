import React, { useState, useEffect } from 'react';
import { User } from 'lucide-react';
import { getCurrentUser } from '../../backend/API.js';

const UserComponent = () => {
  const [user, setUser] = useState({
    full_name: 'Loading...',
    email: '',
    role: '',
    avatar: null,
  });

  // Load user data from localStorage
  useEffect(() => {
    const currentUser = getCurrentUser();
    if (currentUser) {
      // Map role to display name
      const roleDisplayNames = {
        admin: 'Administrator',
        fleet_manager: 'Fleet Manager',
        driver: 'Driver',
      };

      setUser({
        ...currentUser,
        role: roleDisplayNames[currentUser.role] || currentUser.role,
      });
    }
  }, []);

  return (
    <div className="flex items-center gap-3">
      <div className="hidden sm:flex flex-col items-end mr-2">
        <p className="text-sm font-medium">{user.full_name}</p>
        <p className="text-xs text-muted-foreground">{user.role}</p>
      </div>
      <div className="h-10 w-10 rounded-full bg-primary/20 flex items-center justify-center text-primary font-semibold">
        {user.avatar ? (
          <img
            src={user.avatar}
            alt={user.full_name || 'User'}
            className="h-full w-full rounded-full object-cover"
          />
        ) : (
          <User size={20} />
        )}
      </div>
    </div>
  );
};

export default UserComponent;
