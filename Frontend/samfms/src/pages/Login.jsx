import React from 'react';
import { Button } from '../components/ui/button';
import { Link } from 'react-router-dom';

const Login = () => {
  return (
    <div className="min-h-screen flex flex-col md:flex-row">
      {/* Left section - Medium blue */}
      <div className="hidden md:flex md:w-1/2 bg-primary-700 flex-col justify-center items-center p-8 text-white">
        <div className="max-w-md text-center">
          <h1 className="text-4xl font-bold mb-4">SAMFMS</h1>
          <p className="text-xl mb-6">Smart Automotive Fleet Management System</p>
          <div className="mb-8">
            <p className="text-lg opacity-90">Manage your fleet with ease</p>
            <p className="opacity-80">Track, maintain, and optimize your entire fleet operations</p>
          </div>
        </div>
      </div>

      {/* Right section - Light blue */}
      <div className="w-full md:w-1/2 bg-primary-100 flex justify-center items-center p-4 md:p-8">
        <div className="w-full max-w-md bg-primary-50 p-8 rounded-lg shadow-md border border-primary-200">
          <h1 className="text-3xl font-bold mb-6 text-center text-primary-900">Login</h1>
          <form className="space-y-6">
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
                placeholder="Enter your password"
                className="w-full p-2 border border-primary-200 rounded-md bg-primary-50 text-primary-900 focus:ring-primary-700 focus:border-primary-700"
              />
            </div>

            <Button className="w-full bg-primary-700 hover:bg-primary-800 text-white">Login</Button>

            <div className="text-center text-sm text-primary-800">
              <span>Don't have an account? </span>
              <Link to="/signup" className="font-medium text-primary-700 hover:text-primary-800">
                Sign up
              </Link>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Login;
