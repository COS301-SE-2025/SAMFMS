import React, { useState } from 'react';
import { X, User, Phone, Mail, Calendar, Building, CreditCard } from 'lucide-react';
import { createDriver } from '../../backend/API';

const AddDriverModal = ({ closeModal, onDriverAdded }) => {
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    phoneNo: '',
    license_number: '',
    license_type: 'Code B (Light Motor Vehicle)',
    license_expiry: '',
    department: '',
    joining_date: '',
    emergency_contact: '',
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleInputChange = e => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  };
  const handleSubmit = async e => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      // Validate required fields
      if (
        !formData.full_name ||
        !formData.email ||
        !formData.license_number ||
        !formData.license_expiry
      ) {
        throw new Error('Please fill in all required fields');
      }

      // Validate email format
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(formData.email)) {
        throw new Error('Please enter a valid email address');
      }

      // Validate phone number format (South African format)
      if (formData.phoneNo) {
        const phoneRegex = /^(\+27|0)[1-9][0-9]{8}$/;
        if (!phoneRegex.test(formData.phoneNo.replace(/\s+/g, ''))) {
          throw new Error(
            'Please enter a valid South African phone number (e.g., +27123456789 or 0123456789)'
          );
        }
      }

      // Validate emergency contact format if provided
      if (formData.emergency_contact) {
        const emergencyPhoneRegex = /^(\+27|0)[1-9][0-9]{8}$/;
        if (!emergencyPhoneRegex.test(formData.emergency_contact.replace(/\s+/g, ''))) {
          throw new Error('Please enter a valid South African emergency contact number');
        }
      } // Auto-generate employee ID if not provided
      const submissionData = {
        ...formData,
      };

      // Create driver
      const newDriver = await createDriver(submissionData);

      // Call the callback to refresh the drivers list
      if (onDriverAdded) {
        onDriverAdded(newDriver);
      }

      // Close modal
      closeModal();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  const licenseTypes = [
    'Code EB (Light Motor Vehicle)',
    'Code B (Light Motor Vehicle)',
    'Code C1 (Medium Heavy Vehicle)',
    'Code C (Heavy Vehicle)',
    'Code EC1 (Medium Heavy Vehicle with Trailer)',
    'Code EC (Heavy Vehicle with Trailer)',
    'Code A (Motorcycle)',
    'Code A1 (Light Motorcycle)',
    'Professional Driving Permit (PrDP)',
  ];
  const departments = ['Sales', 'Operations', 'Delivery', 'Executive', 'Support', 'Maintenance'];

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-card w-full max-w-2xl rounded-lg shadow-xl overflow-hidden max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold">Add New Driver</h2>
            <button
              onClick={closeModal}
              className="text-muted-foreground hover:text-foreground"
              disabled={loading}
            >
              <X size={24} />
            </button>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-destructive/10 border border-destructive/20 rounded-md text-destructive text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Personal Information */}
            <div>
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <User size={20} />
                Personal Information
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Full Name <span className="text-destructive">*</span>
                  </label>
                  <input
                    type="text"
                    name="full_name"
                    value={formData.full_name}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-input rounded-md bg-background"
                    placeholder="Enter full name"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Email <span className="text-destructive">*</span>
                  </label>
                  <div className="relative">
                    <Mail
                      size={16}
                      className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground"
                    />
                    <input
                      type="email"
                      name="email"
                      value={formData.email}
                      onChange={handleInputChange}
                      className="w-full pl-10 pr-3 py-2 border border-input rounded-md bg-background"
                      placeholder="Enter email address"
                      required
                    />
                  </div>
                </div>{' '}
                <div>
                  <label className="block text-sm font-medium mb-2">Phone Number</label>
                  <div className="relative">
                    <Phone
                      size={16}
                      className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground"
                    />
                    <input
                      type="tel"
                      name="phoneNo"
                      value={formData.phoneNo}
                      onChange={handleInputChange}
                      className="w-full pl-10 pr-3 py-2 border border-input rounded-md bg-background"
                      placeholder="+27123456789 or 0123456789"
                    />
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    South African format: +27123456789 or 0123456789
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Emergency Contact (Optional)
                  </label>
                  <input
                    type="tel"
                    name="emergency_contact"
                    value={formData.emergency_contact}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-input rounded-md bg-background"
                    placeholder="+27123456789 or 0123456789"
                  />
                  <p className="text-xs text-muted-foreground mt-1">
                    Optional: Emergency contact phone number
                  </p>
                </div>
              </div>
            </div>{' '}
            {/* License Information */}
            <div>
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <CreditCard size={20} />
                South African Driver's License Information
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">
                    License Number <span className="text-destructive">*</span>
                  </label>
                  <input
                    type="text"
                    name="license_number"
                    value={formData.license_number}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-input rounded-md bg-background"
                    placeholder="e.g., 1234567890123"
                    required
                  />
                  <p className="text-xs text-muted-foreground mt-1">SA license number format</p>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">License Code/Type</label>
                  <select
                    name="license_type"
                    value={formData.license_type}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-input rounded-md bg-background"
                  >
                    {licenseTypes.map(type => (
                      <option key={type} value={type}>
                        {type}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">
                    License Expiry <span className="text-destructive">*</span>
                  </label>
                  <div className="relative">
                    <Calendar
                      size={16}
                      className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground"
                    />
                    <input
                      type="date"
                      name="license_expiry"
                      value={formData.license_expiry}
                      onChange={handleInputChange}
                      className="w-full pl-10 pr-3 py-2 border border-input rounded-md bg-background"
                      required
                    />
                  </div>
                </div>
              </div>
            </div>
            {/* Employment Information */}
            <div>
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Building size={20} />
                Employment Information
              </h3>{' '}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Department</label>
                  <select
                    name="department"
                    value={formData.department}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-input rounded-md bg-background"
                  >
                    <option value="">Select Department</option>
                    {departments.map(dept => (
                      <option key={dept} value={dept}>
                        {dept}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Joining Date</label>
                  <input
                    type="date"
                    name="joining_date"
                    value={formData.joining_date}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-input rounded-md bg-background"
                  />
                </div>
              </div>
            </div>
            {/* Submit Buttons */}
            <div className="flex justify-end gap-3 pt-4 border-t border-border">
              <button
                type="button"
                onClick={closeModal}
                className="px-4 py-2 border border-border rounded-md hover:bg-accent/10 transition"
                disabled={loading}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition flex items-center gap-2"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"></div>
                    Creating...
                  </>
                ) : (
                  'Add Driver'
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default AddDriverModal;
