import {BrowserRouter as Router, Routes, Route, Navigate} from 'react-router-dom';
import './App.css';
import 'leaflet/dist/leaflet.css';

// Import layout and contexts
import Layout from './components/layout/Layout';
import ThemeProvider from './contexts/ThemeContext';
import NotificationProvider from './contexts/NotificationContext';
import ProtectedRoute from './components/auth/ProtectedRoute';
import RoleBasedRoute from './components/auth/RoleBasedRoute';
import DriverAccessGuard from './components/auth/DriverAccessGuard';
import ErrorBoundary from './components/common/ErrorBoundary';
import AuthErrorBoundary from './components/auth/AuthErrorBoundary';

// Import pages
import UserActivation from './components/auth/UserActivation';
import Dashboard from './pages/Dashboard';
import Account from './pages/Account';
import Plugins from './pages/Plugins';
import Vehicles from './pages/Vehicles';
import Drivers from './pages/Drivers';
import Tracking from './pages/Tracking';
import Trips from './pages/Trips';
import Maintenance from './pages/Maintenance';
import Help from './pages/Help';
import Landing from './pages/Landing';
import UserManagement from './pages/UserManagement';
import DriverHomePage from './pages/DriverHomePage';
import TripNavigation from './pages/TripNavigation';
import DriverBehavior from './pages/DriverBehavior';

function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider>
        <NotificationProvider>
          <Router>
            <Routes>
              {/* Public landing page as default route */}
              <Route path="/" element={<Landing />} />

              <Route
                path="/activate"
                element={
                  <AuthErrorBoundary>
                    <UserActivation />
                  </AuthErrorBoundary>
                }
              />
              {/* Protected routes inside Layout - all wrapped in AuthErrorBoundary */}
              <Route
                element={
                  <AuthErrorBoundary>
                    <ProtectedRoute />
                  </AuthErrorBoundary>
                }
              >
                <Route element={<Layout />}>
                  <Route
                    path="/dashboard"
                    element={
                      <DriverAccessGuard>
                        <RoleBasedRoute adminComponent={Dashboard} driverComponent={null} />
                      </DriverAccessGuard>
                    }
                  />
                  <Route path="/driver-home" element={<DriverHomePage />} />
                  <Route path="/trip-navigation" element={<TripNavigation />} />
                  <Route path="/driver-behavior" element={<DriverAccessGuard><DriverBehavior /></DriverAccessGuard>} />
                  <Route path="/vehicles" element={<DriverAccessGuard><Vehicles /></DriverAccessGuard>} />
                  <Route path="/drivers" element={<DriverAccessGuard><Drivers /></DriverAccessGuard>} />
                  <Route path="/tracking" element={<DriverAccessGuard><Tracking /></DriverAccessGuard>} />
                  <Route path="/trips" element={<DriverAccessGuard><Trips /></DriverAccessGuard>} />
                  <Route path="/maintenance" element={<DriverAccessGuard><Maintenance /></DriverAccessGuard>} />
                  <Route path="/account" element={<Account />} />
                  <Route path="/plugins" element={<DriverAccessGuard><Plugins /></DriverAccessGuard>} />
                  <Route path="/users" element={<DriverAccessGuard><UserManagement /></DriverAccessGuard>} />
                  <Route path="/help" element={<Help />} />
                </Route>
              </Route>

              {/* Catch-all route */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Router>
        </NotificationProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
