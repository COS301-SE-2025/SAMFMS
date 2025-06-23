import {BrowserRouter as Router, Routes, Route, Navigate} from 'react-router-dom';
import './App.css';
import 'leaflet/dist/leaflet.css';

// Import layout and contexts
import Layout from './components/Layout';
import ThemeProvider from './contexts/ThemeContext';
import NotificationProvider from './contexts/NotificationContext';
import ProtectedRoute from './components/ProtectedRoute';
import ErrorBoundary from './components/ErrorBoundary';
import AuthErrorBoundary from './components/AuthErrorBoundary';

// Import pages
import Login from './pages/Login';
import Signup from './pages/Signup';
import UserActivation from './components/UserActivation';
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
import UserManagement from './components/UserManagement';

function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider>
        <NotificationProvider>
          <Router>
            <Routes>
              {/* Public landing page as default route */}
              <Route path="/" element={<Landing />} />

              {/* Public routes - wrapped in AuthErrorBoundary for auth-related errors */}
              <Route
                path="/login" element={
                  <AuthErrorBoundary>
                    <Login />
                  </AuthErrorBoundary>
                }
              />
              <Route
                path="/signup"
                element={
                  <AuthErrorBoundary>
                    <Signup />
                  </AuthErrorBoundary>
                }
              />
              <Route
                path="/activate"
                element={
                  <AuthErrorBoundary>
                    <UserActivation />
                  </AuthErrorBoundary>
                }
              />
              {/* Protected routes inside Layout - all wrapped in AuthErrorBoundary */}
              {/* <Route
                element={
                  <AuthErrorBoundary>
                    <ProtectedRoute />
                  </AuthErrorBoundary>
                }
              > */}
              <Route element={<Layout />}>
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/vehicles" element={<Vehicles />} />{' '}
                <Route path="/drivers" element={<Drivers />} />
                <Route path="/tracking" element={<Tracking />} />
                <Route path="/trips" element={<Trips />} />
                <Route path="/maintenance" element={<Maintenance />} />
                <Route path="/account" element={<Account />} />
                <Route path="/plugins" element={<Plugins />} />
                <Route path="/users" element={<UserManagement />} />
                <Route path="/help" element={<Help />} />
              </Route>
              {/* </Route> */}

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
