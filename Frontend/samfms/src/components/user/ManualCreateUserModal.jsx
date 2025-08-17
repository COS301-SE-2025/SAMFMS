import React, { useState } from 'react';
import { Button } from '../ui/button';
import { useAuth, ROLES } from '../auth/RBACUtils';

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
  const [phoneError, setPhoneError] = useState('');

  // Update form data when preselectedRole changes
  React.useEffect(() => {
    setFormData(prev => ({
      ...prev,
      role: preselectedRole,
    }));
  }, [preselectedRole]);

  // Phone number validation function
  const validatePhoneNumber = (phone) => {
    // Remove all spaces and non-digit characters except +
    const cleanPhone = phone.replace(/[\s\-\(\)]/g, '');

    // Check if it starts with +27 (South African international format)
    if (cleanPhone.startsWith('+27')) {
      const localNumber = cleanPhone.substring(3);
      // Should have 9 digits after +27
      return /^[0-9]{9}$/.test(localNumber);
    }

    // Check if it starts with 0 (South African local format)
    if (cleanPhone.startsWith('0')) {
      // Should have exactly 10 digits total (0 + 9 digits)
      return /^0[0-9]{9}$/.test(cleanPhone);
    }

    // Check if it starts with 27 (international without +)
    if (cleanPhone.startsWith('27')) {
      const localNumber = cleanPhone.substring(2);
      // Should have 9 digits after 27
      return /^[0-9]{9}$/.test(localNumber);
    }

    // If it doesn't start with 0, 27, or +27, it's invalid
    return false;
  };

  // Convert phone number to international format (+27)
  const convertToInternationalFormat = (phone) => {
    const cleanPhone = phone.replace(/[\s\-\(\)]/g, '');

    // If already in +27 format, return as is
    if (cleanPhone.startsWith('+27')) {
      return cleanPhone;
    }

    // If starts with 27 (without +), add the +
    if (cleanPhone.startsWith('27') && cleanPhone.length === 11) {
      return '+' + cleanPhone;
    }

    // If starts with 0, replace with +27
    if (cleanPhone.startsWith('0') && cleanPhone.length === 10) {
      return '+27' + cleanPhone.substring(1);
    }

    // Return original if can't convert (shouldn't happen if validation passed)
    return phone;
  };

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

    // Validate phone number in real-time
    if (name === 'phoneNo') {
      setPhoneError('');
    }
  };

  const validateForm = () => {
    // let isValid = true;

    // Validate password
    if (formData.password !== formData.confirmPassword) {
      setPasswordError('Passwords do not match');
      return false;
    }
    if (formData.password.length < 6) {
      setPasswordError('Password must be at least 6 characters long');
      return false;
    }

    // Validate phone number - required field
    if (!formData.phoneNo || formData.phoneNo.trim() === '') {
      setPhoneError('Phone number is required');
      return false;
    } else if (!validatePhoneNumber(formData.phoneNo)) {
      setPhoneError('Please enter a valid South African phone number (e.g., 0826468537, +27826468537, or 27826468537)');
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
      // Convert phone number to international format before submitting
      const formDataWithInternationalPhone = {
        ...formData,
        phoneNo: convertToInternationalFormat(formData.phoneNo)
      };

      await onSubmit(formDataWithInternationalPhone);
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
      setPhoneError('');
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
    setPhoneError('');
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
      <div className="bg-card bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 rounded-lg shadow-xl p-6 w-full max-w-2xl border border-border">
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
                maxLength="50"
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
                maxLength="50"
                required
              />
            </div>
            <div>
              <input type="hidden" name="role" value={preselectedRole} />
              <label className="block text-sm font-medium mb-1 text-foreground">Phone Number *</label>
              <input
                type="tel"
                name="phoneNo"
                value={formData.phoneNo}
                onChange={handleChange}
                className={`w-full p-2 border rounded-md bg-background text-foreground focus:ring-primary focus:border-primary ${phoneError ? 'border-destructive' : 'border-border'
                  }`}
                required
              />
              {phoneError && (
                <div className="text-sm text-destructive mt-1">
                  {phoneError}
                </div>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium mb-1 text-foreground">Password *</label>
              <input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                className="w-full p-2 border border-border rounded-md bg-background text-foreground focus:ring-primary focus:border-primary"
                maxLength="50"
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
                maxLength="50"
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
