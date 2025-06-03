import React, { useState, useEffect } from 'react';
import { Button } from '../components/ui/button';
import { Link, useNavigate } from 'react-router-dom';
import { signup, isAuthenticated } from '../backend/api/auth.js';

const Signup = () => {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [phone, setPhone] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [validationErrors, setValidationErrors] = useState({
    fullName: '',
    email: '',
    password: '',
    confirmPassword: '',
    phone: '',
  });
  const [touched, setTouched] = useState({
    fullName: false,
    email: false,
    password: false,
    confirmPassword: false,
    phone: false,
  });
  const navigate = useNavigate();

  useEffect(() => {
    // If user is already authenticated, redirect to dashboard
    if (isAuthenticated()) {
      navigate('/dashboard');
    }
  }, [navigate]);
  // Validate full name
  const validateFullName = name => {
    if (!name.trim()) {
      return 'Full name is required';
    } else if (name.trim().length < 2) {
      return 'Name must be at least 2 characters';
    }
    return '';
  };

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
    if (!password) {
      return 'Password is required';
    } else if (password.length < 8) {
      return 'Password must be at least 8 characters long';
    } else if (!/(?=.*[A-Z])/.test(password)) {
      return 'Password must contain at least one uppercase letter';
    } else if (!/(?=.*[a-z])/.test(password)) {
      return 'Password must contain at least one lowercase letter';
    } else if (!/(?=.*\d)/.test(password)) {
      return 'Password must contain at least one number';
    }
    return '';
  };

  // Validate confirm password
  const validateConfirmPassword = (confirmPass, pass) => {
    if (!confirmPass) {
      return 'Please confirm your password';
    } else if (confirmPass !== pass) {
      return 'Passwords do not match';
    }
    return '';
  };

  // Validate phone
  const validatePhone = phone => {
    // Phone is optional, so no validation if empty
    if (!phone) {
      return '';
    }
    const phoneRegex = /^\+?[0-9\s\-()]{8,20}$/;
    if (!phoneRegex.test(phone)) {
      return 'Invalid phone format';
    }
    return '';
  };

  // Handle blur events
  const handleBlur = field => {
    setTouched({ ...touched, [field]: true });

    let error = '';
    switch (field) {
      case 'fullName':
        error = validateFullName(fullName);
        break;
      case 'email':
        error = validateEmail(email);
        break;
      case 'password':
        error = validatePassword(password);
        break;
      case 'confirmPassword':
        error = validateConfirmPassword(confirmPassword, password);
        break;
      case 'phone':
        error = validatePhone(phone);
        break;
      default:
        break;
    }

    setValidationErrors({
      ...validationErrors,
      [field]: error,
    });
  };

  // Handle change events with validation
  const handleChange = (field, value) => {
    switch (field) {
      case 'fullName':
        setFullName(value);
        if (touched.fullName) {
          setValidationErrors({
            ...validationErrors,
            fullName: validateFullName(value),
          });
        }
        break;
      case 'email':
        setEmail(value);
        if (touched.email) {
          setValidationErrors({
            ...validationErrors,
            email: validateEmail(value),
          });
        }
        break;
      case 'password':
        setPassword(value);
        if (touched.password) {
          setValidationErrors({
            ...validationErrors,
            password: validatePassword(value),
          });
        }
        // Also update confirm password validation if it's been touched
        if (touched.confirmPassword) {
          setValidationErrors(prev => ({
            ...prev,
            confirmPassword: validateConfirmPassword(confirmPassword, value),
          }));
        }
        break;
      case 'confirmPassword':
        setConfirmPassword(value);
        if (touched.confirmPassword) {
          setValidationErrors({
            ...validationErrors,
            confirmPassword: validateConfirmPassword(value, password),
          });
        }
        break;
      case 'phone':
        setPhone(value);
        if (touched.phone) {
          setValidationErrors({
            ...validationErrors,
            phone: validatePhone(value),
          });
        }
        break;
      default:
        break;
    }
  };

  const handleSubmit = async e => {
    e.preventDefault();

    // Validate all fields
    const fullNameError = validateFullName(fullName);
    const emailError = validateEmail(email);
    const passwordError = validatePassword(password);
    const confirmPasswordError = validateConfirmPassword(confirmPassword, password);
    const phoneError = validatePhone(phone);

    setValidationErrors({
      fullName: fullNameError,
      email: emailError,
      password: passwordError,
      confirmPassword: confirmPasswordError,
      phone: phoneError,
    });

    setTouched({
      fullName: true,
      email: true,
      password: true,
      confirmPassword: true,
      phone: true,
    });

    // If any validation errors, prevent form submission
    if (fullNameError || emailError || passwordError || confirmPasswordError || phoneError) {
      return;
    }

    setError('');
    setLoading(true);

    try {
      const response = await signup(fullName, email, password, confirmPassword, phone);
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Signup failed');
      }
      // Signup was successful, redirect to login
      navigate('/login');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col md:flex-row overflow-hidden">
      {/* Left section - Medium blue with animated background */}
      <div
        className="hidden md:flex md:w-1/2 flex-col justify-center items-center p-8 text-white shadow-2xl relative z-10 overflow-hidden"
        style={{
          backgroundImage: 'linear-gradient(125deg, #010e54, #0855b1, #2A91CD, #010e54)',
          backgroundSize: '400% 400%',
          animation: 'wave 10s ease infinite',
        }}
      >
        {/* Animated background elements */}
        <div className="absolute inset-0 opacity-20">
          <div
            className="absolute top-[10%] left-[20%] h-64 w-64 rounded-full bg-primary-700 mix-blend-overlay animate-float"
            style={{ animationDelay: '0s' }}
          ></div>
          <div
            className="absolute bottom-[15%] right-[15%] h-48 w-48 rounded-full bg-primary-500 mix-blend-overlay animate-float"
            style={{ animationDelay: '2s' }}
          ></div>
          <div
            className="absolute top-[30%] right-[30%] h-32 w-32 rounded-full bg-primary-600 mix-blend-overlay animate-float"
            style={{ animationDelay: '4s' }}
          ></div>
        </div>

        <div className="max-w-md text-center relative z-10 transform hover:scale-105 transition-transform duration-500">
          <img
            src="/logo/logo_dark.svg"
            alt="SAMFMS Logo"
            className="h-64 mx-auto mb-6 animate-fadeIn animate-float hover:animate-pulse hover:animate-none transition-all duration-300 drop-shadow-xl transform hover:rotate-3 hover:brightness-110"
          />
        </div>
      </div>

      {/* Right section - Light blue */}
      <div className="w-full md:w-1/2 bg-primary-200 flex justify-center items-center p-4 md:p-8">
        <div
          className="w-full max-w-md bg-foreground p-8 rounded-lg border border-primary-300 animate-slideIn transform hover:scale-[1.01] transition-all duration-300"
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
          <div className="md:hidden mb-6 text-center">
            <img
              src="/logo/logo_dark.svg"
              alt="SAMFMS Logo"
              className="h-24 mx-auto mb-2 animate-fadeIn animate-float hover:animate-pulse hover:animate-none transition-all duration-300 drop-shadow-lg"
            />
            <p className="text-sm text-primary-700">Smart Fleet Management System</p>
          </div>
          <h1 className="text-3xl font-bold mb-6 text-center text-primary-900 relative">
            Sign Up
            <span className="absolute -bottom-2 left-1/2 transform -translate-x-1/2 w-16 h-1 bg-primary-700 rounded-full"></span>
          </h1>{' '}
          <form className="space-y-4" onSubmit={handleSubmit}>
            {error && (
              <div
                className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4"
                role="alert"
              >
                <span className="block sm:inline">{error}</span>
              </div>
            )}{' '}
            <div className="space-y-2">
              <label htmlFor="name" className="block text-sm font-medium text-primary-900">
                Full Name
              </label>
              <input
                id="name"
                type="text"
                placeholder="Enter your full name"
                value={fullName}
                onChange={e => handleChange('fullName', e.target.value)}
                onBlur={() => handleBlur('fullName')}
                required
                className={`w-full p-2 border rounded-md bg-primary-50 text-primary-900 focus:ring-primary-700 focus:border-primary-700 focus:shadow-lg hover:border-primary-400 transition-all duration-200 transform hover:scale-[1.02] ${
                  validationErrors.fullName && touched.fullName
                    ? 'border-red-500'
                    : 'border-primary-200'
                }`}
              />
              {validationErrors.fullName && touched.fullName && (
                <p className="text-red-500 text-xs mt-1">{validationErrors.fullName}</p>
              )}
            </div>
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
                className={`w-full p-2 border rounded-md bg-primary-50 text-primary-900 focus:ring-primary-700 focus:border-primary-700 focus:shadow-lg hover:border-primary-400 transition-all duration-200 transform hover:scale-[1.02] ${
                  validationErrors.email && touched.email ? 'border-red-500' : 'border-primary-200'
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
                placeholder="Create a password"
                value={password}
                onChange={e => handleChange('password', e.target.value)}
                onBlur={() => handleBlur('password')}
                required
                className={`w-full p-2 border rounded-md bg-primary-50 text-primary-900 focus:ring-primary-700 focus:border-primary-700 focus:shadow-lg hover:border-primary-400 transition-all duration-200 transform hover:scale-[1.02] ${
                  validationErrors.password && touched.password
                    ? 'border-red-500'
                    : 'border-primary-200'
                }`}
              />
              {validationErrors.password && touched.password && (
                <p className="text-red-500 text-xs mt-1">{validationErrors.password}</p>
              )}
            </div>
            <div className="space-y-2">
              <label
                htmlFor="confirmPassword"
                className="block text-sm font-medium text-primary-900"
              >
                Confirm Password
              </label>
              <input
                id="confirmPassword"
                type="password"
                placeholder="Confirm your password"
                value={confirmPassword}
                onChange={e => handleChange('confirmPassword', e.target.value)}
                onBlur={() => handleBlur('confirmPassword')}
                required
                className={`w-full p-2 border rounded-md bg-primary-50 text-primary-900 focus:ring-primary-700 focus:border-primary-700 focus:shadow-lg hover:border-primary-400 transition-all duration-200 transform hover:scale-[1.02] ${
                  validationErrors.confirmPassword && touched.confirmPassword
                    ? 'border-red-500'
                    : 'border-primary-200'
                }`}
              />
              {validationErrors.confirmPassword && touched.confirmPassword && (
                <p className="text-red-500 text-xs mt-1">{validationErrors.confirmPassword}</p>
              )}
            </div>
            <div className="space-y-2">
              <label htmlFor="phone" className="block text-sm font-medium text-primary-900">
                Phone Number (optional)
              </label>
              <input
                id="phone"
                type="tel"
                placeholder="Enter your phone number"
                value={phone}
                onChange={e => handleChange('phone', e.target.value)}
                onBlur={() => handleBlur('phone')}
                className={`w-full p-2 border rounded-md bg-primary-50 text-primary-900 focus:ring-primary-700 focus:border-primary-700 focus:shadow-lg hover:border-primary-400 transition-all duration-200 transform hover:scale-[1.02] ${
                  validationErrors.phone && touched.phone ? 'border-red-500' : 'border-primary-200'
                }`}
              />
              {validationErrors.phone && touched.phone && (
                <p className="text-red-500 text-xs mt-1">{validationErrors.phone}</p>
              )}
            </div>{' '}
            <Button
              type="submit"
              disabled={loading}
              className="w-full bg-primary-700 hover:bg-primary-800 text-white mt-6 transform transition-all duration-300 hover:scale-[1.03] active:scale-[0.98] hover:shadow-lg"
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
              {loading ? 'Creating Account...' : 'Sign Up'}
            </Button>
            <div className="relative my-4">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-300"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-foreground text-primary-700">Or</span>
              </div>
            </div>
            <Button
              className="w-full flex items-center justify-center gap-2 bg-white hover:bg-gray-100 text-gray-800 border border-gray-300 transform transition-transform duration-300 hover:scale-[1.02] active:scale-[0.98] hover:shadow-md"
              onClick={() => console.log('Google signup clicked')}
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
              </svg>
              Continue with Google
            </Button>
            <div className="text-center text-sm text-primary-800 mt-4">
              <span>Already have an account? </span>
              <Link
                to="/login"
                className="font-medium text-primary-700 hover:text-primary-800 hover:underline transition-all duration-200"
              >
                Login
              </Link>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Signup;
