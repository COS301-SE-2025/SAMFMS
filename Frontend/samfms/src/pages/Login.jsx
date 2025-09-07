import React, {useState, useEffect} from 'react';
import {Button} from '../components/ui/button';
import {useNavigate} from 'react-router-dom';
import {useTheme} from '../contexts/ThemeContext';
import {
  login,
  isAuthenticated,
  checkUserExistence,
  clearUserExistenceCache,
  hasRole,
} from '../backend/API.js';
import {ROLES} from '../components/auth/RBACUtils';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [checkingUsers, setCheckingUsers] = useState(true);
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
  useEffect(() => {
    // If user is already authenticated, redirect based on role
    if (isAuthenticated()) {
      if (hasRole(ROLES.DRIVER)) {
        navigate('/driver-home');
      } else {
        navigate('/dashboard');
      }
      return;
    } // Flag to track if the component is still mounted
    let isMounted = true; // Clear the cache when the Login component mounts to ensure fresh check
    clearUserExistenceCache();

    // Check if there are any users in the system
    const checkUsers = async () => {
      try {
        // Only set loading state if component is still mounted
        if (isMounted) setCheckingUsers(true);

        // Add a safety timeout promise
        const timeoutPromise = new Promise((_, reject) => {
          setTimeout(() => {
            reject(new Error('User existence check timed out'));
          }, 3000);
        });

        // Create a promise for the user existence check with a forced refresh
        const userCheckPromise = checkUserExistence(true); // Force refresh

        // Race the promises to handle timeout gracefully
        const usersExist = await Promise.race([userCheckPromise, timeoutPromise]).catch(err => {
          console.error('Error in checkUserExistence:', err);
          return true; // Default to assuming users exist if there's an error/timeout
        });

        if (!isMounted) return; // Exit if component unmounted during the check

        console.log('Users exist check result:', usersExist);

        // If no users exist, redirect to signup page
        if (usersExist === false) {
          console.log('No users exist, redirecting to signup');
          navigate('/signup');
        }
      } catch (error) {
        if (!isMounted) return;
        console.error('Error checking user existence:', error);
      } finally {
        if (isMounted) setCheckingUsers(false);
      }
    };

    checkUsers(); // Cleanup function
    return () => {
      isMounted = false;
    };
  }, [navigate]);
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
    setTouched({...touched, [field]: true});

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
        // Redirect based on user role
        if (hasRole(ROLES.DRIVER)) {
          navigate('/driver-home', {replace: true});
        } else {
          navigate('/dashboard', {replace: true});
        }
      }, 100);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  // Display loading state while checking for users
  if (checkingUsers) {
    return (
      <div className="min-h-screen flex justify-center items-center bg-background">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-primary">Checking system...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col md:flex-row overflow-hidden bg-background">
      {/* Left section - plain background - hidden on mobile */}
      <div className="hidden md:flex md:w-1/2 flex-col justify-center items-center p-8 relative z-10 bg-background">
        <img
          src={theme === 'dark' ? '/logo/logo_dark.svg' : '/logo/logo_light.svg'}
          alt="SAMFMS Logo"
          className="h-48 mb-8 animate-fadeIn transition-all duration-300 drop-shadow-lg"
        />
        <p className="text-lg text-primary-700">Smart Fleet Management System</p>
      </div>

      {/* Right section - form - full width on mobile */}
      <div className="w-full md:w-1/2 flex justify-center items-center p-4 md:p-8 relative min-h-screen md:min-h-0">
        {/* Background pattern - lighter on mobile */}
        <div
          className="absolute inset-0 z-0 opacity-5 md:opacity-10 pointer-events-none"
          style={{
            backgroundImage: 'url("/logo/logo_icon_light.svg")',
            backgroundSize: '120px 120px',
            backgroundRepeat: 'repeat',
            filter: 'blur(1px)',
          }}
        />

        <div className="relative z-10 w-full max-w-md mx-auto">
          {/* Mobile logo - only visible on mobile */}
          <div className="md:hidden mb-6 text-center">
            <img
              src={theme === 'dark' ? '/logo/logo_dark.svg' : '/logo/logo_light.svg'}
              alt="SAMFMS Logo"
              className="h-24 mx-auto mb-3 animate-fadeIn transition-all duration-300 drop-shadow-lg"
            />
            <p className="text-sm text-primary-700 font-medium">Smart Fleet Management System</p>
          </div>

          {/* Login form card */}
          <div
            className="bg-white p-6 md:p-8 rounded-lg border border-primary-300 shadow-lg md:shadow-xl animate-slideIn transform transition-all duration-300 hover:shadow-2xl"
            style={{
              boxShadow: '0 4px 20px rgba(8,85,177,0.15)',
            }}
          >
            <h1 className="text-2xl md:text-3xl font-bold mb-6 text-center text-primary-900 relative">
              Login
              <span className="absolute -bottom-2 left-1/2 transform -translate-x-1/2 w-16 h-1 bg-primary-700 rounded-full"></span>
            </h1>

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
                <label htmlFor="email" className="block text-sm font-medium text-primary-900">
                  Email
                </label>
                <input
                  id="email"
                  type="email"
                  placeholder="Enter your email"
                  value={email}
                  onChange={e => handleChange('email', e.target.value)}
                  onBlur={() => handleBlur('email')}
                  required
                  className={`w-full p-3 border rounded-md bg-primary-50 text-primary-900 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all duration-200 ${validationErrors.email && touched.email
                      ? 'border-red-500'
                      : 'border-primary-200'
                    }`}
                />
                {validationErrors.email && touched.email && (
                  <p className="text-red-500 text-xs mt-1">{validationErrors.email}</p>
                )}
              </div>

              <div className="space-y-2">
                <label htmlFor="password" className="block text-sm font-medium text-primary-900">
                  Password
                </label>
                <input
                  id="password"
                  type="password"
                  placeholder="Enter your password"
                  value={password}
                  onChange={e => handleChange('password', e.target.value)}
                  onBlur={() => handleBlur('password')}
                  required
                  className={`w-full p-3 border rounded-md bg-primary-50 text-primary-900 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all duration-200 ${validationErrors.password && touched.password
                      ? 'border-red-500'
                      : 'border-primary-200'
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
                  onClick={() => console.log('Forgot password clicked')}
                  className="text-sm text-primary-700 hover:text-primary-800 hover:underline focus:outline-none focus:underline transition-colors duration-200"
                >
                  Forgot your password?
                </button>
              </div>

              <Button
                type="submit"
                disabled={loading}
                className="w-full py-3 bg-primary-700 hover:bg-primary-800 text-white transform transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] hover:shadow-lg"
                style={{
                  backgroundImage: 'linear-gradient(to right, #0855b1, #2A91CD, #0855b1)',
                  backgroundSize: '200% auto',
                }}
              >
                {loading ? 'Logging in...' : 'Login'}
              </Button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
