import { PermissionsAndroid, Platform } from 'react-native';

/**
 * Request required permissions for the app functionality
 */
export const requestAppPermissions = async () => {
  try {
    if (Platform.OS === 'android') {
      // Request Android permissions
      const permissions = [
        PermissionsAndroid.PERMISSIONS.ACCESS_FINE_LOCATION,
        PermissionsAndroid.PERMISSIONS.ACCESS_COARSE_LOCATION,
      ];

      // Add POST_NOTIFICATIONS permission for Android 13+ (API level 33+)
      if (Platform.Version >= 33) {
        permissions.push(PermissionsAndroid.PERMISSIONS.POST_NOTIFICATIONS);
      }

      const results = await PermissionsAndroid.requestMultiple(permissions);

      const allGranted = Object.values(results).every(
        result => result === PermissionsAndroid.RESULTS.GRANTED
      );

      return {
        allGranted,
        results,
      };
    }

    // iOS permissions are handled through Info.plist
    return { allGranted: true, results: {} };
  } catch (err) {
    console.error('Error requesting permissions:', err);
    return { allGranted: false, error: err };
  }
};

/**
 * Check if all required permissions are granted
 */
export const checkPermissions = async () => {
  if (Platform.OS === 'android') {
    try {
      // For Android API 33+ (Android 13+) we need to check POST_NOTIFICATIONS
      if (Platform.Version >= 33) {
        const notificationPermission = await PermissionsAndroid.check(
          PermissionsAndroid.PERMISSIONS.POST_NOTIFICATIONS
        );

        if (!notificationPermission) {
          return false;
        }
      }

      // Check location permissions
      const fineLocation = await PermissionsAndroid.check(
        PermissionsAndroid.PERMISSIONS.ACCESS_FINE_LOCATION
      );

      return fineLocation;
    } catch (err) {
      console.error('Error checking permissions:', err);
      return false;
    }
  }

  // For iOS we assume permissions are handled through the system dialogs
  return true;
};
