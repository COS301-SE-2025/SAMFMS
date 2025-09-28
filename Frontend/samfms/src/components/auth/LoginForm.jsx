import React, {useState} from 'react';
import {Button} from '../ui/button';
import {useNavigate} from 'react-router-dom';
import {useTheme} from '../../contexts/ThemeContext';
import {
  login,
  logout,
  hasRole
} from '../../backend/API.js';
import {
  forgotPassword
} from '../../backend/API.ts';
import {ROLES} from '../auth/RBACUtils';

const LoginForm = ({onSuccess, onClose}) => {
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
  const {theme} = useTheme();

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


  // Handle blur events
  const handleBlur = field => {
    setTouched({...touched, [field]: true});

    if (field === 'email') {
      setValidationErrors({
        ...validationErrors,
        email: validateEmail(email),
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
    }
  };

  const handleForgotPassword = async email => {
    const emailError = validateEmail(email);
    setValidationErrors({
      email: emailError,
    });
    setTouched({
      email: true
    });
    if (emailError) {
      return;
    }
    setError('');
    try {
      const res = await forgotPassword(email);
    } catch (err) {
      setError(err.message);
    }
  };

  // Helper function to clear form inputs and validation states
  const clearForm = () => {
    setEmail('');
    setPassword('');
    setValidationErrors({
      email: '',
      password: '',
    });
    setTouched({
      email: false,
      password: false,
    });
  };

  const handleSubmit = async e => {
    e.preventDefault();

    // Validate all fields
    const emailError = validateEmail(email);

    setValidationErrors({
      email: emailError,
    });

    setTouched({
      email: true,
      password: true,
    });

    // If any validation errors, prevent form submission
    if (emailError) {
      return;
    }

    setError('');
    setLoading(true);

    // Preserve current theme before login attempt
    const currentTheme = theme;
    const currentDOMTheme = document.documentElement.classList.contains('dark') ? 'dark' : 'light';

    try {
      await login(email, password);

      // Force a small delay to ensure cookies are set before checking roles
      setTimeout(() => {
        // Check if user is a driver - drivers should not access the web app
        if (hasRole(ROLES.DRIVER)) {
          // Log out the driver immediately
          logout();

          // Restore the previous theme since driver was rejected
          const root = document.documentElement;
          root.classList.remove('light', 'dark');
          root.classList.add(currentDOMTheme);

          // Restore theme in localStorage
          localStorage.setItem('theme', currentTheme);

          // Clear the form inputs
          clearForm();

          // Show error message for drivers
          setError('Drivers are not authorized to access the web application. Please download and use the driver mobile app instead.');
          setLoading(false);
          return;
        }

        // If not a driver, proceed with normal login flow
        if (onSuccess) {
          onSuccess();
        }

        // Redirect to dashboard for non-driver users
        navigate('/dashboard', {replace: true});
      }, 100);
    } catch (err) {
      setError(err.message);
    } finally {
      // Only set loading to false if we're not dealing with a driver logout scenario
      if (!hasRole(ROLES.DRIVER)) {
        setLoading(false);
      }
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

      <form className="space-y-5" onSubmit={handleSubmit}>
        {error && (
          <div
            className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative"
            role="alert"
          >
            <span className="block text-sm">{error}</span>
          </div>
        )}

        <div className="space-y-2">
          <label htmlFor="modal-email" className="block text-sm font-medium text-primary-900 dark:text-white">
            Email
          </label>
          <input
            id="modal-email"
            type="email"
            placeholder="Enter your email"
            value={email}
            onChange={e => handleChange('email', e.target.value)}
            onBlur={() => handleBlur('email')}
            required
            className={`w-full p-3 border rounded-md bg-primary-50 dark:bg-gray-700 text-primary-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all duration-200 ${validationErrors.email && touched.email
              ? 'border-red-500'
              : 'border-primary-200 dark:border-gray-600'
              }`}
          />
          {validationErrors.email && touched.email && (
            <p className="text-red-500 text-xs mt-1">{validationErrors.email}</p>
          )}
        </div>

        <div className="space-y-2">
          <label htmlFor="modal-password" className="block text-sm font-medium text-primary-900 dark:text-white">
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
            className={`w-full p-3 border rounded-md bg-primary-50 dark:bg-gray-700 text-primary-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all duration-200 ${validationErrors.password && touched.password
              ? 'border-red-500'
              : 'border-primary-200 dark:border-gray-600'
              }`}
          />
          {validationErrors.password && touched.password && (
            <p className="text-red-500 text-xs mt-1">{validationErrors.password}</p>
          )}
        </div>

        {/* Forgot Password Link */}
        <div className="text-right">
          <button
            type="button"

            onClick={() => (handleForgotPassword(email))}
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
            className="flex-1"
          >
            Cancel
          </Button>
          <Button
            type="submit"
            disabled={loading}
            className="flex-1 bg-primary-700 hover:bg-primary-800 text-white transform transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] hover:shadow-lg"
            style={{
              backgroundImage: 'linear-gradient(to right, #0855b1, #2A91CD, #0855b1)',
              backgroundSize: '200% auto',
            }}
          >
            {loading ? 'Logging in...' : 'Login'}
          </Button>
        </div>
      </form>
    </div>
  );
};

export default LoginForm;
