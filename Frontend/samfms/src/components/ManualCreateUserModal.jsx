import React, { useState } from 'react';
import { Button } from './ui/button';
import { useAuth, ROLES } from './RBACUtils';

const ManualCreateUserModal = ({
  isOpen,
  onClose,
  onSubmit,
  loading,
  preselectedRole = 'driver',
}) => {
  const { hasRole } = useAuth();
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    role: preselectedRole,
    password: '',
    confirmPassword: '',
    phoneNo: '',
  });
  const [passwordError, setPasswordError] = useState('');

  // Update form data when preselectedRole changes
  React.useEffect(() => {
    setFormData(prev => ({
      ...prev,
      role: preselectedRole,
    }));
  }, [preselectedRole]);

  const handleChange = e => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));

    // Clear password error when user starts typing
    if (name === 'password' || name === 'confirmPassword') {
      setPasswordError('');
    }
  };

  const validateForm = () => {
    if (formData.password !== formData.confirmPassword) {
      setPasswordError('Passwords do not match');
      return false;
    }
    if (formData.password.length < 6) {
      setPasswordError('Password must be at least 6 characters long');
      return false;
    }
    return true;
  };
  const handleSubmit = async e => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    try {
      await onSubmit(formData);
      // Reset form after successful submission
      setFormData({
        full_name: '',
        email: '',
        role: preselectedRole,
        password: '',
        confirmPassword: '',
        phoneNo: '',
      });
      setPasswordError('');
    } catch (error) {
      console.error('Error in form submission:', error);
      // Don't reset form if there's an error
    }
  };

  const handleClose = () => {
    setFormData({
      full_name: '',
      email: '',
      role: preselectedRole,
      password: '',
      confirmPassword: '',
      phoneNo: '',
    });
    setPasswordError('');
    onClose();
  };

  // Get the display name for the role
  const getRoleDisplayName = role => {
    switch (role) {
      case 'admin':
        return 'Administrator';
      case 'fleet_manager':
        return 'Fleet Manager';
      case 'driver':
        return 'Driver';
      default:
        return 'User';
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-card rounded-lg shadow-xl p-6 w-full max-w-2xl border border-border">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold text-foreground">
            Add {getRoleDisplayName(preselectedRole)}
          </h2>
          <button
            onClick={handleClose}
            className="text-muted-foreground hover:text-foreground text-2xl"
          >
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1 text-foreground">Full Name *</label>
              <input
                type="text"
                name="full_name"
                value={formData.full_name}
                onChange={handleChange}
                className="w-full p-2 border border-border rounded-md bg-background text-foreground focus:ring-primary focus:border-primary"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1 text-foreground">Email *</label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                className="w-full p-2 border border-border rounded-md bg-background text-foreground focus:ring-primary focus:border-primary"
                required
              />
            </div>{' '}
            <div>
              <label className="block text-sm font-medium mb-1 text-foreground">Role *</label>
              <select
                name="role"
                value={formData.role}
                onChange={handleChange}
                disabled={true}
                className="w-full p-2 border border-border rounded-md bg-muted text-foreground focus:ring-primary focus:border-primary cursor-not-allowed"
              >
                {hasRole(ROLES.ADMIN) && <option value="admin">Administrator</option>}
                {hasRole(ROLES.ADMIN) && <option value="fleet_manager">Fleet Manager</option>}
                <option value="driver">Driver</option>
              </select>
              <p className="text-xs text-muted-foreground mt-1">
                Role is pre-selected based on the table you're adding to
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1 text-foreground">Phone Number</label>
              <input
                type="tel"
                name="phoneNo"
                value={formData.phoneNo}
                onChange={handleChange}
                className="w-full p-2 border border-border rounded-md bg-background text-foreground focus:ring-primary focus:border-primary"
                placeholder="Optional"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1 text-foreground">Password *</label>
              <input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                className="w-full p-2 border border-border rounded-md bg-background text-foreground focus:ring-primary focus:border-primary"
                required
                minLength="6"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1 text-foreground">
                Confirm Password *
              </label>
              <input
                type="password"
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleChange}
                className="w-full p-2 border border-border rounded-md bg-background text-foreground focus:ring-primary focus:border-primary"
                required
                minLength="6"
              />
            </div>
          </div>
          {passwordError && (
            <div className="text-sm text-destructive bg-destructive/10 p-2 rounded border border-destructive/20">
              {passwordError}
            </div>
          )}{' '}
          <div className="flex justify-end space-x-3 pt-4">
            <Button type="button" variant="outline" onClick={handleClose} disabled={loading}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? 'Creating User...' : 'Create User'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ManualCreateUserModal;
