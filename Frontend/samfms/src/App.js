import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';
import 'leaflet/dist/leaflet.css';

// Import layout and contexts
import Layout from './components/Layout';
import ThemeProvider from './contexts/ThemeContext';
import ProtectedRoute from './components/ProtectedRoute';

// Import pages
import Login from './pages/Login';
import Signup from './pages/Signup';
import Dashboard from './pages/Dashboard';
import Account from './pages/Account';
import Settings from './pages/Settings';
import Plugins from './pages/Plugins';
import Vehicles from './pages/Vehicles';
import Drivers from './pages/Drivers';
import Tracking from './pages/Tracking';
import Trips from './pages/Trips';
import Maintenance from './pages/Maintenance';
import UserManagement from './components/UserManagement';

function App() {
  return (
    <ThemeProvider>
      <Router>
        <Routes>
          {' '}
          {/* Public routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          {/* Protected routes inside Layout */}{' '}
          <Route element={<ProtectedRoute />}>
            <Route path="/" element={<Layout />}>
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/vehicles" element={<Vehicles />} />
              <Route path="/drivers" element={<Drivers />} />
              <Route path="/tracking" element={<Tracking />} />
              <Route path="/trips" element={<Trips />} />
              <Route path="/maintenance" element={<Maintenance />} />
              <Route path="/account" element={<Account />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="/plugins" element={<Plugins />} />
              <Route path="/users" element={<UserManagement />} />
            </Route>
          </Route>
        </Routes>
      </Router>
    </ThemeProvider>
  );
}

export default App;
