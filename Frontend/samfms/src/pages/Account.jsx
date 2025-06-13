import React, { useState, useEffect, useRef } from 'react';
import { Button } from '../components/ui/button';
import {
  getCurrentUser,
  getUserInfo,
  updateUserProfile,
  uploadProfilePicture,
  changePassword,
} from '../backend/api/auth';

const Account = () => {
  const [userData, setUserData] = useState({
    full_name: '',
    email: '',
    role: '',
    phoneNo: '',
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [initials, setInitials] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [profilePicture, setProfilePicture] = useState(null);
  const [editableData, setEditableData] = useState({
    phoneNo: '',
    full_name: '',
  });

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
          setEditableData({
            phoneNo: userDataFromCookie.phoneNo || '',
            full_name: userDataFromCookie.full_name || '',
          });

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
            setEditableData({
              phoneNo: mergedData.phoneNo || '',
              full_name: mergedData.full_name || '',
            });

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
      const result = await uploadProfilePicture(file);

      // Update with server URL
      if (result && result.profile_picture_url) {
        setProfilePicture(result.profile_picture_url);
        setSuccess('Profile picture updated successfully');
      }
    } catch (err) {
      console.error('Error uploading profile picture:', err);
      setError('Failed to upload profile picture');
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
      setSuccess('');

      // Only update fields that have changed
      const updates = {};
      if (editableData.phoneNo !== userData.phoneNo) {
        updates.phoneNo = editableData.phoneNo;
      }

      if (editableData.full_name !== userData.full_name) {
        updates.full_name = editableData.full_name;
      }

      if (Object.keys(updates).length === 0) {
        setSuccess('No changes to save');
        setLoading(false);
        return;
      }

      await updateUserProfile(updates);

      // Update local data
      setUserData(prev => ({
        ...prev,
        ...updates,
      }));

      setSuccess('Profile updated successfully');
    } catch (err) {
      console.error('Error updating profile:', err);
      setError('Failed to update profile');
    } finally {
      setLoading(false);
    }
  };
  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [passwordError, setPasswordError] = useState('');
  const [passwordSuccess, setPasswordSuccess] = useState('');

  const handlePasswordChange = e => {
    const { name, value } = e.target;
    setPasswordData(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const handlePasswordSubmit = async e => {
    e.preventDefault();

    // Reset states
    setPasswordError('');
    setPasswordSuccess('');

    // Validate passwords
    if (!passwordData.currentPassword) {
      setPasswordError('Current password is required');
      return;
    }

    if (!passwordData.newPassword) {
      setPasswordError('New password is required');
      return;
    }

    if (passwordData.newPassword !== passwordData.confirmPassword) {
      setPasswordError('New passwords do not match');
      return;
    }

    // Check password strength
    if (passwordData.newPassword.length < 8) {
      setPasswordError('Password must be at least 8 characters long');
      return;
    }

    try {
      setPasswordLoading(true);

      await changePassword(passwordData.currentPassword, passwordData.newPassword);

      // Clear form
      setPasswordData({
        currentPassword: '',
        newPassword: '',
        confirmPassword: '',
      });

      setPasswordSuccess('Password updated successfully');
    } catch (err) {
      console.error('Error updating password:', err);
      setPasswordError(err.message || 'Failed to update password');
    } finally {
      setPasswordLoading(false);
    }
  };

  return (
    <div className="container mx-auto py-8">
      <header className="mb-8">
        <h1 className="text-4xl font-bold">Account</h1>
        <p className="text-muted-foreground">Manage your account details</p>
      </header>

      {loading && !isUploading ? (
        <div className="flex justify-center items-center min-h-[300px]">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      ) : error ? (
        <div className="bg-red-50 text-red-800 p-4 rounded-lg mb-6">{error}</div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-1">
            <div className="bg-card p-6 rounded-lg shadow-md border border-border">
              <div className="flex flex-col items-center mb-6">
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
                    <span className="text-4xl">{initials || 'U'}</span>
                  )}
                </div>
                <h2 className="text-xl font-semibold">{userData.full_name || 'User'}</h2>
                <p className="text-muted-foreground">
                  {userData.role
                    ? userData.role.charAt(0).toUpperCase() + userData.role.slice(1)
                    : 'User'}
                </p>
                <p className="text-xs text-muted-foreground mt-2">
                  Click on the profile picture to upload a new one (PNG or JPEG)
                </p>
              </div>
            </div>
          </div>

          <div className="lg:col-span-2">
            {success && (
              <div className="bg-green-50 text-green-700 p-4 rounded-lg mb-6">{success}</div>
            )}

            <div className="bg-card p-6 rounded-lg shadow-md border border-border mb-6">
              <h2 className="text-xl font-semibold mb-4">Personal Information</h2>
              <form className="space-y-4" onSubmit={handleSubmit}>
                {' '}
                <div>
                  <label className="block text-sm font-medium mb-1">Full Name</label>
                  <input
                    type="text"
                    value={editableData.full_name || ''}
                    onChange={e => setEditableData({ ...editableData, full_name: e.target.value })}
                    className="w-full p-2 border rounded-md focus:ring-primary-700 focus:border-primary-700"
                  />
                  <p className="text-xs text-muted-foreground mt-1">
                    Your name as it appears in the system
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Email</label>
                  <input
                    type="email"
                    value={userData.email || ''}
                    readOnly
                    className="w-full p-2 border rounded-md bg-gray-50"
                  />
                  <p className="text-xs text-muted-foreground mt-1">
                    Email address is used for login and cannot be changed
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Role</label>
                  <input
                    type="text"
                    value={
                      userData.role
                        ? userData.role.charAt(0).toUpperCase() + userData.role.slice(1)
                        : 'User'
                    }
                    readOnly
                    className="w-full p-2 border rounded-md bg-gray-50"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Phone</label>
                  <input
                    type="tel"
                    name="phoneNo"
                    value={editableData.phoneNo || ''}
                    onChange={handleInputChange}
                    className="w-full p-2 border rounded-md"
                  />
                </div>
                <div className="flex justify-end">
                  <Button type="submit" disabled={loading}>
                    {loading ? 'Saving...' : 'Save Changes'}
                  </Button>
                </div>
              </form>
            </div>

            <div className="bg-card p-6 rounded-lg shadow-md border border-border">
              <h2 className="text-xl font-semibold mb-4">Security</h2>{' '}
              <form className="space-y-4" onSubmit={handlePasswordSubmit}>
                {passwordError && (
                  <div className="bg-red-50 text-red-700 p-3 rounded-md">{passwordError}</div>
                )}
                {passwordSuccess && (
                  <div className="bg-green-50 text-green-700 p-3 rounded-md">{passwordSuccess}</div>
                )}
                <div>
                  <label className="block text-sm font-medium mb-1">Current Password</label>
                  <input
                    type="password"
                    className="w-full p-2 border rounded-md"
                    name="currentPassword"
                    value={passwordData.currentPassword}
                    onChange={handlePasswordChange}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">New Password</label>
                  <input
                    type="password"
                    className="w-full p-2 border rounded-md"
                    name="newPassword"
                    value={passwordData.newPassword}
                    onChange={handlePasswordChange}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Confirm New Password</label>
                  <input
                    type="password"
                    className="w-full p-2 border rounded-md"
                    name="confirmPassword"
                    value={passwordData.confirmPassword}
                    onChange={handlePasswordChange}
                  />
                </div>
                <div className="flex justify-end">
                  <Button type="submit" disabled={passwordLoading}>
                    {passwordLoading ? 'Updating...' : 'Update Password'}
                  </Button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Account;
