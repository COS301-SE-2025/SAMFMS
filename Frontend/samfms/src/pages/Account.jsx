import React, { useState, useEffect, useRef } from 'react';
import { Button } from '../components/ui/button';
import {
  getCurrentUser,
  getUserInfo,
  updateUserProfile,
  uploadProfilePicture,
  changePassword,
} from '../backend/api/auth';
import {
  validatePassword,
  PasswordStrengthIndicator,
  PasswordRequirements,
} from '../utils/passwordValidation';
import PreferencesSection from '../components/common/PreferencesSection';
import { useNotification } from '../contexts/NotificationContext';

// Modal component for change password
const ChangePasswordModal = ({ isOpen, onClose, onSubmit, loading, error, success }) => {
  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });

  const handlePasswordChange = e => {
    const { name, value } = e.target;
    setPasswordData(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async e => {
    e.preventDefault();

    // Validate current password
    if (!passwordData.currentPassword) {
      return;
    }

    // Validate new password
    if (!passwordData.newPassword) {
      return;
    }

    // Enhanced password validation
    const passwordErrors = validatePassword(passwordData.newPassword);
    if (passwordErrors.length > 0) {
      return;
    }

    // Check if passwords match
    if (passwordData.newPassword !== passwordData.confirmPassword) {
      return;
    }

    // Check if new password is different from current
    if (passwordData.currentPassword === passwordData.newPassword) {
      return;
    }

    await onSubmit(passwordData.currentPassword, passwordData.newPassword);

    // Clear form on success
    if (success) {
      setPasswordData({
        currentPassword: '',
        newPassword: '',
        confirmPassword: '',
      });
    }
  };

  // Reset form when modal closes
  useEffect(() => {
    if (!isOpen) {
      setPasswordData({
        currentPassword: '',
        newPassword: '',
        confirmPassword: '',
      });
    }
  }, [isOpen]);

  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-background dark:bg-background rounded-lg shadow-xl p-6 w-full max-w-md mx-4 border border-border">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-foreground">Change Password</h2>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground text-xl">
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="bg-destructive/10 text-destructive p-3 rounded-md border border-destructive/20">
              {error}
            </div>
          )}
          {success && (
            <div className="bg-green-500/10 text-green-600 dark:text-green-400 p-3 rounded-md border border-green-500/20">
              {success}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium mb-1 text-foreground">
              Current Password
            </label>
            <input
              type="password"
              className="w-full p-2 border border-border rounded-md bg-background text-foreground focus:ring-primary focus:border-primary placeholder:text-muted-foreground"
              name="currentPassword"
              value={passwordData.currentPassword}
              onChange={handlePasswordChange}
              placeholder="Enter current password"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1 text-foreground">New Password</label>
            <input
              type="password"
              className="w-full p-2 border border-border rounded-md bg-background text-foreground focus:ring-primary focus:border-primary placeholder:text-muted-foreground"
              name="newPassword"
              value={passwordData.newPassword}
              onChange={handlePasswordChange}
              placeholder="Enter new password"
              required
            />
            {passwordData.newPassword && (
              <>
                <PasswordStrengthIndicator password={passwordData.newPassword} />
                <PasswordRequirements password={passwordData.newPassword} />
              </>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium mb-1 text-foreground">
              Confirm New Password
            </label>
            <input
              type="password"
              className="w-full p-2 border border-border rounded-md bg-background text-foreground focus:ring-primary focus:border-primary placeholder:text-muted-foreground"
              name="confirmPassword"
              value={passwordData.confirmPassword}
              onChange={handlePasswordChange}
              placeholder="Confirm new password"
              required
            />
            {passwordData.confirmPassword && passwordData.newPassword && (
              <p
                className={`text-xs mt-1 ${
                  passwordData.newPassword === passwordData.confirmPassword
                    ? 'text-green-600 dark:text-green-400'
                    : 'text-destructive'
                }`}
              >
                {passwordData.newPassword === passwordData.confirmPassword
                  ? '✓ Passwords match'
                  : '✗ Passwords do not match'}
              </p>
            )}
          </div>

          <div className="flex justify-end space-x-3 pt-4">
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? 'Updating...' : 'Update Password'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

const Account = () => {
  const { showSuccess, showError } = useNotification();
  const [userData, setUserData] = useState({
    full_name: '',
    email: '',
    role: '',
    phoneNo: '',
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [initials, setInitials] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [profilePicture, setProfilePicture] = useState(null);
  const [editableData, setEditableData] = useState({
    phoneNo: '',
    full_name: '',
  });
  const [originalData, setOriginalData] = useState({
    phoneNo: '',
    full_name: '',
  }); // Password modal states
  const [isPasswordModalOpen, setIsPasswordModalOpen] = useState(false);
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [passwordError, setPasswordError] = useState('');
  const [passwordSuccess, setPasswordSuccess] = useState('');

  const fileInputRef = useRef(null);
  useEffect(() => {
    const fetchUserData = async () => {
      try {
        setLoading(true);

        // First try to get data from cookies
        const cookieUser = getCurrentUser();

        if (cookieUser) {
          const userDataFromCookie = {
            full_name: cookieUser.full_name || '',
            email: cookieUser.email || '',
            role: cookieUser.role || '',
            phoneNo: cookieUser.phoneNo || '',
            ...cookieUser,
          };
          setUserData(userDataFromCookie);
          const editableInfo = {
            phoneNo: userDataFromCookie.phoneNo || '',
            full_name: userDataFromCookie.full_name || '',
          };
          setEditableData(editableInfo);
          setOriginalData(editableInfo);

          // Set profile picture if available
          if (cookieUser.profile_picture_url) {
            setProfilePicture(cookieUser.profile_picture_url);
          }

          // Set initials for avatar
          if (cookieUser.full_name) {
            const names = cookieUser.full_name.split(' ');
            const firstInitial = names[0] ? names[0].charAt(0).toUpperCase() : '';
            const lastInitial =
              names.length > 1 ? names[names.length - 1].charAt(0).toUpperCase() : '';
            setInitials(firstInitial + lastInitial);
          }
        } // Then try to get more complete data from the API
        try {
          const apiUserData = await getUserInfo();
          if (apiUserData) {
            const mergedData = {
              ...apiUserData,
            };
            setUserData(mergedData);
            const editableInfo = {
              phoneNo: mergedData.phoneNo || '',
              full_name: mergedData.full_name || '',
            };
            setEditableData(editableInfo);
            setOriginalData(editableInfo);

            // Update profile picture if available from API
            if (apiUserData.profile_picture_url) {
              setProfilePicture(apiUserData.profile_picture_url);
            }

            // Update initials if we got a full name from the API
            if (apiUserData.full_name) {
              const names = apiUserData.full_name.split(' ');
              const firstInitial = names[0] ? names[0].charAt(0).toUpperCase() : '';
              const lastInitial =
                names.length > 1 ? names[names.length - 1].charAt(0).toUpperCase() : '';
              setInitials(firstInitial + lastInitial);
            }
          }
        } catch (apiError) {
          // Log error but don't display to user since we already have data from cookies
          console.error('Error getting data from API:', apiError);
          // We can continue with cookie data only
        }
      } catch (err) {
        console.error('Error fetching user data:', err);
        setError('Failed to load account details');
      } finally {
        setLoading(false);
      }
    };
    fetchUserData();
  }, []);

  // Helper function to check if personal information has changed
  const hasPersonalInfoChanges = () => {
    return (
      editableData.full_name !== originalData.full_name ||
      editableData.phoneNo !== originalData.phoneNo
    );
  };

  const handleInputChange = e => {
    const { name, value } = e.target;
    setEditableData(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleProfilePictureClick = () => {
    fileInputRef.current.click();
  };

  const handleFileChange = async e => {
    const file = e.target.files[0];
    if (!file) return;

    // Check if file is PNG or JPEG
    const validTypes = ['image/png', 'image/jpeg', 'image/jpg'];
    if (!validTypes.includes(file.type)) {
      setError('Please select a PNG or JPEG image file');
      return;
    }

    try {
      setIsUploading(true);
      setError('');

      // Create a local URL for immediate display
      const localUrl = URL.createObjectURL(file);
      setProfilePicture(localUrl);

      // Upload to server
      const result = await uploadProfilePicture(file); // Update with server URL
      if (result && result.profile_picture_url) {
        setProfilePicture(result.profile_picture_url);
        showSuccess('Profile picture updated successfully');
      }
    } catch (err) {
      console.error('Error uploading profile picture:', err);
      if (err.message.includes('PNG or JPEG')) {
        showError('Please select a PNG or JPEG image file');
      } else if (err.message.includes('Network')) {
        showError('Network error. Please check your connection and try again.');
      } else if (err.message.includes('5MB')) {
        showError('File size must be less than 5MB');
      } else {
        showError(err.message || 'Failed to upload profile picture. Please try again.');
      }
      // Revert to previous picture or initials
      setProfilePicture(userData.profile_picture_url || null);
    } finally {
      setIsUploading(false);
    }
  };
  const handleSubmit = async e => {
    e.preventDefault();

    try {
      setLoading(true);
      setError('');

      // Basic validation
      if (editableData.full_name && editableData.full_name.trim().length < 2) {
        setError('Full name must be at least 2 characters long');
        return;
      }

      if (editableData.phoneNo && !/^\+?[\d\s\-()]+$/.test(editableData.phoneNo)) {
        setError('Please enter a valid phone number');
        return;
      }

      // Only update fields that have changed
      const updates = {};
      if (editableData.phoneNo !== userData.phoneNo) {
        updates.phoneNo = editableData.phoneNo;
      }

      if (editableData.full_name !== userData.full_name) {
        updates.full_name = editableData.full_name;
      }

      if (Object.keys(updates).length === 0) {
        showSuccess('No changes to save');
        setLoading(false);
        return;
      }

      await updateUserProfile(updates); // Update local data
      setUserData(prev => ({
        ...prev,
        ...updates,
      }));

      // Update original data to reflect the saved state
      setOriginalData(prev => ({
        ...prev,
        ...updates,
      }));

      showSuccess('Profile updated successfully');

      // Update initials if name changed
      if (updates.full_name) {
        const names = updates.full_name.split(' ');
        const firstInitial = names[0] ? names[0].charAt(0).toUpperCase() : '';
        const lastInitial = names.length > 1 ? names[names.length - 1].charAt(0).toUpperCase() : '';
        setInitials(firstInitial + lastInitial);
      }
    } catch (err) {
      console.error('Error updating profile:', err);
      if (err.message.includes('Network')) {
        setError('Network error. Please check your connection and try again.');
      } else if (err.message.includes('503')) {
        setError('Service temporarily unavailable. Please try again later.');
      } else {
        setError(err.message || 'Failed to update profile. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  // Handle password change via modal
  const handlePasswordSubmit = async (currentPassword, newPassword) => {
    // Reset states
    setPasswordError('');
    setPasswordSuccess('');

    // Validate current password
    if (!currentPassword) {
      setPasswordError('Current password is required');
      return;
    }

    // Validate new password
    if (!newPassword) {
      setPasswordError('New password is required');
      return;
    }

    // Enhanced password validation
    const passwordErrors = validatePassword(newPassword);
    if (passwordErrors.length > 0) {
      setPasswordError(passwordErrors[0]); // Show first error
      return;
    }

    // Check if new password is different from current
    if (currentPassword === newPassword) {
      setPasswordError('New password must be different from current password');
      return;
    }

    try {
      setPasswordLoading(true);

      await changePassword(currentPassword, newPassword);

      setPasswordSuccess('Password updated successfully');

      // Close modal after a short delay to show success message
      setTimeout(() => {
        setIsPasswordModalOpen(false);
        setPasswordSuccess('');
      }, 2000);
    } catch (err) {
      console.error('Error updating password:', err);
      if (err.message.includes('Network')) {
        setPasswordError('Network error. Please check your connection and try again.');
      } else if (err.message.includes('503')) {
        setPasswordError('Service temporarily unavailable. Please try again later.');
      } else if (err.message.includes('Current password is incorrect')) {
        setPasswordError('Current password is incorrect. Please try again.');
      } else {
        setPasswordError(err.message || 'Failed to update password. Please try again.');
      }
    } finally {
      setPasswordLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background relative">
      {/* SVG pattern background like Landing page */}
      <div
        className="absolute inset-0 z-0 opacity-10 pointer-events-none"
        style={{
          backgroundImage: 'url("/logo/logo_icon_dark.svg")',
          backgroundSize: '200px',
          backgroundRepeat: 'repeat',
          filter: 'blur(1px)',
        }}
      />
      <div className="relative z-10 container mx-auto py-8">
        <header className="mb-8">
          <h1 className="text-4xl font-bold">Account</h1>
        </header>
        {loading && !isUploading ? (
          <div className="flex justify-center items-center min-h-[300px]">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
          </div>
        ) : error ? (
          <div className="bg-red-50 text-red-800 p-4 rounded-lg mb-6">{error}</div>
        ) : (
          <div className="max-w-7xl mx-auto">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {' '}
              {/* Left Column - Profile Section */}
              <div className="bg-card p-8 rounded-lg shadow-md border border-border h-fit">
                {/* Profile Picture Section - Now at the top */}
                <div className="flex flex-col items-center mb-8 pb-6 border-b border-border">
                  {/* Hidden file input for profile picture upload */}
                  <input
                    type="file"
                    ref={fileInputRef}
                    className="hidden"
                    accept="image/png,image/jpeg,image/jpg"
                    onChange={handleFileChange}
                  />

                  {/* Profile picture or initials */}
                  <div
                    onClick={handleProfilePictureClick}
                    className="w-32 h-32 rounded-full bg-primary/20 flex items-center justify-center mb-4 cursor-pointer relative overflow-hidden"
                    title="Click to change profile picture"
                  >
                    {isUploading && (
                      <div className="absolute inset-0 bg-black/30 flex items-center justify-center">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
                      </div>
                    )}

                    {profilePicture ? (
                      <img
                        src={profilePicture}
                        alt="Profile"
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <span className="text-4xl text-foreground">{initials || 'U'}</span>
                    )}
                  </div>
                  <h2 className="text-xl font-semibold text-foreground">
                    {userData.full_name || 'User'}
                  </h2>
                  <p className="text-muted-foreground">
                    {userData.role
                      ? userData.role.charAt(0).toUpperCase() + userData.role.slice(1)
                      : 'User'}
                  </p>
                </div>
                {/* Form Section - Now takes full width */}
                <form className="space-y-6" onSubmit={handleSubmit}>
                  {/* Personal Information Section */}
                  <div>
                    <h3 className="text-lg font-semibold mb-4 text-primary border-b border-border pb-2">
                      Personal Information
                    </h3>
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium mb-1 text-foreground">
                          Full Name
                        </label>
                        <input
                          type="text"
                          value={editableData.full_name || ''}
                          onChange={e =>
                            setEditableData({ ...editableData, full_name: e.target.value })
                          }
                          className="w-full p-2 border border-border rounded-md bg-background text-foreground focus:ring-primary focus:border-primary placeholder:text-muted-foreground"
                          placeholder="Enter your full name"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium mb-1 text-foreground">
                          Email
                        </label>
                        <input
                          type="email"
                          value={userData.email || ''}
                          readOnly
                          className="w-full p-2 border border-border rounded-md bg-muted text-muted-foreground cursor-not-allowed"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium mb-1 text-foreground">
                          Phone
                        </label>{' '}
                        <input
                          type="tel"
                          name="phoneNo"
                          value={editableData.phoneNo || ''}
                          onChange={handleInputChange}
                          className="w-full p-2 border border-border rounded-md bg-background text-foreground focus:ring-primary focus:border-primary placeholder:text-muted-foreground"
                          placeholder="Enter your phone number"
                        />
                      </div>
                    </div>

                    {/* Save Button for Personal Information - Only show if there are changes */}
                    {hasPersonalInfoChanges() && (
                      <div className="flex justify-end pt-4 border-t border-border mt-4">
                        <Button type="submit" disabled={loading}>
                          {loading ? 'Saving...' : 'Save Changes'}
                        </Button>
                      </div>
                    )}
                  </div>

                  {/* Security Section */}
                  <div>
                    <h3 className="text-lg font-semibold mb-4 text-primary border-b border-border pb-2">
                      Security
                    </h3>
                    <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg border border-border">
                      <div>
                        <p className="font-medium text-foreground">Password</p>
                        <p className="text-sm text-muted-foreground">
                          Last updated: {new Date().toLocaleDateString()}
                        </p>
                      </div>
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => setIsPasswordModalOpen(true)}
                      >
                        Change Password
                      </Button>{' '}
                    </div>
                  </div>
                </form>
              </div>
              {/* Right Column - Preferences Section */}
              <div>
                <PreferencesSection />
              </div>
            </div>
          </div>
        )}
        {/* Change Password Modal */}
        <ChangePasswordModal
          isOpen={isPasswordModalOpen}
          onClose={() => {
            setIsPasswordModalOpen(false);
            setPasswordError('');
            setPasswordSuccess('');
          }}
          onSubmit={handlePasswordSubmit}
          loading={passwordLoading}
          error={passwordError}
          success={passwordSuccess}
        />
      </div>
    </div>
  );
};

export default Account;
