import React from 'react';
import { Button } from '../components/ui/button';

const Login = () => {
  return (
    <div className="container mx-auto py-8">
      <div className="max-w-md mx-auto bg-card p-8 rounded-lg shadow-md">
        <h1 className="text-3xl font-bold mb-6 text-center">Login</h1>
        <form className="space-y-4">
          <div className="space-y-2">
            <label htmlFor="email" className="block text-sm font-medium">
              Email
            </label>
            <input
              id="email"
              type="email"
              placeholder="Enter your email"
              className="w-full p-2 border rounded-md"
            />
          </div>
          <div className="space-y-2">
            <label htmlFor="password" className="block text-sm font-medium">
              Password
            </label>
            <input
              id="password"
              type="password"
              placeholder="Enter your password"
              className="w-full p-2 border rounded-md"
            />
          </div>
          <Button className="w-full">Login</Button>
        </form>
      </div>
    </div>
  );
};

export default Login;
