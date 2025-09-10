import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  useColorScheme,
  StyleSheet,
  TextInput,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { User, Phone, Mail, Award, Edit3, Save, X, LogOut } from 'lucide-react-native';
import { getUserData, setUserData as saveUserData, API_URL, getToken, logout } from '../utils/api';
import { useAuth } from '../contexts/AuthContext';

export default function AccountScreen() {
  const isDarkMode = useColorScheme() === 'dark';
  const { logout: authLogout } = useAuth();

  const [userData, setUserData] = useState({
    full_name: '',
    email: '',
    role: '',
    phoneNo: '',
    employeeId: '',
  });
  const [editableData, setEditableData] = useState({
    full_name: '',
    phoneNo: '',
  });
  const [originalData, setOriginalData] = useState({
    full_name: '',
    phoneNo: '',
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [isEditing, setIsEditing] = useState(false);

  const theme = {
    background: isDarkMode ? '#0f172a' : '#f8fafc',
    cardBackground: isDarkMode ? '#1e293b' : '#ffffff',
    text: isDarkMode ? '#f1f5f9' : '#1e293b',
    textSecondary: isDarkMode ? '#94a3b8' : '#64748b',
    accent: '#3b82f6',
    border: isDarkMode ? '#334155' : '#e2e8f0',
    success: '#10b981',
    error: '#ef4444',
  };

  useEffect(() => {
    fetchUserData();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const getEmployeeID = async (security_id: string) => {
    try {
      const token = await getToken();
      if (!token) return null;

      const response = await fetch(`${API_URL}/management/drivers/employee/${security_id}`, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        // Based on the provided response structure: {"status":"success","data":{"status":"success","data":"EMP139",...}}
        return data?.data?.data || data?.data || null;
      }
    } catch (err) {
      console.error('Error fetching employee ID:', err);
    }
    return null;
  };

  const fetchUserData = async () => {
    try {
      setLoading(true);
      setError('');

      // First get data from local storage
      const localUserData = await getUserData();
      console.log('=== USER DATA FETCH DEBUG ===');
      console.log('Local user data:', localUserData);
      console.log('Local user data type:', typeof localUserData);
      console.log('Local user data keys:', localUserData ? Object.keys(localUserData) : 'null');
      if (localUserData) {
        // Handle various possible field names in local storage
        const user = {
          full_name: localUserData.full_name || localUserData.name || localUserData.fullName || '',
          email: localUserData.email || '',
          role: localUserData.role || '',
          phoneNo: localUserData.phoneNo || localUserData.phone || localUserData.phone_number || '',
          employeeId: localUserData.employeeId || '',
          // Preserve additional fields
          id: localUserData.id || localUserData.user_id,
          user_id: localUserData.user_id || localUserData.id,
        };
        console.log('Processed user data:', user);
        setUserData(user);
        setEditableData({
          full_name: user.full_name,
          phoneNo: user.phoneNo,
        });
        setOriginalData({
          full_name: user.full_name,
          phoneNo: user.phoneNo,
        });

        // Fetch employee ID if we don't have it cached
        if ((user.id || user.user_id) && !user.employeeId) {
          const employeeId = await getEmployeeID(user.id || user.user_id);
          if (employeeId) {
            const updatedUser = { ...user, employeeId };
            setUserData(updatedUser);
            await saveUserData(updatedUser);
          }
        }
      } else {
        console.log('No local user data found - setting defaults');
        // Set default empty values if no local data
        const defaultUser = {
          full_name: '',
          email: '',
          role: '',
          phoneNo: '',
          employeeId: '',
        };
        setUserData(defaultUser);
        setEditableData({
          full_name: '',
          phoneNo: '',
        });
        setOriginalData({
          full_name: '',
          phoneNo: '',
        });
      }

      // Then try to get updated data from API
      const token = await getToken();
      console.log('Token available:', !!token);

      if (token) {
        try {
          // Use the correct endpoint that matches the main app
          const response = await fetch(`${API_URL}/auth/me`, {
            method: 'GET',
            headers: {
              Authorization: `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
          });

          console.log('API response status:', response.status);

          if (response.ok) {
            const apiUserData = await response.json();
            console.log('API user data:', apiUserData);

            // Handle the response data structure properly
            const mergedData = {
              full_name:
                apiUserData.full_name ||
                apiUserData.name ||
                localUserData?.full_name ||
                localUserData?.name ||
                '',
              email: apiUserData.email || localUserData?.email || '',
              role: apiUserData.role || localUserData?.role || '',
              phoneNo:
                apiUserData.phoneNo ||
                apiUserData.phone_number ||
                apiUserData.phone ||
                localUserData?.phoneNo ||
                localUserData?.phone ||
                '',
              employeeId: localUserData?.employeeId || '',
              // Preserve additional fields that might be needed
              id:
                apiUserData.id ||
                apiUserData.user_id ||
                localUserData?.id ||
                localUserData?.user_id,
              user_id:
                apiUserData.user_id ||
                apiUserData.id ||
                localUserData?.user_id ||
                localUserData?.id,
              profile_picture_url:
                apiUserData.profile_picture_url || localUserData?.profile_picture_url,
            };

            console.log('Merged data:', mergedData);
            setUserData(mergedData);
            setEditableData({
              full_name: mergedData.full_name,
              phoneNo: mergedData.phoneNo,
            });
            setOriginalData({
              full_name: mergedData.full_name,
              phoneNo: mergedData.phoneNo,
            });

            // Update local storage with fresh data
            await saveUserData(mergedData);

            // Fetch employee ID if we have a user ID and don't have employee ID cached
            if ((mergedData.id || mergedData.user_id) && !mergedData.employeeId) {
              const employeeId = await getEmployeeID(mergedData.id || mergedData.user_id);
              if (employeeId) {
                const updatedData = { ...mergedData, employeeId };
                setUserData(updatedData);
                await saveUserData(updatedData);
              }
            }
          } else {
            const errorText = await response.text();
            console.log('API request failed:', response.status, errorText);
            // If API fails, we'll continue with local data
          }
        } catch (apiError) {
          console.log('API request error:', apiError);
          // If API fails, we'll continue with local data
        }
      }
    } catch (err) {
      console.error('Error fetching user data:', err);
      setError('Failed to load account details');
    } finally {
      setLoading(false);
    }
  };

  const hasChanges = () => {
    return (
      editableData.full_name !== originalData.full_name ||
      editableData.phoneNo !== originalData.phoneNo
    );
  };

  const handleSave = async () => {
    if (!hasChanges()) {
      setIsEditing(false);
      return;
    }

    try {
      setSaving(true);
      setError('');

      // Basic validation
      if (editableData.full_name.trim().length < 2) {
        setError('Full name must be at least 2 characters long');
        return;
      }

      if (editableData.phoneNo && !/^\+?[\d\s\-()]+$/.test(editableData.phoneNo)) {
        setError('Please enter a valid phone number');
        return;
      }

      const token = await getToken();
      if (!token) {
        setError('Authentication required');
        return;
      }

      const updates: any = {};
      if (editableData.full_name !== originalData.full_name) {
        updates.full_name = editableData.full_name;
      }
      if (editableData.phoneNo !== originalData.phoneNo) {
        updates.phoneNo = editableData.phoneNo;
      }

      const response = await fetch(`${API_URL}/auth/update-profile`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updates),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update profile');
      }

      // Update local state
      const updatedUserData = { ...userData, ...updates };
      setUserData(updatedUserData);
      setOriginalData({
        full_name: updatedUserData.full_name,
        phoneNo: updatedUserData.phoneNo,
      });

      // Update local storage
      await saveUserData(updatedUserData);

      Alert.alert('Success', 'Profile updated successfully');
      setIsEditing(false);
    } catch (err) {
      console.error('Error updating profile:', err);
      if ((err as Error).message.includes('Network')) {
        setError('Network error. Please check your connection and try again.');
      } else if ((err as Error).message.includes('503')) {
        setError('Service temporarily unavailable. Please try again later.');
      } else {
        setError((err as Error).message || 'Failed to update profile. Please try again.');
      }
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    setEditableData({
      full_name: originalData.full_name,
      phoneNo: originalData.phoneNo,
    });
    setIsEditing(false);
    setError('');
  };

  const handleLogout = () => {
    Alert.alert('Logout', 'Are you sure you want to logout?', [
      {
        text: 'Cancel',
        style: 'cancel',
      },
      {
        text: 'Logout',
        style: 'destructive',
        onPress: async () => {
          try {
            await logout();
            // Navigate back to landing page
            authLogout();
          } catch (logoutError) {
            Alert.alert('Error', 'Failed to logout. Please try again.');
          }
        },
      },
    ]);
  };

  const getInitials = (name: string) => {
    if (!name) return 'U';
    const names = name.split(' ');
    const firstInitial = names[0]?.charAt(0).toUpperCase() || '';
    const lastInitial = names.length > 1 ? names[names.length - 1]?.charAt(0).toUpperCase() : '';
    return firstInitial + lastInitial;
  };

  if (loading) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={theme.accent} />
          <Text style={[styles.loadingText, { color: theme.textSecondary }]}>
            Loading account details...
          </Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
      <ScrollView showsVerticalScrollIndicator={false}>
        {/* Profile Header */}
        <View style={[styles.profileHeader, { backgroundColor: theme.cardBackground }]}>
          <View style={styles.profileImageContainer}>
            <View style={[styles.profileImage, { backgroundColor: theme.accent }]}>
              <Text style={styles.profileInitials}>{getInitials(userData.full_name)}</Text>
            </View>
          </View>
          <View style={styles.profileHeaderInfo}>
            <Text style={[styles.driverName, { color: theme.text }]}>
              {userData.full_name || 'User'}
            </Text>
            <Text style={[styles.driverTitle, { color: theme.textSecondary }]}>
              {userData.role
                ? userData.role.charAt(0).toUpperCase() + userData.role.slice(1)
                : 'User'}
            </Text>
            <View style={styles.statusBadge}>
              <View style={styles.statusDot} />
              <Text style={[styles.statusText, { color: theme.textSecondary }]}>Active</Text>
            </View>
          </View>
        </View>

        {/* Error Display */}
        {error ? (
          <View
            style={[
              styles.errorContainer,
              { backgroundColor: theme.error + '20', borderColor: theme.error },
            ]}
          >
            <Text style={[styles.errorText, { color: theme.error }]}>{error}</Text>
          </View>
        ) : null}

        {/* Profile Information */}
        <View style={styles.profileSection}>
          <View style={styles.sectionHeader}>
            <Text style={[styles.sectionTitle, { color: theme.text }]}>Profile Information</Text>
            {!isEditing ? (
              <TouchableOpacity
                style={[styles.editButton, { backgroundColor: theme.accent + '20' }]}
                onPress={() => setIsEditing(true)}
              >
                <Edit3 size={16} color={theme.accent} />
                <Text style={[styles.editButtonText, { color: theme.accent }]}>Edit</Text>
              </TouchableOpacity>
            ) : (
              <View style={styles.editActions}>
                <TouchableOpacity
                  style={[styles.saveButton, { backgroundColor: theme.success }]}
                  onPress={handleSave}
                  disabled={saving}
                >
                  {saving ? (
                    <ActivityIndicator size="small" color="#ffffff" />
                  ) : (
                    <>
                      <Save size={16} color="#ffffff" />
                      <Text style={styles.saveButtonText}>Save</Text>
                    </>
                  )}
                </TouchableOpacity>
                <TouchableOpacity
                  style={[styles.cancelButton, { backgroundColor: theme.textSecondary + '20' }]}
                  onPress={handleCancel}
                  disabled={saving}
                >
                  <X size={16} color={theme.textSecondary} />
                </TouchableOpacity>
              </View>
            )}
          </View>

          <View style={[styles.profileCard, { backgroundColor: theme.cardBackground }]}>
            {/* Full Name */}
            <View style={[styles.profileItem, { borderBottomColor: theme.border }]}>
              <View style={styles.profileItemLeft}>
                <User size={20} color={theme.textSecondary} />
                <Text style={[styles.profileLabel, { color: theme.textSecondary }]}>Full Name</Text>
              </View>
              {isEditing ? (
                <TextInput
                  style={[styles.profileInput, { color: theme.text, borderColor: theme.border }]}
                  value={editableData.full_name}
                  onChangeText={(text: string) =>
                    setEditableData({ ...editableData, full_name: text })
                  }
                  placeholder="Enter your full name"
                  placeholderTextColor={theme.textSecondary}
                />
              ) : (
                <Text style={[styles.profileValue, { color: theme.text }]}>
                  {userData.full_name || 'Not provided'}
                </Text>
              )}
            </View>

            {/* Email */}
            <View style={[styles.profileItem, { borderBottomColor: theme.border }]}>
              <View style={styles.profileItemLeft}>
                <Mail size={20} color={theme.textSecondary} />
                <Text style={[styles.profileLabel, { color: theme.textSecondary }]}>Email</Text>
              </View>
              <Text style={[styles.profileValue, { color: theme.text }]}>
                {userData.email || 'Not provided'}
              </Text>
            </View>

            {/* Phone */}
            <View style={[styles.profileItem, { borderBottomColor: theme.border }]}>
              <View style={styles.profileItemLeft}>
                <Phone size={20} color={theme.textSecondary} />
                <Text style={[styles.profileLabel, { color: theme.textSecondary }]}>Phone</Text>
              </View>
              {isEditing ? (
                <TextInput
                  style={[styles.profileInput, { color: theme.text, borderColor: theme.border }]}
                  value={editableData.phoneNo}
                  onChangeText={(text: string) =>
                    setEditableData({ ...editableData, phoneNo: text })
                  }
                  placeholder="Enter your phone number"
                  placeholderTextColor={theme.textSecondary}
                  keyboardType="phone-pad"
                />
              ) : (
                <Text style={[styles.profileValue, { color: theme.text }]}>
                  {userData.phoneNo || 'Not provided'}
                </Text>
              )}
            </View>

            {/* Role */}
            <View style={styles.profileItem}>
              <View style={styles.profileItemLeft}>
                <Award size={20} color={theme.textSecondary} />
                <Text style={[styles.profileLabel, { color: theme.textSecondary }]}>Role</Text>
              </View>
              <Text style={[styles.profileValue, { color: theme.text }]}>
                {userData.role
                  ? userData.role.charAt(0).toUpperCase() + userData.role.slice(1)
                  : 'User'}
              </Text>
            </View>

            {/* Employee ID */}
            <View style={styles.profileItem}>
              <View style={styles.profileItemLeft}>
                <User size={20} color={theme.textSecondary} />
                <Text style={[styles.profileLabel, { color: theme.textSecondary }]}>
                  Employee ID
                </Text>
              </View>
              <Text style={[styles.profileValue, { color: theme.text }]}>
                {userData.employeeId || 'Loading...'}
              </Text>
            </View>
          </View>
        </View>

        {/* Account Actions */}
        <View style={styles.actionsSection}>
          {/* Logout Button */}
          <TouchableOpacity
            style={[
              styles.logoutButton,
              { backgroundColor: theme.error, borderColor: theme.error },
            ]}
            onPress={handleLogout}
          >
            <LogOut size={20} color="#ffffff" />
            <Text style={[styles.logoutButtonText]}>Logout</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
  },
  profileHeader: {
    padding: 20,
    alignItems: 'center',
  },
  profileImageContainer: {
    marginBottom: 16,
  },
  profileImage: {
    width: 80,
    height: 80,
    borderRadius: 40,
    justifyContent: 'center',
    alignItems: 'center',
  },
  profileInitials: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  profileHeaderInfo: {
    alignItems: 'center',
  },
  driverName: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  driverTitle: {
    fontSize: 16,
    marginBottom: 8,
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#10b981',
    marginRight: 6,
  },
  statusText: {
    fontSize: 14,
  },
  errorContainer: {
    margin: 16,
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
  },
  errorText: {
    fontSize: 14,
    textAlign: 'center',
  },
  profileSection: {
    padding: 16,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  editButton: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 8,
    borderRadius: 8,
  },
  editButtonText: {
    fontSize: 14,
    fontWeight: '500',
    marginLeft: 4,
  },
  editActions: {
    flexDirection: 'row',
    gap: 8,
  },
  saveButton: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 8,
    borderRadius: 8,
    minWidth: 60,
    justifyContent: 'center',
  },
  saveButtonText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#ffffff',
    marginLeft: 4,
  },
  cancelButton: {
    padding: 8,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  profileCard: {
    borderRadius: 12,
    overflow: 'hidden',
  },
  profileItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    minHeight: 60,
  },
  profileItemLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  profileLabel: {
    fontSize: 14,
    marginLeft: 12,
    flex: 1,
  },
  profileValue: {
    fontSize: 14,
    fontWeight: '500',
    flex: 1,
    textAlign: 'right',
  },
  profileInput: {
    fontSize: 14,
    fontWeight: '500',
    flex: 1,
    textAlign: 'right',
    borderBottomWidth: 1,
    paddingBottom: 4,
    marginLeft: 8,
  },
  actionsSection: {
    padding: 16,
    paddingBottom: 32,
  },
  actionButton: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    marginBottom: 12,
  },
  actionButtonText: {
    fontSize: 16,
    fontWeight: '500',
  },
  logoutButton: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    marginBottom: 12,
    marginTop: 8,
  },
  logoutButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ffffff',
    marginLeft: 8,
  },
});
