import React, { useEffect, useState, useRef } from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { isAuthenticated, checkUserExistence, clearUserExistenceCache } from '../../backend/API';

const ProtectedRoute = () => {
  const [loading, setLoading] = useState(true);
  const [redirectTo, setRedirectTo] = useState('/login');
  const [error, setError] = useState(false);
  const mountedRef = useRef(true);
  const checkingRef = useRef(false);
  const location = useLocation();

  useEffect(() => {
    mountedRef.current = true;

    // Prevent multiple concurrent checks
    if (checkingRef.current) {
      return;
    }

    // Add a safety timeout to prevent infinite loading
    const timeoutId = setTimeout(() => {
      if (loading && mountedRef.current) {
        console.log('Safety timeout triggered - forcing loading to complete');
        setLoading(false);
      }
    }, 5000); // 5 second maximum loading time

    const checkAuthAndUsers = async () => {
      // Prevent multiple concurrent executions
      if (checkingRef.current) {
        return;
      }

      checkingRef.current = true;

      try {
        // First check if the user is already authenticated
        if (isAuthenticated()) {
          if (mountedRef.current) {
            setLoading(false);
          }
          return; // Already authenticated, no need to check user existence
        }

        // Clear cache to ensure fresh check when determining routes
        clearUserExistenceCache();

        // If no users exist in the system, redirect to signup instead of login
        const usersExist = await checkUserExistence(true);

        if (mountedRef.current) {
          setRedirectTo(usersExist ? '/login' : '/signup');
        }
      } catch (error) {
        console.error('Error in ProtectedRoute:', error);
        if (mountedRef.current) {
          setError(true);
          // If there's an error, default to login route
          setRedirectTo('/login');
        }
      } finally {
        checkingRef.current = false;
        if (mountedRef.current) {
          setLoading(false);
        }
      }
    };

    checkAuthAndUsers();

    return () => {
      mountedRef.current = false;
      clearTimeout(timeoutId); // Cleanup timeout on unmount
    };
  }, [location.pathname]); // Only re-check authentication when route changes

  if (loading) {
    return (
      <div className="min-h-screen flex justify-center items-center bg-primary-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-800 mx-auto mb-4"></div>
          <p className="text-primary-800">Loading...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex justify-center items-center bg-primary-100">
        <div className="text-center p-6 max-w-md bg-white rounded-lg shadow-lg">
          <div className="text-red-600 text-5xl mb-4">⚠️</div>
          <h2 className="text-xl font-bold text-red-600 mb-2">Connection Error</h2>
          <p className="text-gray-700 mb-4">
            We couldn't connect to the authentication service. This may happen if the server is down
            or you're experiencing network issues.
          </p>
          <div className="flex justify-center">
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-primary-700 text-white rounded hover:bg-primary-800"
            >
              Retry Connection
            </button>
          </div>
        </div>
      </div>
    );
  }

  return isAuthenticated() ? <Outlet /> : <Navigate to={redirectTo} />;
};

export default ProtectedRoute;
