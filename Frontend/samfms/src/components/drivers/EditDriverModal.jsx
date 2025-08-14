import React, { useState, useEffect } from 'react';
import { X, User, Phone, Mail, Calendar, Building, CreditCard } from 'lucide-react';
import { updateDriver } from '../../backend/API';

const EditDriverModal = ({ driver, closeModal, onDriverUpdated }) => {
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
    employee_id: '',
    status: 'available',
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Validation errors state
  const [validationErrors, setValidationErrors] = useState({});

  // Initialize form data when driver prop changes
  useEffect(() => {
    if (driver) {
      setFormData({
        full_name: driver.name || '',
        email: driver.email || '',
        phoneNo: driver.phone || '',
        license_number: driver.licenseNumber || '',
        license_type: driver.licenseType || 'Code B (Light Motor Vehicle)',
        license_expiry: driver.licenseExpiry || '',
        department: driver.department || '',
        joining_date: driver.joiningDate || '',
        emergency_contact: driver.emergencyContact || '',
        employee_id: driver.employeeId || '',
        status: driver.status?.toLowerCase().replace(/\s+/g, '_') || 'available',
      });
    }
  }, [driver]);

  const handleInputChange = e => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));

    // Clear validation error for this field when user starts typing
    if (validationErrors[name]) {
      setValidationErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };
  const handleSubmit = async e => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setValidationErrors({});

    try {
      // Validate required fields
      const errors = {};

      if (!formData.full_name.trim()) {
        errors.full_name = 'Full name is required';
      }

      if (!formData.license_number.trim()) {
        errors.license_number = 'License number is required';
      }

      if (!formData.license_expiry) {
        errors.license_expiry = 'License expiry date is required';
      }

      if (!formData.email.trim()) {
        errors.email = 'Email is required';
      } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
        errors.email = 'Please enter a valid email address';
      }

      // Validate phone number if provided
      if (formData.phoneNo.trim()) {
        const phoneRegex = /^(\+27|0)[1-9][0-9]{8}$/;
        if (!phoneRegex.test(formData.phoneNo.replace(/\s+/g, ''))) {
          errors.phoneNo = 'Please enter a valid South African phone number';
        }
      }

      // Validate emergency contact if provided
      if (formData.emergency_contact.trim()) {
        const emergencyPhoneRegex = /^(\+27|0)[1-9][0-9]{8}$/;
        if (!emergencyPhoneRegex.test(formData.emergency_contact.replace(/\s+/g, ''))) {
          errors.emergency_contact = 'Please enter a valid South African emergency contact number';
        }
      }

      // If there are validation errors, display them and stop
      if (Object.keys(errors).length > 0) {
        setValidationErrors(errors);
        throw new Error('Please fix the validation errors below');
      }

      // Use employee ID instead of MongoDB id for operations
      const driverId = driver.employeeId || driver.id;

      // Update driver using the employee ID
      const updatedDriver = await updateDriver(driverId, formData);

      // Call the callback to refresh the drivers list
      if (onDriverUpdated) {
        onDriverUpdated(updatedDriver);
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

  const statusOptions = [
    { value: 'available', label: 'Available' },
    { value: 'on_trip', label: 'On Trip' },
    { value: 'on_leave', label: 'On Leave' },
    { value: 'inactive', label: 'Inactive' },
  ];

  if (!driver) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-card w-full max-w-5xl rounded-lg shadow-xl overflow-hidden max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold">Edit Driver</h2>
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
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Full Name <span className="text-destructive">*</span>
                  </label>
                  <input
                    type="text"
                    name="full_name"
                    value={formData.full_name}
                    onChange={handleInputChange}
                    className={`w-full px-3 py-2 border rounded-md bg-background ${
                      validationErrors.full_name ? 'border-destructive' : 'border-input'
                    }`}
                    placeholder="Enter full name"
                    required
                  />
                  {validationErrors.full_name && (
                    <p className="text-destructive text-xs mt-1">{validationErrors.full_name}</p>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Employee ID</label>
                  <input
                    type="text"
                    name="employee_id"
                    value={formData.employee_id}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-input rounded-md bg-background"
                    placeholder="Enter employee ID"
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
                      className={`w-full pl-10 pr-3 py-2 border rounded-md bg-background ${
                        validationErrors.email ? 'border-destructive' : 'border-input'
                      }`}
                      placeholder="Enter email address"
                      required
                    />
                  </div>
                  {validationErrors.email && (
                    <p className="text-destructive text-xs mt-1">{validationErrors.email}</p>
                  )}
                </div>
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
                      className={`w-full pl-10 pr-3 py-2 border rounded-md bg-background ${
                        validationErrors.phoneNo ? 'border-destructive' : 'border-input'
                      }`}
                      placeholder="+27123456789 or 0123456789"
                    />
                  </div>
                  {validationErrors.phoneNo && (
                    <p className="text-destructive text-xs mt-1">{validationErrors.phoneNo}</p>
                  )}
                </div>
              </div>

              {/* Second row of personal info */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Emergency Contact (Optional)
                  </label>
                  <input
                    type="tel"
                    name="emergency_contact"
                    value={formData.emergency_contact}
                    onChange={handleInputChange}
                    className={`w-full px-3 py-2 border rounded-md bg-background ${
                      validationErrors.emergency_contact ? 'border-destructive' : 'border-input'
                    }`}
                    placeholder="+27123456789 or 0123456789"
                  />
                  {validationErrors.emergency_contact && (
                    <p className="text-destructive text-xs mt-1">
                      {validationErrors.emergency_contact}
                    </p>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Status</label>
                  <select
                    name="status"
                    value={formData.status}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-input rounded-md bg-background"
                  >
                    {statusOptions.map(option => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>
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
              </div>
            </div>

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
                    className={`w-full px-3 py-2 border rounded-md bg-background ${
                      validationErrors.license_number ? 'border-destructive' : 'border-input'
                    }`}
                    placeholder="e.g., 1234567890123"
                    required
                  />
                  {validationErrors.license_number && (
                    <p className="text-destructive text-xs mt-1">
                      {validationErrors.license_number}
                    </p>
                  )}
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
                      className={`w-full pl-10 pr-3 py-2 border rounded-md bg-background ${
                        validationErrors.license_expiry ? 'border-destructive' : 'border-input'
                      }`}
                      required
                    />
                  </div>
                  {validationErrors.license_expiry && (
                    <p className="text-destructive text-xs mt-1">
                      {validationErrors.license_expiry}
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* Employment Information */}
            <div>
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Building size={20} />
                Employment Information
              </h3>
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
                    Updating...
                  </>
                ) : (
                  'Update Driver'
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default EditDriverModal;
