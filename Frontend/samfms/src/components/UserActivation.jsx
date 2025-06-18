import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button } from './ui/button';
import { verifyInvitationOTP, completeUserRegistration } from '../backend/API.js';

const UserActivation = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [step, setStep] = useState(1); // 1: Email & OTP, 2: Complete Registration
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Form data
  const [formData, setFormData] = useState({
    email: '',
    otp: '',
    password: '',
    confirmPassword: '',
  });

  // Verified user data from OTP verification
  const [verifiedUser, setVerifiedUser] = useState(null);

  // Real-time validation states
  const [validation, setValidation] = useState({
    passwordStrength: '',
    passwordsMatch: false,
    otpValid: false,
  });

  // Extract email from URL parameters on component mount
  useEffect(() => {
    const urlParams = new URLSearchParams(location.search);
    const emailParam = urlParams.get('email');

    if (emailParam) {
      setFormData(prevData => ({
        ...prevData,
        email: emailParam,
      }));
    }
  }, [location.search]);

  // Real-time validation
  useEffect(() => {
    const validatePassword = password => {
      const checks = [
        { test: /.{8,}/, label: 'At least 8 characters' },
        { test: /[A-Z]/, label: 'One uppercase letter' },
        { test: /[a-z]/, label: 'One lowercase letter' },
        { test: /\d/, label: 'One number' },
      ];

      const passed = checks.filter(check => check.test.test(password)).length;

      if (passed === 0) return { strength: 'none', message: 'Enter a password' };
      if (passed < 2) return { strength: 'weak', message: 'Weak password' };
      if (passed < 3) return { strength: 'medium', message: 'Medium password' };
      if (passed < 4) return { strength: 'good', message: 'Good password' };
      return { strength: 'strong', message: 'Strong password' };
    };

    const passwordValidation = validatePassword(formData.password);
    setValidation(prev => ({
      ...prev,
      passwordStrength: passwordValidation,
      passwordsMatch:
        formData.password === formData.confirmPassword && formData.password.length > 0,
      otpValid: /^\d{6}$/.test(formData.otp),
    }));
  }, [formData.password, formData.confirmPassword, formData.otp]);

  const handleOTPSubmit = async e => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!formData.email || !formData.otp) {
      setError('Please enter both email and OTP');
      return;
    }

    if (!validation.otpValid) {
      setError('OTP must be exactly 6 digits');
      return;
    }

    try {
      setLoading(true);
      const result = await verifyInvitationOTP(formData.email, formData.otp);
      setVerifiedUser(result);
      setSuccess('OTP verified successfully! Please complete your registration.');
      setStep(2);
    } catch (err) {
      setError(err.message || 'Invalid OTP or email');
    } finally {
      setLoading(false);
    }
  };

  const handleRegistrationSubmit = async e => {
    e.preventDefault();
    setError('');
    setSuccess('');

    // Validation
    if (!formData.password || !formData.confirmPassword) {
      setError('Please fill in all required fields');
      return;
    }

    if (!validation.passwordsMatch) {
      setError('Passwords do not match');
      return;
    }

    if (
      validation.passwordStrength.strength === 'weak' ||
      validation.passwordStrength.strength === 'none'
    ) {
      setError('Please choose a stronger password');
      return;
    }

    try {
      setLoading(true);
      const result = await completeUserRegistration(
        formData.email,
        formData.otp,
        null, // username is optional now
        formData.password
      );

      setSuccess('Registration completed successfully! Redirecting to dashboard...');

      // Store the token and redirect
      localStorage.setItem('authToken', result.access_token);
      setTimeout(() => {
        navigate('/dashboard');
      }, 2000);
    } catch (err) {
      setError(err.message || 'Failed to complete registration');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));
    // Clear errors when user types
    if (error) setError('');
  };

  const getPasswordStrengthColor = strength => {
    switch (strength) {
      case 'weak':
        return 'text-red-600';
      case 'medium':
        return 'text-yellow-600';
      case 'good':
        return 'text-blue-600';
      case 'strong':
        return 'text-green-600';
      default:
        return 'text-gray-400';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
          {step === 1 ? 'Activate Your Account' : 'Complete Registration'}
        </h2>
        <p className="mt-2 text-center text-sm text-gray-600">
          {step === 1
            ? 'Enter your email and the OTP you received to continue'
            : 'Choose a secure password to complete setup'}
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          {error && (
            <div className="mb-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}

          {success && (
            <div className="mb-4 bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">
              {success}
            </div>
          )}

          {step === 1 ? (
            <form onSubmit={handleOTPSubmit} className="space-y-6">
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                  Email Address
                </label>
                <div className="mt-1">
                  <input
                    id="email"
                    name="email"
                    type="email"
                    autoComplete="email"
                    required
                    value={formData.email}
                    onChange={e => handleInputChange('email', e.target.value)}
                    className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                    placeholder="Enter your email address"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="otp" className="block text-sm font-medium text-gray-700">
                  One-Time Password (OTP)
                </label>
                <div className="mt-1">
                  <input
                    id="otp"
                    name="otp"
                    type="text"
                    required
                    maxLength="6"
                    value={formData.otp}
                    onChange={e => handleInputChange('otp', e.target.value.replace(/\D/g, ''))}
                    className={`appearance-none block w-full px-3 py-2 border rounded-md placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm ${
                      formData.otp.length > 0 && !validation.otpValid
                        ? 'border-red-300'
                        : 'border-gray-300'
                    }`}
                    placeholder="Enter 6-digit OTP"
                  />
                </div>
                <p className="mt-1 text-xs text-gray-500">
                  Check your email for the OTP code
                  {formData.otp.length > 0 && !validation.otpValid && (
                    <span className="text-red-600 ml-2">• Must be exactly 6 digits</span>
                  )}
                </p>
              </div>

              <div>
                <Button
                  type="submit"
                  disabled={loading || !validation.otpValid}
                  className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                >
                  {loading ? 'Verifying...' : 'Verify OTP'}
                </Button>
              </div>
            </form>
          ) : (
            <form onSubmit={handleRegistrationSubmit} className="space-y-6">
              {verifiedUser && (
                <div className="bg-blue-50 border border-blue-200 rounded-md p-4 mb-4">
                  <h3 className="text-sm font-medium text-blue-800">
                    Welcome, {verifiedUser.full_name}!
                  </h3>{' '}
                  <p className="text-sm text-blue-600 mt-1">
                    You're being registered as:{' '}
                    <strong>
                      {verifiedUser.role
                        ? verifiedUser.role.replace('_', ' ').toUpperCase()
                        : 'USER'}
                    </strong>
                  </p>
                </div>
              )}

              <div>
                <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                  Password
                </label>
                <div className="mt-1">
                  <input
                    id="password"
                    name="password"
                    type="password"
                    required
                    value={formData.password}
                    onChange={e => handleInputChange('password', e.target.value)}
                    className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                    placeholder="Choose a secure password"
                  />
                </div>
                {formData.password && (
                  <p
                    className={`mt-1 text-xs ${getPasswordStrengthColor(
                      validation.passwordStrength.strength
                    )}`}
                  >
                    {validation.passwordStrength.message}
                  </p>
                )}
                <p className="mt-1 text-xs text-gray-500">
                  Must contain: 8+ characters, uppercase, lowercase, and number
                </p>
              </div>

              <div>
                <label
                  htmlFor="confirmPassword"
                  className="block text-sm font-medium text-gray-700"
                >
                  Confirm Password
                </label>
                <div className="mt-1">
                  <input
                    id="confirmPassword"
                    name="confirmPassword"
                    type="password"
                    required
                    value={formData.confirmPassword}
                    onChange={e => handleInputChange('confirmPassword', e.target.value)}
                    className={`appearance-none block w-full px-3 py-2 border rounded-md placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm ${
                      formData.confirmPassword.length > 0 && !validation.passwordsMatch
                        ? 'border-red-300'
                        : 'border-gray-300'
                    }`}
                    placeholder="Confirm your password"
                  />
                </div>
                {formData.confirmPassword.length > 0 && (
                  <p
                    className={`mt-1 text-xs ${
                      validation.passwordsMatch ? 'text-green-600' : 'text-red-600'
                    }`}
                  >
                    {validation.passwordsMatch ? '✓ Passwords match' : '✗ Passwords do not match'}
                  </p>
                )}
              </div>

              <div className="flex space-x-3">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setStep(1)}
                  disabled={loading}
                  className="flex-1"
                >
                  Back
                </Button>
                <Button
                  type="submit"
                  disabled={
                    loading ||
                    !validation.passwordsMatch ||
                    validation.passwordStrength.strength === 'weak' ||
                    validation.passwordStrength.strength === 'none'
                  }
                  className="flex-1 flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                >
                  {loading ? 'Creating Account...' : 'Complete Registration'}
                </Button>
              </div>
            </form>
          )}

          <div className="mt-6">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-300" />
              </div>
            </div>
            <div className="mt-6">
              <p className="text-center text-sm text-gray-600">
                Already have an account?{' '}
                <button
                  onClick={() => navigate('/login')}
                  className="font-medium text-indigo-600 hover:text-indigo-500"
                >
                  Sign in here
                </button>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UserActivation;
