import React, {useEffect} from 'react';
import {useNavigate} from 'react-router-dom';
import {hasRole, logout} from '../../backend/API';
import {ROLES} from '../auth/RBACUtils';

/**
 * Component that checks if the current user is a driver and handles logout/redirection
 * This should be used to protect routes that drivers shouldn't access
 */
const DriverAccessGuard = ({children, showError = true}) => {
    const navigate = useNavigate();

    useEffect(() => {
        // Check if user is a driver
        if (hasRole(ROLES.DRIVER)) {
            // Log out the driver immediately
            logout();

            // Redirect to landing page with error message
            navigate('/', {
                replace: true,
                state: {
                    driverError: true,
                    errorMessage: 'Drivers are not authorized to access the web application. Please download and use the driver mobile app instead.'
                }
            });
        }
    }, [navigate]);

    // If user is a driver, don't render children
    if (hasRole(ROLES.DRIVER)) {
        return null;
    }

    // If user is not a driver, render children normally
    return children;
};

export default DriverAccessGuard;