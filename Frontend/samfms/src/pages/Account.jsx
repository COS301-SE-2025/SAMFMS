import React, {useEffect, useState} from 'react';
import {Button} from '../components/ui/button';
import {getUserInfo} from '../backend/api/auth';

const Account = () => {
  const [user, setUser] = useState(null);
  const [form, setForm] = useState({
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
  });
  const [loading, setLoading] = useState(true);

  // Fetch user info on mount
  useEffect(() => {
    const fetchUser = async () => {
      try {
        const data = await getUserInfo();
        // Assuming backend returns { first_name, last_name, email, phone }
        setUser(data);
        setForm({
          firstName: data.first_name || '',
          lastName: data.last_name || '',
          email: data.email || '',
          phone: data.phone || '',
        });
      } catch (e) {
        // Handle error (could show a toast or message)
      } finally {
        setLoading(false);
      }
    };
    fetchUser();
  }, []);

  const handleChange = e => {
    setForm({...form, [e.target.name]: e.target.value});
  };

  const handleSave = e => {
    e.preventDefault();
    // TODO: Implement update user info API call
  };

  return (
    <div className="container mx-auto py-8">
      <header className="mb-8">
        <h1 className="text-4xl font-bold">Account</h1>
        <p className="text-muted-foreground">Manage your account details and preferences</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-1">
          <div className="bg-card p-6 rounded-lg shadow-md border border-border">
            <div className="flex flex-col items-center mb-6">
              <div className="w-32 h-32 rounded-full bg-primary/20 flex items-center justify-center mb-4">
                <span className="text-4xl">
                  {user
                    ? (user.first_name?.[0] || '') + (user.last_name?.[0] || '')
                    : 'JD'}
                </span>
              </div>
              <h2 className="text-xl font-semibold">
                {user
                  ? `${user.first_name || ''} ${user.last_name || ''}`.trim()
                  : 'John Doe'}
              </h2>
              <p className="text-muted-foreground">
                {user?.role ? user.role.charAt(0).toUpperCase() + user.role.slice(1) : 'Administrator'}
              </p>
            </div>
            <div className="space-y-2">
              <Button variant="outline" className="w-full">
                Change Avatar
              </Button>
              <Button variant="outline" className="w-full">
                View Activity
              </Button>
            </div>
          </div>
        </div>

        <div className="lg:col-span-2">
          <div className="bg-card p-6 rounded-lg shadow-md border border-border mb-6">
            <h2 className="text-xl font-semibold mb-4">Personal Information</h2>
            <form className="space-y-4" onSubmit={handleSave}>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">First Name</label>
                  <input
                    type="text"
                    name="firstName"
                    value={form.firstName}
                    onChange={handleChange}
                    className="w-full p-2 border rounded-md"
                    disabled={loading}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Last Name</label>
                  <input
                    type="text"
                    name="lastName"
                    value={form.lastName}
                    onChange={handleChange}
                    className="w-full p-2 border rounded-md"
                    disabled={loading}
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Email</label>
                <input
                  type="email"
                  name="email"
                  value={form.email}
                  onChange={handleChange}
                  className="w-full p-2 border rounded-md"
                  disabled={loading}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Phone</label>
                <input
                  type="tel"
                  name="phone"
                  value={form.phone}
                  onChange={handleChange}
                  className="w-full p-2 border rounded-md"
                  disabled={loading}
                />
              </div>
              <div className="flex justify-end">
                <Button type="submit" disabled={loading}>
                  Save Changes
                </Button>
              </div>
            </form>
          </div>

          <div className="bg-card p-6 rounded-lg shadow-md border border-border">
            <h2 className="text-xl font-semibold mb-4">Security</h2>
            <form className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Current Password</label>
                <input type="password" className="w-full p-2 border rounded-md" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">New Password</label>
                <input type="password" className="w-full p-2 border rounded-md" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Confirm New Password</label>
                <input type="password" className="w-full p-2 border rounded-md" />
              </div>
              <div className="flex justify-end">
                <Button>Update Password</Button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Account;