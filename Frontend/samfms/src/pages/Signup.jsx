import React from 'react';
import { Button } from '../components/ui/button';
import { Link } from 'react-router-dom';

const Signup = () => {
  return (
    <div className="min-h-screen flex flex-col md:flex-row">
      {' '}
      {/* Left section - Medium blue */}
      <div className="hidden md:flex md:w-1/2 bg-primary-700 flex-col justify-center items-center p-8 text-white">
        <div className="max-w-md text-center">
          <img src="/logo/logo_light.png" alt="SAMFMS Logo" className="h-24 mx-auto mb-6" />
          <p className="text-xl mb-6">Smart Automotive Fleet Management System</p>
          <div className="mb-8">
            <p className="text-lg opacity-90">Join our fleet management platform</p>
            <p className="opacity-80">Get started with comprehensive fleet management tools</p>
          </div>
        </div>
      </div>
      {/* Right section - Light blue */}
      <div className="w-full md:w-1/2 bg-primary-100 flex justify-center items-center p-4 md:p-8">
        <div className="w-full max-w-md bg-primary-50 p-8 rounded-lg shadow-md border border-primary-200">
          <div className="md:hidden mb-6 text-center">
            <img src="/logo/logo_dark.png" alt="SAMFMS Logo" className="h-16 mx-auto mb-2" />
            <p className="text-sm text-primary-700">Smart Fleet Management System</p>
          </div>
          <h1 className="text-3xl font-bold mb-6 text-center text-primary-900">Sign Up</h1>
          <form className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="name" className="block text-sm font-medium text-primary-900">
                Full Name
              </label>
              <input
                id="name"
                type="text"
                placeholder="Enter your full name"
                className="w-full p-2 border border-primary-200 rounded-md bg-primary-50 text-primary-900 focus:ring-primary-700 focus:border-primary-700"
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="email" className="block text-sm font-medium text-primary-900">
                Email
              </label>
              <input
                id="email"
                type="email"
                placeholder="Enter your email"
                className="w-full p-2 border border-primary-200 rounded-md bg-primary-50 text-primary-900 focus:ring-primary-700 focus:border-primary-700"
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="password" className="block text-sm font-medium text-primary-900">
                Password
              </label>
              <input
                id="password"
                type="password"
                placeholder="Create a password"
                className="w-full p-2 border border-primary-200 rounded-md bg-primary-50 text-primary-900 focus:ring-primary-700 focus:border-primary-700"
              />
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
                className="w-full p-2 border border-primary-200 rounded-md bg-primary-50 text-primary-900 focus:ring-primary-700 focus:border-primary-700"
              />
            </div>

            <Button className="w-full bg-primary-700 hover:bg-primary-800 text-white mt-6">
              Sign Up
            </Button>

            <div className="text-center text-sm text-primary-800 mt-4">
              <span>Already have an account? </span>
              <Link to="/login" className="font-medium text-primary-700 hover:text-primary-800">
                Login
              </Link>
            </div>
          </form>
        </div>{' '}
      </div>
    </div>
  );
};

export default Signup;
