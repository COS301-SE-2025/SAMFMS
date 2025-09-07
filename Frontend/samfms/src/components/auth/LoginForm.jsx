import React, { useState } from 'react';
import { Button } from '../ui/button';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../../contexts/ThemeContext';
import {
  login,
  hasRole,
} from '../../backend/API.js';
import { ROLES } from '../auth/RBACUtils';

const LoginForm = ({ onSuccess, onClose }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [validationErrors, setValidationErrors] = useState({
    email: '',
    password: '',
  });
  const [touched, setTouched] = useState({
    email: false,
    password: false,
  });
  const navigate = useNavigate();
  const { theme } = useTheme();

  // Validate email
  const validateEmail = email => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!email.trim()) {
      return 'Email is required';
    } else if (!emailRegex.test(email)) {
      return 'Invalid email format';
    }
    return '';
  };

  // Validate password
  const validatePassword = password => {
    if (!password.trim()) {
      return 'Password is required';
    } else if (password.length < 6) {
      return 'Password must be at least 6 characters';
    }
    return '';
  };

  // Handle blur events
  const handleBlur = field => {
    setTouched({ ...touched, [field]: true });

    if (field === 'email') {
      setValidationErrors({
        ...validationErrors,
        email: validateEmail(email),
      });
    } else if (field === 'password') {
      setValidationErrors({
        ...validationErrors,
        password: validatePassword(password),
      });
    }
  };

  // Handle change events with validation
  const handleChange = (field, value) => {
    if (field === 'email') {
      setEmail(value);
      if (touched.email) {
        setValidationErrors({
          ...validationErrors,
          email: validateEmail(value),
        });
      }
    } else if (field === 'password') {
      setPassword(value);
      if (touched.password) {
        setValidationErrors({
          ...validationErrors,
          password: validatePassword(value),
        });
      }
    }
  };

  const handleSubmit = async e => {
    e.preventDefault();

    // Validate all fields
    const emailError = validateEmail(email);
    const passwordError = validatePassword(password);

    setValidationErrors({
      email: emailError,
      password: passwordError,
    });

    setTouched({
      email: true,
      password: true,
    });

    // If any validation errors, prevent form submission
    if (emailError || passwordError) {
      return;
    }

    setError('');
    setLoading(true);

    try {
      await login(email, password);
      // Force a small delay to ensure cookies are set before navigation
      setTimeout(() => {
        if (onSuccess) {
          onSuccess();
        }
        // Redirect based on user role
        if (hasRole(ROLES.DRIVER)) {
          navigate('/driver-home', { replace: true });
        } else {
          navigate('/dashboard', { replace: true });
        }
      }, 100);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md mx-auto">
      {/* Logo for modal */}
      <div className="mb-6 text-center">
        <img
          src={theme === 'dark' ? '/logo/logo_dark.svg' : '/logo/logo_light.svg'}
          alt="SAMFMS Logo"
          className="h-16 mx-auto mb-3 animate-fadeIn transition-all duration-300 drop-shadow-lg"
        />
      </div>

      <form className="space-y-6" onSubmit={handleSubmit}>
        {error && (
          <div
            className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 px-4 py-3 rounded-lg relative"
            role="alert"
          >
            <div className="flex items-center gap-2">
              <span className="text-red-500">⚠</span>
              <span className="block text-sm font-medium">{error}</span>
            </div>
          </div>
        )}

        <div className="space-y-2">
          <label htmlFor="modal-email" className="block text-sm font-semibold text-gray-700 dark:text-gray-300">
            Email Address
          </label>
          <input
            id="modal-email"
            type="email"
            placeholder="Enter your email"
            value={email}
            onChange={e => handleChange('email', e.target.value)}
            onBlur={() => handleBlur('email')}
            required
            className={`w-full px-4 py-3 border rounded-lg bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 ${
              validationErrors.email && touched.email
                ? 'border-red-500 ring-2 ring-red-200'
                : 'border-gray-300 dark:border-gray-600'
            }`}
          />
          {validationErrors.email && touched.email && (
            <p className="text-red-500 text-sm mt-1 flex items-center gap-1">
              <span className="w-4 h-4 text-red-500">⚠</span>
              {validationErrors.email}
            </p>
          )}
        </div>

        <div className="space-y-2">
          <label htmlFor="modal-password" className="block text-sm font-semibold text-gray-700 dark:text-gray-300">
            Password
          </label>
          <input
            id="modal-password"
            type="password"
            placeholder="Enter your password"
            value={password}
            onChange={e => handleChange('password', e.target.value)}
            onBlur={() => handleBlur('password')}
            required
            className={`w-full px-4 py-3 border rounded-lg bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 ${
              validationErrors.password && touched.password
                ? 'border-red-500 ring-2 ring-red-200'
                : 'border-gray-300 dark:border-gray-600'
            }`}
          />
          {validationErrors.password && touched.password && (
            <p className="text-red-500 text-sm mt-1 flex items-center gap-1">
              <span className="w-4 h-4 text-red-500">⚠</span>
              {validationErrors.password}
            </p>
          )}
        </div>

        {/* Forgot Password Link */}
        <div className="text-right">
          <button
            type="button"
            onClick={() => console.log('Forgot password clicked')}
            className="text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 hover:underline focus:outline-none focus:underline transition-colors duration-200 font-medium"
          >
            Forgot your password?
          </button>
        </div>

        <div className="flex gap-3">
          <Button
            type="button"
            variant="outline"
            onClick={onClose}
            className="flex-1 py-3 border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 transition-all duration-200"
          >
            Cancel
          </Button>
          <Button
            type="submit"
            disabled={loading}
            className="flex-1 py-3 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white font-semibold rounded-lg transform transition-all duration-200 hover:scale-[1.02] active:scale-[0.98] hover:shadow-lg focus:ring-4 focus:ring-blue-300 dark:focus:ring-blue-800 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
          >
            {loading ? (
              <div className="flex items-center justify-center gap-2">
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                Logging in...
              </div>
            ) : (
              'Login to Account'
            )}
          </Button>
        </div>
      </form>
    </div>
  );
};

export default LoginForm;
