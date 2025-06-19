import React, { useState } from 'react';
import { Button } from './ui/button';
import { useAuth, ROLES } from './RBACUtils';

const InviteUserModal = ({ isOpen, onClose, onSubmit, loading }) => {
  const { hasRole } = useAuth();
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    role: 'driver',
    phoneNo: '',
  });

  const handleChange = e => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async e => {
    e.preventDefault();
    await onSubmit(formData);
    // Reset form after successful submission
    setFormData({
      full_name: '',
      email: '',
      role: 'driver',
      phoneNo: '',
    });
  };

  const handleClose = () => {
    setFormData({
      full_name: '',
      email: '',
      role: 'driver',
      phoneNo: '',
    });
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-card rounded-lg shadow-xl p-6 w-full max-w-2xl border border-border">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold text-foreground">Invite User</h2>
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
            </div>

            <div>
              <label className="block text-sm font-medium mb-1 text-foreground">Role *</label>
              <select
                name="role"
                value={formData.role}
                onChange={handleChange}
                className="w-full p-2 border border-border rounded-md bg-background text-foreground focus:ring-primary focus:border-primary"
              >
                {hasRole(ROLES.ADMIN) && <option value="admin">Administrator</option>}
                {hasRole(ROLES.ADMIN) && <option value="fleet_manager">Fleet Manager</option>}
                <option value="driver">Driver</option>
              </select>
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
          </div>

          <div className="flex justify-end space-x-3 pt-4">
            <Button type="button" variant="outline" onClick={handleClose} disabled={loading}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? 'Sending Invitation...' : 'Send Invitation'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default InviteUserModal;
