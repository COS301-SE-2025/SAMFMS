import React, {useState, useEffect} from 'react';
import {Button} from '../components/ui/button';
import {useNavigate} from 'react-router-dom';
import {
  login,
  isAuthenticated,
  checkUserExistence,
  clearUserExistenceCache,
} from '../backend/API.js';

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
  useEffect(() => {
    // If user is already authenticated, redirect to dashboard
    if (isAuthenticated()) {
      navigate('/dashboard');
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
        navigate('/dashboard', {replace: true});
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
      <div className="hidden md:flex w-full md:w-1/2 flex-col justify-center items-center p-8 relative z-10 bg-background">
        <img
          src="/logo/logo_dark.svg"
          alt="SAMFMS Logo"
          className="h-32 mb-4 animate-fadeIn transition-all duration-300 drop-shadow-lg"
        />
        <p className="text-lg text-primary-700">Smart Fleet Management System</p>
      </div>
      {/* Right section - SVG pattern background */}
      <div className="w-full md:w-1/2 flex justify-center items-center p-4 md:p-8 relative">
        <div
          className="absolute inset-0 z-0 opacity-10 pointer-events-none"
          style={{
            backgroundImage: 'url("/logo/logo_icon_light.svg")',
            backgroundSize: '200px',
            backgroundRepeat: 'repeat',
            filter: 'blur(1px)',
          }}
        />
        <div
          className="relative z-10 w-full max-w-md bg-white p-8 rounded-lg border border-primary-300 animate-slideIn transform hover:scale-[1.01] transition-all duration-300"
          style={{
            boxShadow: '0 20px 50px rgba(8,85,177,0.4)',
            transform: 'perspective(1000px) rotateX(0deg)',
          }}
          onMouseMove={e => {
            const card = e.currentTarget;
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            const rotateX = (y - centerY) / 20;
            const rotateY = (centerX - x) / 20;

            card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
          }}
          onMouseLeave={e => {
            e.currentTarget.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg)';
          }}
        >
          {/* Mobile logo - only visible on mobile */}
          <div className="md:hidden mb-6 text-center">
            <img
              src="/logo/logo_dark.svg"
              alt="SAMFMS Logo"
              className="h-24 mx-auto mb-2 animate-fadeIn transition-all duration-300 drop-shadow-lg"
            />
            <p className="text-sm text-primary-700">Smart Fleet Management System</p>
          </div>
          <h1 className="text-3xl font-bold mb-6 text-center text-primary-900 relative">
            Login
            <span className="absolute -bottom-2 left-1/2 transform -translate-x-1/2 w-16 h-1 bg-primary-700 rounded-full"></span>
          </h1>{' '}
          <form className="space-y-6" onSubmit={handleSubmit}>
            {error && (
              <div
                className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4"
                role="alert"
              >
                <span className="block sm:inline">{error}</span>
              </div>
            )}{' '}
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
                className={`w-full p-2 border rounded-md bg-primary-50 text-primary-900 focus:ring-primary-700 focus:border-primary-700 focus:shadow-lg hover:border-primary-400 transition-all duration-200 transform hover:scale-[1.02] ${validationErrors.email && touched.email ? 'border-red-500' : 'border-primary-200'
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
                className={`w-full p-2 border rounded-md bg-primary-50 text-primary-900 focus:ring-primary-700 focus:border-primary-700 focus:shadow-lg hover:border-primary-400 transition-all duration-200 transform hover:scale-[1.02] ${validationErrors.password && touched.password
                    ? 'border-red-500'
                    : 'border-primary-200'
                  }`}
              />{' '}
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
              className="w-full bg-primary-700 hover:bg-primary-800 text-white transform transition-all duration-300 hover:scale-[1.03] active:scale-[0.98] hover:shadow-lg"
              style={{
                backgroundImage: 'linear-gradient(to right, #0855b1, #2A91CD, #0855b1)',
                backgroundSize: '200% auto',
              }}
              onMouseEnter={e => {
                e.currentTarget.style.backgroundPosition = 'right center';
              }}
              onMouseLeave={e => {
                e.currentTarget.style.backgroundPosition = 'left center';
              }}
            >
              {loading ? 'Logging in...' : 'Login'}
            </Button>{' '}
            <div className="relative my-4">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-300"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white text-primary-700">Or</span>
              </div>
            </div>
            <Button
              className="w-full flex items-center justify-center gap-2 bg-white hover:bg-gray-100 text-gray-800 border border-gray-300 transform transition-transform duration-300 hover:scale-[1.02] active:scale-[0.98] hover:shadow-md"
              onClick={() => console.log('Google login clicked')}
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 48 48">
                <path
                  fill="#FFC107"
                  d="M43.611,20.083H42V20H24v8h11.303c-1.649,4.657-6.08,8-11.303,8c-6.627,0-12-5.373-12-12
                  s5.373-12,12-12c3.059,0,5.842,1.154,7.961,3.039l5.657-5.657C34.046,6.053,29.268,4,24,4C12.955,4,4,12.955,4,24
                  s8.955,20,20,20s20-8.955,20-20C44,22.659,43.862,21.35,43.611,20.083z"
                />
                <path
                  fill="#FF3D00"
                  d="M6.306,14.691l6.571,4.819C14.655,15.108,18.961,12,24,12c3.059,0,5.842,1.154,7.961,3.039
                  l5.657-5.657C34.046,6.053,29.268,4,24,4C16.318,4,9.656,8.337,6.306,14.691z"
                />
                <path
                  fill="#4CAF50"
                  d="M24,44c5.166,0,9.86-1.977,13.409-5.192l-6.19-5.238C29.211,35.091,26.715,36,24,36
                  c-5.202,0-9.619-3.317-11.283-7.946l-6.522,5.025C9.505,39.556,16.227,44,24,44z"
                />
                <path
                  fill="#1976D2"
                  d="M43.611,20.083H42V20H24v8h11.303c-0.792,2.237-2.231,4.166-4.087,5.571
                  c0.001-0.001,0.002-0.001,0.003-0.002l6.19,5.238C36.971,39.205,44,34,44,24C44,22.659,43.862,21.35,43.611,20.083z"
                />
              </svg>{' '}
              Continue with Google
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Login;
